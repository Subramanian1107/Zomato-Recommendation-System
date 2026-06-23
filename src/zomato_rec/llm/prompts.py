import json
from typing import List
from zomato_rec.models.preferences import UserPreferences
from zomato_rec.models.restaurant import RestaurantRecord

SYSTEM_PROMPT = """You are the Zomato AI Restaurant Recommendation Assistant, a local dining expert in Bangalore, India.
Your task is to rank and recommend the best restaurants from a provided candidate list based on the user's preferences.

You MUST follow these strict rules:
1. ONLY recommend restaurants that are in the provided candidates list. Do NOT invent new restaurants or suggest places not explicitly listed.
2. Refer to restaurants ONLY by their exact `restaurant_id` as specified in the candidates list.
3. Be fully honest and grounded. Never fabricate ratings, cost, or features.
4. If the user specifies soft preferences (in `additional_preferences`), address how well the top recommendations satisfy them. If a preference cannot be met, explain the compromise/trade-off.
5. You MUST return your response as a valid JSON object matching this schema:
{
  "summary": "A brief paragraph summarizing why these recommendations were chosen and how they fit the user's preferences, including any soft preference trade-offs.",
  "recommendations": [
    {
      "restaurant_id": "The exact restaurant_id from the candidate list",
      "explanation": "A detailed, personalized explanation of why this restaurant is a great match, mentioning specific dishes, customer reviews, or vibes that align with the user's soft preferences.",
      "highlights": ["A bullet list of 2-4 key features, e.g., 'Famous for Butter Chicken', 'Cozy outdoor seating', 'Affordable rates'"]
    }
  ]
}
Return ONLY this JSON object. Do not include markdown code block formatting (like ```json) in your raw output.
"""

def build_user_prompt(prefs: UserPreferences, candidates: List[RestaurantRecord]) -> str:
    """Build the user prompt containing preferences and compact candidate data."""
    # Truncate additional preferences to prevent prompt injection or excessive length
    add_prefs = prefs.additional_preferences or ""
    if len(add_prefs) > 500:
        add_prefs = add_prefs[:500] + "..."

    candidates_data = []
    for c in candidates:
        candidates_data.append({
            "restaurant_id": c.restaurant_id,
            "name": c.name,
            "rating": c.rating,
            "votes": c.votes,
            "cost_for_two": c.cost_for_two,
            "cuisines": c.cuisines,
            "popular_dishes": c.popular_dishes,
            "review_snippets": c.review_snippets
        })

    user_data = {
        "user_preferences": {
            "location": prefs.location,
            "cuisine": prefs.cuisine,
            "budget": prefs.budget,
            "min_rating": prefs.min_rating,
            "online_order": prefs.online_order,
            "book_table": prefs.book_table,
            "additional_preferences": add_prefs
        },
        "candidates": candidates_data
    }

    return json.dumps(user_data, indent=2)
