import logging
import difflib
from typing import List, Dict, Any, Optional

from zomato_rec.models.preferences import UserPreferences
from zomato_rec.models.recommendation import RecommendationResponse
from zomato_rec.data.index import RestaurantIndex
from zomato_rec.filtering.engine import FilterEngine
from zomato_rec.llm.client import LLMClient
from zomato_rec.llm.prompts import SYSTEM_PROMPT, build_user_prompt
from zomato_rec.llm.parser import parse_llm_json, merge_recommendations, build_deterministic_fallback

logger = logging.getLogger(__name__)

class LocationNotFoundError(ValueError):
    def __init__(self, requested_location: str, suggestions: List[str]):
        self.requested_location = requested_location
        self.suggestions = suggestions
        super().__init__(f"Location '{requested_location}' not found.")

class RecommendationService:
    def __init__(self, index: RestaurantIndex, filter_engine: FilterEngine, llm_client: LLMClient):
        self.index = index
        self.filter_engine = filter_engine
        self.llm_client = llm_client

    def validate_preferences(self, prefs: UserPreferences):
        """Validate that the location exists in the index, suggesting close matches if not."""
        location = prefs.location.strip()
        known_locations = self.index.get_locations()
        known_locations_lower = [l.lower() for l in known_locations]

        if location.lower() not in known_locations_lower:
            # Find close matches
            suggestions = difflib.get_close_matches(location, known_locations, n=3, cutoff=0.3)
            logger.warning(f"Location validation failed for '{location}'. Suggestions: {suggestions}")
            raise LocationNotFoundError(location, suggestions)

    async def get_recommendations(self, prefs: UserPreferences) -> RecommendationResponse:
        """Orchestrate the recommendation pipeline: validate -> filter -> prompt -> LLM -> parse."""
        # 1. Validate location
        self.validate_preferences(prefs)

        # 2. Filter candidates
        candidates = self.filter_engine.apply(prefs)
        filters_applied = {
            "location": prefs.location,
            "cuisine": prefs.cuisine,
            "budget": prefs.budget,
            "min_rating": prefs.min_rating,
            "online_order": prefs.online_order,
            "book_table": prefs.book_table
        }

        # 3. Empty candidates handling
        if not candidates:
            logger.info("No candidates matched preferences. Returning empty recommendations list.")
            return RecommendationResponse(
                summary="No restaurants matched your filters. Please loosen your criteria.",
                recommendations=[],
                filters_applied=filters_applied,
                candidate_count=0,
                relaxation_note=self.filter_engine.last_relaxation_note
            )

        # 4. Prompt construction
        user_prompt = build_user_prompt(prefs, candidates)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]

        # 5. LLM Completion and parsing with repair retry
        try:
            # Use json_object response format
            response_text = await self.llm_client.complete(
                messages,
                response_format={"type": "json_object"}
            )
            
            try:
                llm_data = parse_llm_json(response_text)
            except Exception as parse_err:
                logger.warning(f"LLM output failed to parse: {parse_err}. Attempting repair retry...")
                # Repair retry message thread
                repair_messages = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                    {"role": "assistant", "content": response_text},
                    {"role": "user", "content": (
                        f"Your response was not valid JSON. Parse error: {str(parse_err)}. "
                        "Please correct your response and return ONLY valid JSON matching the schema."
                    )}
                ]
                # Second attempt
                repair_response = await self.llm_client.complete(
                    repair_messages,
                    response_format={"type": "json_object"}
                )
                llm_data = parse_llm_json(repair_response)

            # Successfully parsed, merge with data records
            return merge_recommendations(llm_data, candidates, filters_applied)

        except Exception as e:
            logger.error(f"Error during recommendation orchestration: {e}. Falling back to deterministic results.")
            return build_deterministic_fallback(
                candidates,
                filters_applied,
                relaxation_note=self.filter_engine.last_relaxation_note
            )
