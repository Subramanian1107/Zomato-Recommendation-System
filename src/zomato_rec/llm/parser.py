import json
import logging
from typing import List, Dict, Any, Optional
from zomato_rec.models.restaurant import RestaurantRecord
from zomato_rec.models.recommendation import RecommendationItem, RecommendationResponse

logger = logging.getLogger(__name__)

def parse_llm_json(response_text: str) -> Dict[str, Any]:
    """Parse JSON string from the LLM, cleaning off markdown code blocks if present."""
    text = response_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    return json.loads(text)

def merge_recommendations(
    llm_data: Dict[str, Any],
    candidates: List[RestaurantRecord],
    filters_applied: Dict[str, Any]
) -> RecommendationResponse:
    """Validate IDs against candidates, merge database facts, and return RecommendationResponse."""
    candidates_map = {c.restaurant_id: c for c in candidates}
    recommendations: List[RecommendationItem] = []
    seen_ids = set()
    rank = 1

    for item in llm_data.get("recommendations", []):
        rest_id = item.get("restaurant_id")
        if not rest_id or rest_id not in candidates_map:
            logger.warning(f"Skipping unknown or empty restaurant_id from LLM: {rest_id}")
            continue

        if rest_id in seen_ids:
            continue
        seen_ids.add(rest_id)

        record = candidates_map[rest_id]
        explanation = item.get("explanation", "Recommended based on your preferences.")
        highlights = item.get("highlights", [])

        recommendations.append(RecommendationItem(
            rank=rank,
            restaurant_id=record.restaurant_id,
            name=record.name,
            location=record.location,
            cuisines=record.cuisines,
            rating=record.rating,
            votes=record.votes,
            cost_for_two=record.cost_for_two,
            rest_type=record.rest_type,
            online_order=record.online_order,
            book_table=record.book_table,
            explanation=explanation,
            highlights=highlights
        ))
        rank += 1

    summary = llm_data.get("summary", "Here are your recommended restaurants.")

    return RecommendationResponse(
        summary=summary,
        recommendations=recommendations,
        filters_applied=filters_applied,
        candidate_count=len(candidates)
    )

def build_deterministic_fallback(
    candidates: List[RestaurantRecord],
    filters_applied: Dict[str, Any],
    relaxation_note: Optional[str] = None
) -> RecommendationResponse:
    """Generate generic recommendations from the top 5 candidates as a fallback path."""
    logger.info("Triggering deterministic fallback recommendation response...")
    recommendations: List[RecommendationItem] = []
    
    top_5 = candidates[:5]
    for idx, record in enumerate(top_5):
        explanation = f"Top options in {record.location} serving {', '.join(record.cuisines[:2])}."
        highlights = [f"Rating: {record.rating or 'No Rating'}", f"Votes: {record.votes}"]
        if record.popular_dishes:
            highlights.append(f"Famous for: {', '.join(record.popular_dishes[:2])}")

        recommendations.append(RecommendationItem(
            rank=idx + 1,
            restaurant_id=record.restaurant_id,
            name=record.name,
            location=record.location,
            cuisines=record.cuisines,
            rating=record.rating,
            votes=record.votes,
            cost_for_two=record.cost_for_two,
            rest_type=record.rest_type,
            online_order=record.online_order,
            book_table=record.book_table,
            explanation=explanation,
            highlights=highlights
        ))

    summary = (
        "We encountered a temporary issue generating AI explanations. "
        "Here are the top-rated matching restaurants based on your preferences."
    )

    return RecommendationResponse(
        summary=summary,
        recommendations=recommendations,
        filters_applied=filters_applied,
        candidate_count=len(candidates),
        relaxation_note=relaxation_note
    )
