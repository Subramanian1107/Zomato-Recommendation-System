import logging
import os
from typing import List, Dict, Tuple, Optional
import pandas as pd
import numpy as np

from zomato_rec.config import Settings
from zomato_rec.models.restaurant import RestaurantRecord
from zomato_rec.data.loader import load_raw_dataset
from zomato_rec.data.preprocessor import preprocess_df

logger = logging.getLogger(__name__)

class RestaurantIndex:
    def __init__(self, records: List[RestaurantRecord], df: pd.DataFrame, low_bound: int, med_bound: int):
        self._records = records
        self._df = df
        self._low_bound = low_bound
        self._med_bound = med_bound
        
    def get_all(self) -> List[RestaurantRecord]:
        """Return all restaurant records."""
        return self._records
        
    def get_locations(self) -> List[str]:
        """Return unique sorted location names."""
        locs = set(r.location for r in self._records if r.location)
        return sorted(list(locs))
        
    def get_cuisines(self) -> List[str]:
        """Return unique sorted cuisines."""
        cuisines_set = set()
        for r in self._records:
            cuisines_set.update(r.cuisines)
        return sorted(list(cuisines_set))
        
    def get_budget_ranges(self) -> Dict[str, Tuple[int, int]]:
        """Return budget ranges (min, max) for low, medium, and high bands."""
        costs = [r.cost_for_two for r in self._records if r.cost_for_two is not None]
        min_cost = min(costs) if costs else 0
        max_cost = max(costs) if costs else 10000
        
        # Budget bands definitions:
        # Low: <= p33
        # Medium: p33 < cost <= p66
        # High: > p66
        # We ensure ranges are contiguous and include min/max
        return {
            "low": (min_cost, self._low_bound),
            "medium": (self._low_bound + 1, self._med_bound),
            "high": (self._med_bound + 1, max_cost)
        }

def build_index() -> RestaurantIndex:
    """Load cached preprocessed dataset, or download, preprocess, and cache it."""
    settings = Settings()
    cache_path = settings.DATA_CACHE_PATH
    
    # Create directory if it doesn't exist
    cache_dir = os.path.dirname(cache_path)
    if cache_dir and not os.path.exists(cache_dir):
        os.makedirs(cache_dir, exist_ok=True)
        
    if os.path.exists(cache_path):
        logger.info(f"Loading cached dataset from {cache_path}...")
        try:
            df = pd.read_parquet(cache_path)
            logger.info("Successfully loaded dataset from Parquet cache.")
        except Exception as e:
            logger.error(f"Failed to read parquet cache: {e}. Rebuilding...")
            df = _download_and_preprocess(cache_path)
    else:
        df = _download_and_preprocess(cache_path)
        
    # Calculate percentiles (p33, p66) for cost_for_two
    costs = df["cost_for_two"].dropna().values
    if len(costs) > 0:
        p33 = int(np.percentile(costs, 33))
        p66 = int(np.percentile(costs, 66))
    else:
        p33, p66 = 300, 600
        
    # Convert DataFrame to list of RestaurantRecord objects
    records = []
    for row in df.to_dict("records"):
        cuisines = row["cuisines"]
        if isinstance(cuisines, np.ndarray):
            cuisines = cuisines.tolist()
        elif not isinstance(cuisines, list):
            cuisines = list(cuisines) if cuisines else []
            
        dishes = row["popular_dishes"]
        if isinstance(dishes, np.ndarray):
            dishes = dishes.tolist()
        elif not isinstance(dishes, list):
            dishes = list(dishes) if dishes else []
            
        reviews = row["review_snippets"]
        if isinstance(reviews, np.ndarray):
            reviews = reviews.tolist()
        elif not isinstance(reviews, list):
            reviews = list(reviews) if reviews else []
            
        records.append(RestaurantRecord(
            restaurant_id=row["restaurant_id"],
            name=row["name"],
            location=row["location"],
            address=row["address"],
            cuisines=cuisines,
            rating=row["rating"] if pd.notna(row["rating"]) else None,
            votes=int(row["votes"]),
            cost_for_two=int(row["cost_for_two"]) if pd.notna(row["cost_for_two"]) else None,
            rest_type=row["rest_type"] if pd.notna(row["rest_type"]) else None,
            popular_dishes=dishes,
            online_order=bool(row["online_order"]),
            book_table=bool(row["book_table"]),
            listed_in_type=row["listed_in_type"] if pd.notna(row["listed_in_type"]) else None,
            review_snippets=reviews,
            url=row["url"]
        ))
        
    return RestaurantIndex(records, df, p33, p66)

def _download_and_preprocess(cache_path: str) -> pd.DataFrame:
    raw_df = load_raw_dataset()
    processed_df = preprocess_df(raw_df)
    
    logger.info(f"Saving processed dataset cache to {cache_path}...")
    try:
        processed_df.to_parquet(cache_path, index=False)
        logger.info("Cache saved successfully.")
    except Exception as e:
        logger.error(f"Failed to save parquet cache: {e}")
        
    return processed_df
