import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from zomato_rec.config import Settings
from zomato_rec.data.index import build_index
from zomato_rec.filtering.engine import FilterEngine
from zomato_rec.llm.groq_client import GroqClient
from zomato_rec.services.recommendation import RecommendationService
from zomato_rec.api.routes import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    logger.info("Initializing Zomato AI Recommendation App...")
    start_time = time.time()
    
    settings = Settings()
    
    # 1. Build Index (loads from Parquet cache or downloads HF dataset)
    logger.info("Building RestaurantIndex...")
    index = build_index()
    
    # 2. Initialize Engine, LLM Client, and Service
    logger.info("Initializing components...")
    filter_engine = FilterEngine(index)
    llm_client = GroqClient(settings)
    recommendation_service = RecommendationService(index, filter_engine, llm_client)
    
    # 3. Store singletons in app state
    app.state.index = index
    app.state.filter_engine = filter_engine
    app.state.llm_client = llm_client
    app.state.recommendation_service = recommendation_service
    
    elapsed = time.time() - start_time
    logger.info(
        f"Zomato AI startup completed successfully in {elapsed:.2f} seconds. "
        f"Indexed {len(index.get_all())} restaurants."
    )
    
    yield
    
    # Shutdown tasks (none required for in-memory)
    logger.info("Shutting down Zomato AI Recommendation App...")

app = FastAPI(
    title="Zomato AI Restaurant Recommendation System",
    description="FastAPI + Groq LLM Recommendation Engine for Bangalore restaurants",
    version="0.1.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API endpoints
app.include_router(router)
