from typing import List
from zomato_rec.models.restaurant import RestaurantRecord

def filter_by_location(records: List[RestaurantRecord], location: str) -> List[RestaurantRecord]:
    """Exact case-insensitive match on location (stripped)."""
    loc_clean = location.strip().lower()
    return [r for r in records if r.location and r.location.strip().lower() == loc_clean]

def filter_by_cuisine(records: List[RestaurantRecord], cuisine: str) -> List[RestaurantRecord]:
    """Substring match on cuisines list (case-insensitive)."""
    c_clean = cuisine.strip().lower()
    return [r for r in records if any(c_clean in c for c in r.cuisines)]

def filter_by_rating(records: List[RestaurantRecord], min_rating: float) -> List[RestaurantRecord]:
    """Exclude records with rating=None or rating < min_rating."""
    return [r for r in records if r.rating is not None and r.rating >= min_rating]

def filter_by_budget(records: List[RestaurantRecord], budget: str, budget_ranges: dict) -> List[RestaurantRecord]:
    """Filter by budget band (low, medium, high) cost range. Excludes records with cost=None."""
    if budget not in budget_ranges:
        return records
    min_cost, max_cost = budget_ranges[budget]
    return [r for r in records if r.cost_for_two is not None and min_cost <= r.cost_for_two <= max_cost]

def filter_by_online_order(records: List[RestaurantRecord]) -> List[RestaurantRecord]:
    """Filter records to only those supporting online ordering."""
    return [r for r in records if r.online_order]

def filter_by_book_table(records: List[RestaurantRecord]) -> List[RestaurantRecord]:
    """Filter records to only those supporting table booking."""
    return [r for r in records if r.book_table]
