import logging
import hashlib
import ast
import re
from typing import Optional, List, Any
import pandas as pd

logger = logging.getLogger(__name__)

def parse_rating(val: Any) -> Optional[float]:
    """Parse rating from formats like "4.5/5", "NEW", "-", or missing.
    Clamps value between 0.0 and 5.0. Returns None if invalid or missing.
    """
    if pd.isna(val) or val is None:
        return None
    
    val_str = str(val).strip()
    if not val_str or val_str == "-" or val_str.upper() == "NEW":
        return None
    
    # Extract the first float-like substring (e.g., "4.5" from "4.5/5" or "-1.0")
    try:
        # Match pattern like X.Y or X with optional sign
        match = re.match(r'^([+-]?[0-9]+(?:\.[0-9]+)?)(?:\s*/\s*5)?$', val_str)
        if match:
            rating = float(match.group(1))
            if 0.0 <= rating <= 5.0:
                return rating
            else:
                logger.warning(f"Rating {rating} out of range [0, 5], setting to None.")
                return None
    except Exception:
        pass
    
    # Fallback to general regex search for any float with optional sign
    try:
        match = re.search(r'[-+]?(?:\d+\.\d+|\d+)', val_str)
        if match:
            rating = float(match.group())
            if 0.0 <= rating <= 5.0:
                return rating
            else:
                logger.warning(f"Rating {rating} out of range [0, 5], setting to None.")
    except Exception:
        pass
        
    return None

def parse_cost(val: Any) -> Optional[int]:
    """Parse cost from formats like "1,200", "300-400", non-numeric, or missing.
    Takes lower bound for range strings. Returns None if negative/zero/invalid.
    """
    if pd.isna(val) or val is None:
        return None
    
    val_str = str(val).strip().replace(",", "")
    if not val_str:
        return None
    
    # Handle range like "300-400"
    if "-" in val_str and not val_str.startswith("-"):
        parts = val_str.split("-")
        try:
            low = float(parts[0].strip())
            high = float(parts[1].strip())
            mid = int((low + high) / 2)
            return mid if mid > 0 else None
        except (ValueError, IndexError):
            pass
            
    # Try parsing first sequence of digits with optional sign
    try:
        match = re.search(r'[-+]?\d+', val_str)
        if match:
            cost = int(match.group())
            return cost if cost > 0 else None
    except Exception:
        pass
        
    return None

def parse_cuisines(val: Any) -> List[str]:
    """Split comma-separated cuisines, strip whitespace, and normalize to lowercase."""
    if pd.isna(val) or val is None:
        return []
    
    val_str = str(val).strip()
    if not val_str:
        return []
        
    return [c.strip().lower() for c in val_str.split(",") if c.strip()]

def parse_popular_dishes(val: Any) -> List[str]:
    """Split comma-separated popular dishes and strip whitespace."""
    if pd.isna(val) or val is None:
        return []
    
    val_str = str(val).strip()
    if not val_str:
        return []
        
    return [d.strip() for d in val_str.split(",") if d.strip()]

def parse_bool(val: Any) -> bool:
    """Map "Yes"/"No" case-insensitively to boolean. Defaults to False."""
    if pd.isna(val) or val is None:
        return False
    return str(val).strip().lower() == "yes"

def parse_reviews(val: Any) -> List[str]:
    """Safely parse Python-literal string tuples, extract review text,
    truncate each snippet to 200 chars, and return up to 3 snippets.
    """
    if pd.isna(val) or val is None:
        return []
        
    val_str = str(val).strip()
    if not val_str or val_str == "[]":
        return []
        
    try:
        reviews = ast.literal_eval(val_str)
        if not isinstance(reviews, list):
            return []
            
        snippets = []
        for r in reviews:
            # Format is typically (rating, review_text) or similar
            if isinstance(r, tuple) and len(r) >= 2:
                text = r[1]
                if isinstance(text, str):
                    # Clean prefix "RATED\n" or "RATED"
                    cleaned_text = re.sub(r'^RATED\s*', '', text, flags=re.IGNORECASE).strip()
                    if cleaned_text:
                        snippets.append(cleaned_text[:200])
            if len(snippets) >= 3:
                break
        return snippets
    except Exception:
        return []

def generate_restaurant_id(url: Any, idx: int) -> str:
    """Generate a stable restaurant_id from url hash, or fallback to index."""
    if pd.isna(url) or url is None:
        return f"fallback_{idx}"
        
    url_str = str(url).strip()
    if not url_str:
        return f"fallback_{idx}"
        
    return hashlib.md5(url_str.encode("utf-8")).hexdigest()

def preprocess_df(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and preprocess the raw restaurant DataFrame.
    Returns a DataFrame with renamed, normalized columns.
    """
    logger.info("Starting DataFrame preprocessing...")
    processed_rows = []
    
    for idx, row in df.iterrows():
        # Extrapolate restaurant_id
        url = row.get("url")
        rest_id = generate_restaurant_id(url, idx)
        
        # Parse fields
        rating = parse_rating(row.get("rate"))
        cost = parse_cost(row.get("approx_cost(for two people)"))
        cuisines = parse_cuisines(row.get("cuisines"))
        dishes = parse_popular_dishes(row.get("dish_liked"))
        online_order = parse_bool(row.get("online_order"))
        book_table = parse_bool(row.get("book_table"))
        reviews = parse_reviews(row.get("reviews_list"))
        
        # Votes check
        try:
            votes = int(row.get("votes", 0))
        except Exception:
            votes = 0
            
        # Basic fields
        name = str(row.get("name", "")).strip()
        location = str(row.get("location", "")).strip()
        address = str(row.get("address", "")).strip()
        rest_type = str(row.get("rest_type", "")).strip() if pd.notna(row.get("rest_type")) else None
        listed_in_type = str(row.get("listed_in(type)", "")).strip() if pd.notna(row.get("listed_in(type)")) else None
        url_val = str(url).strip() if pd.notna(url) else ""
        
        processed_rows.append({
            "restaurant_id": rest_id,
            "name": name,
            "location": location,
            "address": address,
            "cuisines": cuisines,
            "rating": rating,
            "votes": votes,
            "cost_for_two": cost,
            "rest_type": rest_type,
            "popular_dishes": dishes,
            "online_order": online_order,
            "book_table": book_table,
            "listed_in_type": listed_in_type,
            "review_snippets": reviews,
            "url": url_val
        })
        
    processed_df = pd.DataFrame(processed_rows)
    logger.info(f"Preprocessing completed. Processed {len(processed_df)} rows.")
    return processed_df
