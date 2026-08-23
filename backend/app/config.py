import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BASE_DIR.parent
UPLOAD_DIR = BASE_DIR / "uploads"
DATABASE_URL = f"sqlite:///{BASE_DIR / 'wardrobe.db'}"
CHECKPOINT_DIR = PROJECT_DIR / "ml_training" / "checkpoints"
BEST_MODEL_PATH = CHECKPOINT_DIR / "best_scorer.pt"

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

# Master Clothing Taxonomy
CATEGORY_MAP = {
    "top": [
        "t-shirt", "formal shirt", "casual shirt", "polo shirt", 
        "sweater", "hoodie", "jacket", "blazer", "coat", "tank top"
    ],
    "bottom": [
        "denim jeans", "chinos", "formal trousers", "sweatpants", 
        "shorts", "cargo pants", "skirt"
    ],
    "footwear": [
        "sneakers", "formal leather shoes", "boots", "sandals", 
        "loafers", "running shoes"
    ],
    "outerwear": [
        "denim jacket", "leather jacket", "blazer", "winter coat", 
        "bomber jacket", "cardigan", "hoodie"
    ]
}

# Inverted mapping: subcategory -> major category
SUBCATEGORY_TO_MAIN = {}
for main_cat, sub_list in CATEGORY_MAP.items():
    for sub in sub_list:
        SUBCATEGORY_TO_MAIN[sub] = main_cat

# Default Occasions & Associated Formality Ranges (1-5 scale)
OCCASION_RULES = {
    "college": {
        "formality_min": 1,
        "formality_max": 3,
        "allowed_categories": ["top", "bottom", "footwear", "outerwear"],
        "disallowed_subcategories": ["pyjama", "formal leather shoes", "swimwear"],
        "description": "Smart casual, casual tees, jeans, hoodies & sneakers"
    },
    "home": {
        "formality_min": 1,
        "formality_max": 1,
        "allowed_categories": ["top", "bottom", "footwear"],
        "disallowed_subcategories": ["blazer", "formal trousers", "formal leather shoes"],
        "description": "Comfy loungewear, sweatpants, loose t-shirts, sandals"
    },
    "gym": {
        "formality_min": 1,
        "formality_max": 2,
        "allowed_categories": ["top", "bottom", "footwear"],
        "disallowed_subcategories": ["formal shirt", "denim jeans", "formal trousers", "blazer", "formal leather shoes", "boots"],
        "description": "Activewear, t-shirts, tank tops, sweatpants, shorts & running shoes"
    },
    "party": {
        "formality_min": 2,
        "formality_max": 4,
        "allowed_categories": ["top", "bottom", "footwear", "outerwear"],
        "disallowed_subcategories": ["sweatpants", "tank top", "sandals"],
        "description": "Stylish shirts, blazers, dark denim, chinos & sleek shoes"
    },
    "formal": {
        "formality_min": 4,
        "formality_max": 5,
        "allowed_categories": ["top", "bottom", "footwear", "outerwear"],
        "disallowed_subcategories": ["t-shirt", "hoodie", "sweatpants", "shorts", "sandals", "running shoes"],
        "description": "Formal shirts, trousers, blazers, suits & dress shoes"
    },
    "casual_outing": {
        "formality_min": 1,
        "formality_max": 3,
        "allowed_categories": ["top", "bottom", "footwear", "outerwear"],
        "disallowed_subcategories": ["formal trousers", "pyjama"],
        "description": "Casual hangout, cafes, movies & weekend strolls"
    },
    "date_night": {
        "formality_min": 3,
        "formality_max": 4,
        "allowed_categories": ["top", "bottom", "footwear", "outerwear"],
        "disallowed_subcategories": ["sweatpants", "shorts", "sandals", "tank top"],
        "description": "Elevated smart casual, stylish jackets, clean shoes"
    }
}

# Weather Warmth Mapping (1=Very Light/Summer, 5=Heavy Winter)
def get_warmth_range_for_temp(temp_celsius: float) -> tuple[int, int]:
    """Returns (min_warmth, max_warmth) suitable for temperature in Celsius."""
    if temp_celsius >= 28.0:
        return (1, 2)  # Hot / Summer
    elif temp_celsius >= 20.0:
        return (1, 3)  # Pleasant / Warm
    elif temp_celsius >= 14.0:
        return (2, 4)  # Mild / Cool (light layer helpful)
    elif temp_celsius >= 7.0:
        return (3, 5)  # Cold / Sweater or Jacket required
    else:
        return (4, 5)  # Very Cold / Heavy Winter Coat
