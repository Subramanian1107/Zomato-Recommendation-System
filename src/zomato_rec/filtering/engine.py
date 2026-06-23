import logging
from typing import List, Optional

from zomato_rec.config import Settings
from zomato_rec.models.preferences import UserPreferences
from zomato_rec.models.restaurant import RestaurantRecord
from zomato_rec.data.index import RestaurantIndex
from zomato_rec.filtering.hard_filters import (
    filter_by_location,
    filter_by_cuisine,
    filter_by_rating,
    filter_by_budget,
    filter_by_online_order,
    filter_by_book_table
)
from zomato_rec.filtering.ranker import rank_candidates

logger = logging.getLogger(__name__)

class FilterEngine:
    def __init__(self, index: RestaurantIndex):
        self.index = index
        self.last_relaxation_note: Optional[str] = None

    def apply(self, prefs: UserPreferences) -> List[RestaurantRecord]:
        """Apply sequential hard filters according to user preferences and return ranked candidates.
        Sets self.last_relaxation_note if any filter returns zero results.
        """
        self.last_relaxation_note = None
        candidates = self.index.get_all()
        
        # 1. Location Filter
        if prefs.location:
            prev_count = len(candidates)
            candidates = filter_by_location(candidates, prefs.location)
            logger.info(f"Location filter applied: {prev_count} -> {len(candidates)}")
            if len(candidates) == 0:
                known_locations = self.index.get_locations()
                known_locs_lower = [l.lower() for l in known_locations]
                loc_clean = prefs.location.strip().lower()
                if loc_clean not in known_locs_lower:
                    self.last_relaxation_note = f"Location '{prefs.location}' is not recognized. Please select a valid Bangalore neighborhood."
                else:
                    self.last_relaxation_note = f"No restaurants found in neighborhood '{prefs.location}'."
                return []

        # 2. Cuisine Filter
        if prefs.cuisine:
            prev_count = len(candidates)
            candidates = filter_by_cuisine(candidates, prefs.cuisine)
            logger.info(f"Cuisine filter applied: {prev_count} -> {len(candidates)}")
            if len(candidates) == 0:
                self.last_relaxation_note = (
                    f"No restaurants found in '{prefs.location}' serving '{prefs.cuisine}'. "
                    f"Try selecting a different cuisine or location."
                )
                return []

        # 3. Rating Filter
        if prefs.min_rating is not None:
            prev_count = len(candidates)
            candidates = filter_by_rating(candidates, prefs.min_rating)
            logger.info(f"Rating filter applied (min_rating={prefs.min_rating}): {prev_count} -> {len(candidates)}")
            if len(candidates) == 0:
                self.last_relaxation_note = (
                    f"No restaurants in '{prefs.location}' serving '{prefs.cuisine}' have a rating of {prefs.min_rating} or higher. "
                    f"Try lowering the minimum rating requirement."
                )
                return []

        # 4. Budget Filter
        if prefs.budget:
            prev_count = len(candidates)
            budget_ranges = self.index.get_budget_ranges()
            candidates = filter_by_budget(candidates, prefs.budget, budget_ranges)
            logger.info(f"Budget filter applied ({prefs.budget}): {prev_count} -> {len(candidates)}")
            if len(candidates) == 0:
                self.last_relaxation_note = (
                    f"No restaurants in '{prefs.location}' serving '{prefs.cuisine}' with rating >= {prefs.min_rating} "
                    f"matched the '{prefs.budget}' budget band. Try selecting a different budget band."
                )
                return []

        # 5. Online Order Toggle
        if prefs.online_order:
            prev_count = len(candidates)
            candidates = filter_by_online_order(candidates)
            logger.info(f"Online order filter applied: {prev_count} -> {len(candidates)}")
            if len(candidates) == 0:
                self.last_relaxation_note = (
                    f"No restaurants in '{prefs.location}' matching your criteria support online ordering. "
                    f"Try disabling the online ordering preference."
                )
                return []

        # 6. Book Table Toggle
        if prefs.book_table:
            prev_count = len(candidates)
            candidates = filter_by_book_table(candidates)
            logger.info(f"Book table filter applied: {prev_count} -> {len(candidates)}")
            if len(candidates) == 0:
                self.last_relaxation_note = (
                    f"No restaurants in '{prefs.location}' matching your criteria support table bookings. "
                    f"Try disabling the table booking preference."
                )
                return []

        # Rank the remaining candidates
        ranked_candidates = rank_candidates(candidates)

        # Limit to MAX_CANDIDATES
        settings = Settings()
        max_candidates = settings.MAX_CANDIDATES
        final_candidates = ranked_candidates[:max_candidates]
        logger.info(f"Filter engine finished. Output candidates: {len(final_candidates)}")
        
        return final_candidates
