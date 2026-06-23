from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, List, Any

from zomato_rec.models.preferences import UserPreferences
from zomato_rec.models.recommendation import RecommendationResponse
from zomato_rec.data.index import RestaurantIndex
from zomato_rec.services.recommendation import RecommendationService, LocationNotFoundError
from zomato_rec.api.dependencies import get_index, get_recommendation_service

router = APIRouter()

@router.get("/health")
def health_check() -> Dict[str, str]:
    """Liveness check endpoint."""
    return {"status": "ok"}

@router.get("/metadata/locations")
def get_locations(index: RestaurantIndex = Depends(get_index)) -> Dict[str, List[str]]:
    """List valid neighborhoods in Bangalore."""
    return {"locations": index.get_locations()}

@router.get("/metadata/cuisines")
def get_cuisines(index: RestaurantIndex = Depends(get_index)) -> Dict[str, List[str]]:
    """List all available cuisines in the dataset."""
    return {"cuisines": index.get_cuisines()}

@router.get("/metadata/budget-bands")
def get_budget_bands(index: RestaurantIndex = Depends(get_index)) -> Dict[str, Dict[str, int]]:
    """Return cost ranges (min, max) for low/medium/high bands."""
    ranges = index.get_budget_ranges()
    return {
        band: {"min": min_max[0], "max": min_max[1]}
        for band, min_max in ranges.items()
    }

@router.post("/recommendations", response_model=RecommendationResponse)
async def create_recommendations(
    prefs: UserPreferences,
    service: RecommendationService = Depends(get_recommendation_service)
) -> RecommendationResponse:
    """Generate restaurant recommendations based on user preferences."""
    try:
        response = await service.get_recommendations(prefs)
        return response
    except LocationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": f"Location '{e.requested_location}' is not recognized.",
                "suggestions": e.suggestions
            }
        )
