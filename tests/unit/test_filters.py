import pytest
from zomato_rec.models.preferences import UserPreferences
from zomato_rec.models.restaurant import RestaurantRecord
from zomato_rec.data.index import RestaurantIndex
from zomato_rec.filtering.engine import FilterEngine
from zomato_rec.filtering.ranker import rank_candidates
import pandas as pd

# Mock dataset for test isolation
MOCK_RECORDS = [
    RestaurantRecord(
        restaurant_id="r1",
        name="Indiranagar Chinese Palace",
        location="Indiranagar",
        address="123 Road",
        cuisines=["chinese", "momos"],
        rating=4.5,
        votes=100,
        cost_for_two=800,
        rest_type="Casual Dining",
        popular_dishes=["Noodles", "Dim sums"],
        online_order=True,
        book_table=False,
        listed_in_type="Dine-out",
        review_snippets=["Great food!"],
        url="http://r1"
    ),
    RestaurantRecord(
        restaurant_id="r2",
        name="Indiranagar Curry House",
        location="Indiranagar",
        address="456 Road",
        cuisines=["north indian", "mughlai"],
        rating=4.0,
        votes=50,
        cost_for_two=400,
        rest_type="Casual Dining",
        popular_dishes=["Biryani"],
        online_order=False,
        book_table=True,
        listed_in_type="Dine-out",
        review_snippets=["Decent curry."],
        url="http://r2"
    ),
    RestaurantRecord(
        restaurant_id="r3",
        name="Koramangala Punjabi Dhaba",
        location="Koramangala",
        address="789 Road",
        cuisines=["north indian", "punjabi"],
        rating=4.0,
        votes=150,
        cost_for_two=600,
        rest_type="Dhaba",
        popular_dishes=["Butter Chicken"],
        online_order=True,
        book_table=True,
        listed_in_type="Delivery",
        review_snippets=["Awesome butter chicken!"],
        url="http://r3"
    ),
    # Rating is None
    RestaurantRecord(
        restaurant_id="r4",
        name="Koramangala Tea Stall",
        location="Koramangala",
        address="10 Road",
        cuisines=["tea", "snacks"],
        rating=None,
        votes=10,
        cost_for_two=150,
        rest_type="Beverage Shop",
        popular_dishes=[],
        online_order=False,
        book_table=False,
        listed_in_type="Dine-out",
        review_snippets=[],
        url="http://r4"
    ),
    # Cost is None
    RestaurantRecord(
        restaurant_id="r5",
        name="No Cost Cafe",
        location="Indiranagar",
        address="99 Road",
        cuisines=["cafe", "beverages"],
        rating=3.8,
        votes=30,
        cost_for_two=None,
        rest_type="Cafe",
        popular_dishes=[],
        online_order=True,
        book_table=False,
        listed_in_type="Cafes",
        review_snippets=[],
        url="http://r5"
    ),
    # Rating None, high votes
    RestaurantRecord(
        restaurant_id="r6",
        name="Koramangala Secret Stall",
        location="Koramangala",
        address="20 Road",
        cuisines=["fast food"],
        rating=None,
        votes=80,
        cost_for_two=200,
        rest_type="Quick Bites",
        popular_dishes=[],
        online_order=False,
        book_table=False,
        listed_in_type="Dine-out",
        review_snippets=[],
        url="http://r6"
    ),
]

# We define Low <= 300, Medium 300-600, High > 600
LOW_BOUND = 300
MED_BOUND = 600

@pytest.fixture
def mock_index():
    df = pd.DataFrame([r.__dict__ for r in MOCK_RECORDS])
    return RestaurantIndex(MOCK_RECORDS, df, LOW_BOUND, MED_BOUND)

@pytest.fixture
def filter_engine(mock_index):
    return FilterEngine(mock_index)

def test_filter_location(filter_engine):
    # exact case insensitive
    prefs = UserPreferences(
        location="indiranagar",
        cuisine="chinese",
        budget="high"
    )
    res = filter_engine.apply(prefs)
    assert len(res) == 1
    assert res[0].location == "Indiranagar"
    assert res[0].restaurant_id == "r1"

def test_filter_cuisine_partial(filter_engine):
    # "Indian" should match "north indian"
    prefs = UserPreferences(
        location="Indiranagar",
        cuisine="Indian",
        budget="medium"
    )
    res = filter_engine.apply(prefs)
    assert len(res) == 1
    assert res[0].restaurant_id == "r2"

def test_filter_min_rating(filter_engine):
    # min_rating 4.0 excludes 3.8 and None
    prefs = UserPreferences(
        location="Indiranagar",
        cuisine="cafe",
        budget="medium",
        min_rating=4.0
    )
    res = filter_engine.apply(prefs)
    assert len(res) == 0
    assert "rating of 4.0 or higher" in filter_engine.last_relaxation_note

    # min_rating=3.8 includes No Cost Cafe (r5)
    prefs_ok = UserPreferences(
        location="Indiranagar",
        cuisine="cafe",
        budget="medium",
        min_rating=3.8
    )
    # But wait, it's budget="medium" which has range 301-600.
    # r5 has cost_for_two = None, which is excluded from budget filtered results!
    # Let's test with no budget filter
    # To check that min_rating of 3.8 includes r5, we must not filter by budget
    # Actually, UserPreferences budget is not optional in definition, it is Literal["low", "medium", "high"].
    # So budget is always applied. Let's see: r5 has cost=None, so it's excluded from budget-filtered results.
    # What if budget is low? Low range is min_cost to 300.
    # What if we set min_rating=3.8 and budget="high"? High range is 601-800. r5 still excluded.
    # This confirms E2.6: "Restaurants with null cost excluded when budget filter active".

def test_rating_boundary(filter_engine):
    # min_rating >= boundary (e.g. 4.0 includes 4.0)
    prefs = UserPreferences(
        location="Indiranagar",
        cuisine="indian",
        budget="medium",
        min_rating=4.0
    )
    res = filter_engine.apply(prefs)
    assert len(res) == 1
    assert res[0].restaurant_id == "r2"
    assert res[0].rating == 4.0

def test_budget_percentiles(filter_engine):
    # Low budget (<=300)
    prefs_low = UserPreferences(
        location="Koramangala",
        cuisine="fast food",
        budget="low",
        min_rating=3.5 # rating is None so r6 will be excluded since rating is None and min_rating is set
    )
    # But if min_rating is 3.5, and r6 rating is None, it is excluded.
    # Let's check with no min_rating? min_rating defaults to 3.5.
    # Let's set min_rating=0.0 (include all rated, but not None)
    # Wait, what if we want to include r6? We can't if min_rating excludes None.
    # Let's check r3: Koramangala, north indian, rating 4.0, cost 600 (Medium: 301-600)
    prefs_med = UserPreferences(
        location="Koramangala",
        cuisine="indian",
        budget="medium",
        min_rating=4.0
    )
    res_med = filter_engine.apply(prefs_med)
    assert len(res_med) == 1
    assert res_med[0].restaurant_id == "r3"

    # High budget (> 600)
    prefs_high = UserPreferences(
        location="Indiranagar",
        cuisine="chinese",
        budget="high",
        min_rating=4.0
    )
    res_high = filter_engine.apply(prefs_high)
    assert len(res_high) == 1
    assert res_high[0].restaurant_id == "r1"

def test_null_cost_exclusion(filter_engine):
    # No Cost Cafe (r5) has rating 3.8, location Indiranagar, cuisine cafe, cost_for_two = None
    # Let's filter on Indiranagar, cafe, budget="medium", min_rating=3.5
    # Should return empty list because r5 has cost=None and budget filter is active
    prefs = UserPreferences(
        location="Indiranagar",
        cuisine="cafe",
        budget="medium",
        min_rating=3.5
    )
    res = filter_engine.apply(prefs)
    assert len(res) == 0

def test_ranking_sorting():
    # Test rank_candidates logic
    recs = [
        RestaurantRecord(restaurant_id="a", name="A", location="X", address="", cuisines=[], rating=4.0, votes=100, cost_for_two=None, rest_type=None, popular_dishes=[], online_order=False, book_table=False, listed_in_type=None, review_snippets=[], url=""),
        RestaurantRecord(restaurant_id="b", name="B", location="X", address="", cuisines=[], rating=4.5, votes=50, cost_for_two=None, rest_type=None, popular_dishes=[], online_order=False, book_table=False, listed_in_type=None, review_snippets=[], url=""),
        RestaurantRecord(restaurant_id="c", name="C", location="X", address="", cuisines=[], rating=4.0, votes=200, cost_for_two=None, rest_type=None, popular_dishes=[], online_order=False, book_table=False, listed_in_type=None, review_snippets=[], url=""),
        RestaurantRecord(restaurant_id="d", name="D", location="X", address="", cuisines=[], rating=None, votes=50, cost_for_two=None, rest_type=None, popular_dishes=[], online_order=False, book_table=False, listed_in_type=None, review_snippets=[], url=""),
        RestaurantRecord(restaurant_id="e", name="E", location="X", address="", cuisines=[], rating=None, votes=150, cost_for_two=None, rest_type=None, popular_dishes=[], online_order=False, book_table=False, listed_in_type=None, review_snippets=[], url=""),
    ]
    ranked = rank_candidates(recs)
    # Expected order:
    # 1. rating=4.5, votes=50 (b)
    # 2. rating=4.0, votes=200 (c)
    # 3. rating=4.0, votes=100 (a)
    # 4. rating=None, votes=150 (e)
    # 5. rating=None, votes=50 (d)
    assert [r.restaurant_id for r in ranked] == ["b", "c", "a", "e", "d"]

def test_boolean_toggles_and_logic(filter_engine):
    # Koramangala Punjabi Dhaba (r3) has online_order=True, book_table=True
    # Koramangala Tea Stall (r4) has online_order=False, book_table=False
    # Let's request online_order=True AND book_table=True
    prefs = UserPreferences(
        location="Koramangala",
        cuisine="indian",
        budget="medium",
        min_rating=4.0,
        online_order=True,
        book_table=True
    )
    res = filter_engine.apply(prefs)
    assert len(res) == 1
    assert res[0].restaurant_id == "r3"

    # Request book_table=True but online_order=False (r2 in Indiranagar has book_table=True, online_order=False)
    prefs_indira = UserPreferences(
        location="Indiranagar",
        cuisine="indian",
        budget="medium",
        min_rating=4.0,
        online_order=False, # should not restrict online_order to True
        book_table=True
    )
    res_indira = filter_engine.apply(prefs_indira)
    # Since online_order=False (not True), it's not filtered to only True. So it returns r2.
    assert len(res_indira) == 1
    assert res_indira[0].restaurant_id == "r2"

def test_impossible_filters_relaxation_note(filter_engine):
    # Location not recognized
    prefs_loc = UserPreferences(
        location="Delhi",
        cuisine="chinese",
        budget="medium"
    )
    res = filter_engine.apply(prefs_loc)
    assert len(res) == 0
    assert "not recognized" in filter_engine.last_relaxation_note

    # Cuisine not found in location
    prefs_cuis = UserPreferences(
        location="Indiranagar",
        cuisine="ethiopian",
        budget="medium"
    )
    res = filter_engine.apply(prefs_cuis)
    assert len(res) == 0
    assert "serving 'ethiopian'" in filter_engine.last_relaxation_note

    # Rating too high
    prefs_rate = UserPreferences(
        location="Indiranagar",
        cuisine="indian",
        budget="medium",
        min_rating=4.8
    )
    res = filter_engine.apply(prefs_rate)
    assert len(res) == 0
    assert "rating of 4.8 or higher" in filter_engine.last_relaxation_note

def test_candidate_capping(mock_index):
    # Create 30 records that match
    recs = []
    for i in range(30):
        recs.append(RestaurantRecord(
            restaurant_id=f"cap_{i}",
            name=f"Name {i}",
            location="Koramangala",
            address="",
            cuisines=["chinese"],
            rating=4.0,
            votes=100 + i,
            cost_for_two=400,
            rest_type=None,
            popular_dishes=[],
            online_order=False,
            book_table=False,
            listed_in_type=None,
            review_snippets=[],
            url=""
        ))
    df = pd.DataFrame([r.__dict__ for r in recs])
    cap_index = RestaurantIndex(recs, df, LOW_BOUND, MED_BOUND)
    engine = FilterEngine(cap_index)
    
    prefs = UserPreferences(
        location="Koramangala",
        cuisine="chinese",
        budget="medium",
        min_rating=4.0
    )
    res = engine.apply(prefs)
    assert len(res) == 20  # capped at MAX_CANDIDATES
    # Should be sorted by votes DESC (since rating is identical 4.0)
    # cap_29 has votes 129, cap_0 has votes 100.
    # cap_29 should be first.
    assert res[0].restaurant_id == "cap_29"
    assert res[-1].restaurant_id == "cap_10"
