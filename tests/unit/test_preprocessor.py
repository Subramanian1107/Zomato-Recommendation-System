import pytest
from zomato_rec.data.preprocessor import (
    parse_rating,
    parse_cost,
    parse_cuisines,
    parse_popular_dishes,
    parse_bool,
    parse_reviews,
    generate_restaurant_id
)

def test_parse_rating():
    assert parse_rating("4.5/5") == 4.5
    assert parse_rating("4.5") == 4.5
    assert parse_rating("4.1 / 5") == 4.1
    assert parse_rating("-") is None
    assert parse_rating("NEW") is None
    assert parse_rating(None) is None
    # clamp / bounds check
    assert parse_rating("6.0/5") is None  # invalid rating
    assert parse_rating("-1.0") is None

def test_parse_cost():
    assert parse_cost("1,200") == 1200
    assert parse_cost("500") == 500
    # Range string
    assert parse_cost("300-400") == 350
    assert parse_cost("invalid") is None
    assert parse_cost("") is None
    assert parse_cost(None) is None
    assert parse_cost("-100") is None  # invalid cost
    assert parse_cost("0") is None     # invalid cost

def test_parse_cuisines():
    assert parse_cuisines("North Indian, Chinese") == ["north indian", "chinese"]
    assert parse_cuisines(" South Indian ,Italian ") == ["south indian", "italian"]
    assert parse_cuisines("Cafe") == ["cafe"]
    assert parse_cuisines("") == []
    assert parse_cuisines(None) == []

def test_parse_popular_dishes():
    assert parse_popular_dishes("Pizza, Pasta, Mocktails") == ["Pizza", "Pasta", "Mocktails"]
    assert parse_popular_dishes("") == []
    assert parse_popular_dishes(None) == []

def test_parse_bool():
    assert parse_bool("Yes") is True
    assert parse_bool("yes") is True
    assert parse_bool("YES") is True
    assert parse_bool("No") is False
    assert parse_bool("no") is False
    assert parse_bool(None) is False

def test_parse_reviews():
    raw_reviews = "[('Rated 4.0', 'RATED\\n  Good food, nice ambience.'), ('Rated 5.0', 'RATED\\n  Loved it!')]"
    snippets = parse_reviews(raw_reviews)
    assert len(snippets) == 2
    assert snippets[0] == "Good food, nice ambience."
    assert snippets[1] == "Loved it!"
    
    # Check malformed
    assert parse_reviews("invalid python literal") == []
    assert parse_reviews("") == []
    assert parse_reviews(None) == []

def test_generate_restaurant_id():
    url = "https://www.zomato.com/bangalore/jalsa-banashankari"
    rid = generate_restaurant_id(url, 0)
    assert isinstance(rid, str)
    assert len(rid) == 32  # md5 hex string
    
    # stable check
    assert generate_restaurant_id(url, 0) == rid
    
    # fallback check
    assert generate_restaurant_id(None, 42) == "fallback_42"
    assert generate_restaurant_id("", 10) == "fallback_10"
