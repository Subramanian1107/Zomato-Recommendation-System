import pytest
from zomato_rec.models.restaurant import RestaurantRecord
from zomato_rec.llm.parser import (
    parse_llm_json,
    merge_recommendations,
    build_deterministic_fallback
)

# Mock candidate records
MOCK_CANDIDATES = [
    RestaurantRecord(
        restaurant_id="r1",
        name="Restaurant One",
        location="Indiranagar",
        address="",
        cuisines=["chinese"],
        rating=4.5,
        votes=100,
        cost_for_two=500,
        rest_type=None,
        popular_dishes=[],
        online_order=True,
        book_table=False,
        listed_in_type=None,
        review_snippets=[],
        url=""
    ),
    RestaurantRecord(
        restaurant_id="r2",
        name="Restaurant Two",
        location="Indiranagar",
        address="",
        cuisines=["indian"],
        rating=4.0,
        votes=50,
        cost_for_two=400,
        rest_type=None,
        popular_dishes=[],
        online_order=False,
        book_table=True,
        listed_in_type=None,
        review_snippets=[],
        url=""
    )
]

def test_parse_llm_json_valid():
    raw = '{"summary": "Looks good", "recommendations": []}'
    parsed = parse_llm_json(raw)
    assert parsed["summary"] == "Looks good"
    assert parsed["recommendations"] == []

def test_parse_llm_json_markdown():
    raw = '```json\n{"summary": "Markdown formatting", "recommendations": []}\n```'
    parsed = parse_llm_json(raw)
    assert parsed["summary"] == "Markdown formatting"

def test_parse_llm_json_invalid():
    with pytest.raises(Exception):
        parse_llm_json("not a json string")

def test_merge_recommendations():
    llm_output = {
        "summary": "Great options",
        "recommendations": [
            {
                "restaurant_id": "r1",
                "explanation": "Loved the Chinese items here.",
                "highlights": ["Excellent Chinese"]
            },
            {
                "restaurant_id": "r2",
                "explanation": "Solid North Indian food.",
                "highlights": ["North Indian specialties"]
            },
            # unknown ID should be dropped
            {
                "restaurant_id": "r3",
                "explanation": "Unknown restaurant",
                "highlights": []
            }
        ]
    }
    
    response = merge_recommendations(llm_output, MOCK_CANDIDATES, {"location": "Indiranagar"})
    
    assert response.summary == "Great options"
    assert len(response.recommendations) == 2
    
    r_item1 = response.recommendations[0]
    assert r_item1.restaurant_id == "r1"
    assert r_item1.name == "Restaurant One"  # Sourced from candidate record, not LLM
    assert r_item1.rank == 1
    assert r_item1.explanation == "Loved the Chinese items here."
    
    r_item2 = response.recommendations[1]
    assert r_item2.restaurant_id == "r2"
    assert r_item2.name == "Restaurant Two"
    assert r_item2.rank == 2
    assert r_item2.explanation == "Solid North Indian food."

def test_merge_recommendations_deduplication():
    llm_output = {
        "summary": "Deduplicated recommendations",
        "recommendations": [
            {"restaurant_id": "r1", "explanation": "First explain", "highlights": []},
            {"restaurant_id": "r1", "explanation": "Duplicate explain", "highlights": []}
        ]
    }
    response = merge_recommendations(llm_output, MOCK_CANDIDATES, {})
    assert len(response.recommendations) == 1
    assert response.recommendations[0].restaurant_id == "r1"

def test_build_deterministic_fallback():
    response = build_deterministic_fallback(MOCK_CANDIDATES, {"location": "Indiranagar"}, "Relax filters warning")
    assert len(response.recommendations) == 2
    assert response.recommendations[0].restaurant_id == "r1"
    assert response.recommendations[0].rank == 1
    assert response.relaxation_note == "Relax filters warning"
    assert "temporary issue" in response.summary
