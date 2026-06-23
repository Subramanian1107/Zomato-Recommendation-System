import logging
import time
import pandas as pd
from datasets import load_dataset

logger = logging.getLogger(__name__)

def load_raw_dataset() -> pd.DataFrame:
    """Load ManikaSaini/zomato-restaurant-recommendation split='train'."""
    logger.info("Starting raw dataset load from Hugging Face...")
    start_time = time.time()
    
    dataset = load_dataset("ManikaSaini/zomato-restaurant-recommendation", split="train")
    df = pd.DataFrame(dataset)
    
    elapsed = time.time() - start_time
    logger.info(f"Loaded raw dataset with {len(df)} rows in {elapsed:.2f} seconds.")
    return df
