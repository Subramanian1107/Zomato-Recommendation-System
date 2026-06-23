from typing import List
from zomato_rec.models.restaurant import RestaurantRecord

def rank_candidates(candidates: List[RestaurantRecord]) -> List[RestaurantRecord]:
    """Sort candidates by rating (descending), then votes (descending),
    with stable tie-breaking on name and restaurant_id.
    Treats None ratings as the lowest possible rating (-1.0).
    """
    def sort_key(r: RestaurantRecord):
        rating_val = r.rating if r.rating is not None else -1.0
        # Negate values to achieve descending sort using standard ascending Python sorting.
        # Strings are sorted alphabetically.
        return (-rating_val, -r.votes, r.name or "", r.restaurant_id or "")

    return sorted(candidates, key=sort_key)
