from fastapi import Request
from zomato_rec.data.index import RestaurantIndex
from zomato_rec.services.recommendation import RecommendationService

def get_index(request: Request) -> RestaurantIndex:
    """Retrieve the global RestaurantIndex from the FastAPI app state."""
    return request.app.state.index

def get_recommendation_service(request: Request) -> RecommendationService:
    """Retrieve the global RecommendationService from the FastAPI app state."""
    return request.app.state.recommendation_service
