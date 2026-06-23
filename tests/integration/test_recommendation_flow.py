import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from zomato_rec.main import app
from zomato_rec.models.preferences import UserPreferences

@pytest.fixture(scope="module")
def client():
    # Context manager triggers startup and shutdown lifespan events
    with TestClient(app) as c:
        yield c

def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_metadata_endpoints(client):
    # Locations
    response_locs = client.get("/metadata/locations")
    assert response_locs.status_code == 200
    assert "locations" in response_locs.json()
    assert len(response_locs.json()["locations"]) > 0

    # Cuisines
    response_cuis = client.get("/metadata/cuisines")
    assert response_cuis.status_code == 200
    assert "cuisines" in response_cuis.json()
    assert len(response_cuis.json()["cuisines"]) > 0

    # Budget bands
    response_budget = client.get("/metadata/budget-bands")
    assert response_budget.status_code == 200
    json_data = response_budget.json()
    assert "low" in json_data
    assert "medium" in json_data
    assert "high" in json_data
    assert "min" in json_data["low"]
    assert "max" in json_data["low"]

@patch("zomato_rec.llm.groq_client.GroqClient.complete", new_callable=AsyncMock)
def test_recommendations_endpoint_success(mock_complete, client):
    # Grab the first valid restaurant in the loaded index to guarantee filters match
    all_restaurants = client.app.state.index.get_all()
    # Find a restaurant that has a cost and a rating to make it easy to filter
    test_record = None
    for r in all_restaurants:
        if r.cost_for_two is not None and r.rating is not None and r.cuisines:
            test_record = r
            break
            
    assert test_record is not None, "No suitable test record found in index"
    
    # Calculate which budget band this restaurant fits in
    ranges = client.app.state.index.get_budget_ranges()
    cost = test_record.cost_for_two
    budget_band = "medium"
    for band, (low, high) in ranges.items():
        if low <= cost <= high:
            budget_band = band
            break

    # Get the actual top filtered candidate from the filter engine
    filter_engine = client.app.state.filter_engine
    candidates = filter_engine.apply(UserPreferences(
        location=test_record.location,
        cuisine=test_record.cuisines[0],
        budget=budget_band,
        min_rating=test_record.rating
    ))
    assert len(candidates) > 0
    selected_candidate = candidates[0]

    # Mock the LLM output to return this restaurant ID
    mock_complete.return_value = f"""
    {{
      "summary": "AI recommended selection.",
      "recommendations": [
        {{
          "restaurant_id": "{selected_candidate.restaurant_id}",
          "explanation": "Matches perfectly.",
          "highlights": ["Nice food"]
        }}
      ]
    }}
    """

    payload = {
        "location": test_record.location,
        "cuisine": test_record.cuisines[0],
        "budget": budget_band,
        "min_rating": test_record.rating,
        "max_results": 5
    }
    
    # Remove print debugging
    response = client.post("/recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["summary"] == "AI recommended selection."
    assert len(data["recommendations"]) == 1
    assert data["recommendations"][0]["restaurant_id"] == selected_candidate.restaurant_id
    assert data["recommendations"][0]["name"] == selected_candidate.name

def test_recommendations_endpoint_invalid_location(client):
    payload = {
        "location": "NotARealBangaloreNeighborhood",
        "cuisine": "chinese",
        "budget": "medium"
    }
    response = client.post("/recommendations", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert "message" in data["detail"]
    assert "suggestions" in data["detail"]
