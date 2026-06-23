from dataclasses import dataclass
from typing import Optional, List

@dataclass
class RestaurantRecord:
    restaurant_id: str
    name: str
    location: str
    address: str
    cuisines: List[str]
    rating: Optional[float]
    votes: int
    cost_for_two: Optional[int]
    rest_type: Optional[str]
    popular_dishes: List[str]
    online_order: bool
    book_table: bool
    listed_in_type: Optional[str]
    review_snippets: List[str]
    url: str
