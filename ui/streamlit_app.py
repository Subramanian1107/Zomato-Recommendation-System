import streamlit as st
import httpx
import os
import asyncio
from typing import Optional

# Set page configuration for a premium layout
st.set_page_config(
    page_title="Zomato AI Recommendation Engine",
    page_icon="🍔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API endpoint configuration (defaults to empty/embedded mode if not specified)
API_URL = os.getenv("API_URL", "").strip()

# Inject Custom CSS for premium design (glassmorphic, vibrant colors, custom cards)
st.markdown("""
<style>
    /* Main app styles */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #12141d 0%, #1a1b2f 100%);
        color: #f3f4f6;
    }
    
    /* Header design */
    .title-container {
        padding: 2rem 0;
        text-align: center;
        background: linear-gradient(90deg, #ff416c 0%, #ff4b2b 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    
    .title-container h1 {
        font-size: 3rem;
        font-weight: 700;
        margin: 0;
    }
    
    .title-container p {
        font-size: 1.2rem;
        color: #9ca3af;
        margin-top: 0.5rem;
    }

    /* Glassmorphic Sidebar */
    [data-testid="stSidebar"] {
        background-color: rgba(26, 27, 47, 0.7);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Premium Card Design */
    .restaurant-card {
        background: rgba(30, 41, 59, 0.45);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        backdrop-filter: blur(12px);
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.2);
        transition: transform 0.2s, border-color 0.2s;
    }
    
    .restaurant-card:hover {
        transform: translateY(-2px);
        border-color: rgba(255, 75, 43, 0.4);
    }
    
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        padding-bottom: 0.75rem;
        margin-bottom: 0.75rem;
    }
    
    .restaurant-name {
        font-size: 1.5rem;
        font-weight: 600;
        color: #ffffff;
    }
    
    .restaurant-meta {
        font-size: 0.95rem;
        color: #9ca3af;
        margin-top: 0.2rem;
    }
    
    .rank-badge {
        background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.9rem;
    }
    
    .badge-container {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin: 0.5rem 0;
    }
    
    .tag-cuisine {
        background: rgba(99, 102, 241, 0.15);
        color: #a5b4fc;
        border: 1px solid rgba(99, 102, 241, 0.3);
        padding: 0.15rem 0.5rem;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: capitalize;
    }
    
    .tag-highlight {
        background: rgba(16, 185, 129, 0.15);
        color: #6ee7b7;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 0.15rem 0.5rem;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }

    .rating-container {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 1.1rem;
        color: #fbcfe8;
        font-weight: 600;
    }
    
    .star-icon {
        color: #f59e0b;
    }
    
    .ai-explanation {
        background: rgba(15, 23, 42, 0.3);
        border-left: 3px solid #ff4b2b;
        padding: 0.75rem 1rem;
        border-radius: 0 8px 8px 0;
        margin-top: 0.75rem;
        font-style: italic;
        color: #e2e8f0;
    }
    
    .cost-badge {
        font-weight: 600;
        color: #34d399;
    }
</style>
""", unsafe_allow_html=True)

# Application Header
st.markdown("""
<div class="title-container">
    <h1>Zomato Bangalore AI Recommendation Engine</h1>
    <p>Find the best local eats tailored by advanced AI reasoning</p>
</div>
""", unsafe_allow_html=True)

# Setup Embedded Mode Resources if API_URL is empty
if not API_URL:
    from zomato_rec.data.index import build_index
    from zomato_rec.filtering.engine import FilterEngine
    from zomato_rec.llm.groq_client import GroqClient
    from zomato_rec.services.recommendation import RecommendationService, LocationNotFoundError
    from zomato_rec.config import Settings
    from zomato_rec.models.preferences import UserPreferences

    @st.cache_resource
    def get_embedded_service():
        settings = Settings()
        index = build_index()
        filter_engine = FilterEngine(index)
        llm_client = GroqClient(settings)
        return RecommendationService(index, filter_engine, llm_client)

    try:
        service = get_embedded_service()
    except Exception as e:
        st.error(f"Failed to initialize embedded recommendation service: {e}")
        st.stop()

# Helper function to query metadata
@st.cache_data(show_spinner=False)
def fetch_metadata():
    if not API_URL:
        # Fetch directly from the embedded in-memory index
        ranges = service.index.get_budget_ranges()
        return {
            "locations": service.index.get_locations(),
            "cuisines": service.index.get_cuisines(),
            "budget_bands": {
                band: {"min": min_max[0], "max": min_max[1]}
                for band, min_max in ranges.items()
            }
        }
    else:
        # Fetch from FastAPI HTTP endpoints
        try:
            with httpx.Client(timeout=10.0) as client:
                locations_res = client.get(f"{API_URL}/metadata/locations")
                cuisines_res = client.get(f"{API_URL}/metadata/cuisines")
                bands_res = client.get(f"{API_URL}/metadata/budget-bands")
                
                if (locations_res.status_code == 200 and 
                    cuisines_res.status_code == 200 and 
                    bands_res.status_code == 200):
                    return {
                        "locations": locations_res.json()["locations"],
                        "cuisines": cuisines_res.json()["cuisines"],
                        "budget_bands": bands_res.json()
                    }
        except Exception as e:
            st.error(f"Error connecting to backend API: {e}")
    return None

# Load metadata
metadata = fetch_metadata()

if not metadata:
    st.markdown("""
    <div style="background: rgba(220, 38, 38, 0.15); border: 1px solid rgba(220, 38, 38, 0.4); padding: 1.5rem; border-radius: 8px; text-align: center;">
        <h3 style="color: #fca5a5; margin-bottom: 0.5rem;">Backend Server Unreachable</h3>
        <p style="color: #cbd5e1;">The UI couldn't connect to the FastAPI backend. Please make sure the API is running at <code>http://localhost:8000</code>.</p>
        <p style="color: #94a3b8; font-size: 0.9rem;">Run this command in a separate terminal: <code>source .venv/bin/activate && uvicorn zomato_rec.main:app --reload</code></p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Sidebar preference form
with st.sidebar:
    st.markdown("### 🛠️ Search Preferences")
    
    location_list = metadata["locations"]
    cuisine_list = metadata["cuisines"]
    
    selected_loc = st.selectbox(
        "Select Location / Neighborhood",
        options=location_list,
        help="Choose a neighborhood in Bangalore"
    )
    
    selected_cuisine = st.selectbox(
        "Select Cuisine",
        options=[c.title() for c in cuisine_list],
        help="Type or select a cuisine"
    ).lower()
    
    selected_budget = st.selectbox(
        "Budget Band",
        options=["low", "medium", "high"],
        format_func=lambda x: {
            "low": "Budget (Low)",
            "medium": "Mid-Range (Medium)",
            "high": "Premium (High)"
        }[x],
        help="Select spending level based on calculated local percentiles"
    )
    
    min_rating = st.slider(
        "Minimum Rating",
        min_value=0.0,
        max_value=5.0,
        value=3.5,
        step=0.1,
        help="Exclude restaurants below this rating boundary"
    )
    
    st.markdown("---")
    st.markdown("### ⚙️ Filters & Special Requests")
    
    online_order = st.checkbox("Online Order Available")
    book_table = st.checkbox("Table Booking Available")
    
    additional_prefs = st.text_area(
        "Soft Preferences / Requests",
        max_chars=500,
        placeholder="e.g., outdoor seating, quiet atmosphere, family friendly, famous for butter chicken...",
        help="AI will analyze reviews and descriptions to match these special requests"
    )
    
    max_results = st.number_input(
        "Number of recommendations",
        min_value=1,
        max_value=10,
        value=5,
        step=1
    )
    
    submit_button = st.button("🌟 Get AI Recommendations", use_container_width=True)

# Main results container
if submit_button:
    payload = {
        "location": selected_loc,
        "cuisine": selected_cuisine,
        "budget": selected_budget,
        "min_rating": min_rating,
        "additional_preferences": additional_prefs if additional_prefs.strip() else None,
        "online_order": online_order if online_order else None,
        "book_table": book_table if book_table else None,
        "max_results": int(max_results)
    }
    
    with st.spinner("🤖 AI is filtering reviews and ranking options..."):
        try:
            if not API_URL:
                # --- Embedded local mode ---
                prefs = UserPreferences(
                    location=selected_loc,
                    cuisine=selected_cuisine,
                    budget=selected_budget,
                    min_rating=min_rating,
                    additional_preferences=additional_prefs if additional_prefs.strip() else None,
                    online_order=online_order if online_order else None,
                    book_table=book_table if book_table else None,
                    max_results=int(max_results)
                )
                try:
                    # Run async function synchronously
                    response_obj = asyncio.run(service.get_recommendations(prefs))
                    data = response_obj.model_dump()
                    status_code = 200
                except LocationNotFoundError as e:
                    status_code = 422
                    error_detail = {
                        "message": f"Location '{e.requested_location}' is not recognized.",
                        "suggestions": e.suggestions
                    }
                except Exception as service_err:
                    status_code = 500
                    error_msg = str(service_err)
            else:
                # --- FastAPI API Mode ---
                with httpx.Client(timeout=45.0) as client:
                    res = client.post(f"{API_URL}/recommendations", json=payload)
                    status_code = res.status_code
                    if status_code == 200:
                        data = res.json()
                    elif status_code == 422:
                        error_detail = res.json().get("detail", {})
                    else:
                        error_msg = res.text

            # --- Render Response ---
            if status_code == 200:
                recommendations = data.get("recommendations", [])
                summary = data.get("summary", "")
                relaxation_note = data.get("relaxation_note")
                
                if not recommendations:
                    st.markdown(f"""
                    <div style="background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.4); padding: 1.5rem; border-radius: 8px; margin-bottom: 2rem;">
                        <h4 style="color: #fcd34d; margin-top: 0;">⚠️ No matching restaurants found</h4>
                        <p style="color: #e2e8f0; margin-bottom: 0;">{relaxation_note or "Try adjusting your budget, rating, or cuisine choices to see matches."}</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("### 📝 AI Recommendation Summary")
                    st.info(summary)
                    
                    st.markdown("---")
                    st.markdown(f"### 🍽️ Top Recommendations ({len(recommendations)})")
                    
                    for item in recommendations:
                        rank = item["rank"]
                        name = item["name"]
                        loc = item["location"]
                        rating = item["rating"]
                        votes = item["votes"]
                        cost = item["cost_for_two"]
                        cuisines = item["cuisines"]
                        explanation = item["explanation"]
                        highlights = item["highlights"]
                        
                        rating_str = f"⭐ {rating:.1f}" if rating else "⭐ No Rating"
                        votes_str = f"({votes} votes)" if rating else ""
                        cost_str = f"₹{cost} for two" if cost else "Cost details missing"
                        
                        cuisine_html = "".join([f'<span class="tag-cuisine">{c}</span>' for c in cuisines])
                        highlight_html = "".join([f'<span class="tag-highlight">{h}</span>' for h in highlights])
                        
                        card_html = f"""
                        <div class="restaurant-card">
                            <div class="card-header">
                                <div>
                                    <div class="restaurant-name">{name}</div>
                                    <div class="restaurant-meta">{loc} · <span class="cost-badge">{cost_str}</span></div>
                                </div>
                                <div class="rank-badge">#{rank}</div>
                            </div>
                            <div class="rating-container">
                                <span>{rating_str}</span> <span style="font-size: 0.85rem; color: #9ca3af; font-weight: 400;">{votes_str}</span>
                            </div>
                            <div class="badge-container">
                                {cuisine_html}
                            </div>
                            <div class="ai-explanation">
                                "{explanation}"
                            </div>
                            <div class="badge-container" style="margin-top: 0.75rem;">
                                {highlight_html}
                            </div>
                        </div>
                        """
                        st.markdown(card_html, unsafe_allow_html=True)
                        
            elif status_code == 422:
                msg = error_detail.get("message", "Validation error occurred.")
                suggs = error_detail.get("suggestions", [])
                suggs_str = ", ".join(suggs) if suggs else "None"
                
                st.error(f"❌ Input Error: {msg}")
                if suggs:
                    st.warning(f"💡 Did you mean: **{suggs_str}**?")
            else:
                st.error(f"❌ Error code {status_code}: {error_msg}")
        except Exception as e:
            st.error(f"❌ Error during recommendation request: {e}")
else:
    # Landing instructions
    st.markdown("""
    <div style="background: rgba(30, 41, 59, 0.3); border: 1px solid rgba(255, 255, 255, 0.05); padding: 2rem; border-radius: 12px; text-align: center; max-width: 800px; margin: 3rem auto;">
        <h3 style="color: #ffffff; margin-bottom: 0.75rem;">👋 Welcome to Zomato AI Recommendations!</h3>
        <p style="color: #cbd5e1; line-height: 1.6;">Use the sidebar panel on the left to set your dining preferences (neighborhood, cuisine type, spending level, rating limits, and special requests).</p>
        <p style="color: #94a3b8;">Click the <strong>Get AI Recommendations</strong> button to begin reasoning over 51,000+ Bangalore listings.</p>
    </div>
    """, unsafe_allow_html=True)
