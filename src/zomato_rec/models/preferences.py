from typing import Literal, Optional
from pydantic import BaseModel, Field

class UserPreferences(BaseModel):
    location: str
    cuisine: str
    budget: Literal["low", "medium", "high"]
    min_rating: float = Field(ge=0.0, le=5.0, default=3.5)
    additional_preferences: Optional[str] = None
    online_order: Optional[bool] = None
    book_table: Optional[bool] = None
    max_results: int = Field(default=5, ge=1, le=10)
