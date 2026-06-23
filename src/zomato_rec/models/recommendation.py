from typing import Any, List, Optional
from pydantic import BaseModel

class RecommendationItem(BaseModel):
    rank: int
    restaurant_id: str
    name: str
    location: str
    cuisines: List[str]
    rating: Optional[float]
    votes: int
    cost_for_two: Optional[int]
    rest_type: Optional[str]
    online_order: bool
    book_table: bool
    explanation: str
    highlights: List[str]

class RecommendationResponse(BaseModel):
    summary: str
    recommendations: List[RecommendationItem]
    filters_applied: dict[str, Any]
    candidate_count: int
    relaxation_note: Optional[str] = None
