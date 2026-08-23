"""
Demo Wardrobe Seeder Script
===========================
Seeds initial high-quality wardrobe items (Tops, Bottoms, Footwear, Outerwear)
with generated sample photo swatches and 512-d CLIP embeddings so you can
test the outfit recommender right out of the box!

Usage:
------
python seed_demo_wardrobe.py
"""

import sys
import json
from pathlib import Path
from PIL import Image, ImageDraw

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR / "backend"
sys.path.append(str(BACKEND_DIR))

import numpy as np
from app.database import SessionLocal, engine, Base
from app.config import UPLOAD_DIR
from app.models.clothing_item import ClothingItem
from app.ml.clip_service import clip_service

# Create tables if not exist
Base.metadata.create_all(bind=engine)

SAMPLE_WARDROBE = [
    # TOPS
    {
        "category": "top",
        "subcategory": "t-shirt",
        "color_name": "White",
        "color_hex": "#f5f5f5",
        "bg_color": (245, 245, 245),
        "text": "Classic White Tee",
        "warmth": 1,
        "formality": 1,
        "occasions": ["college", "casual_outing", "gym", "home"]
    },
    {
        "category": "top",
        "subcategory": "casual shirt",
        "color_name": "Sky Blue",
        "color_hex": "#78afe6",
        "bg_color": (120, 175, 230),
        "text": "Oxford Cotton Shirt",
        "warmth": 2,
        "formality": 3,
        "occasions": ["college", "casual_outing", "date_night"]
    },
    {
        "category": "top",
        "subcategory": "formal shirt",
        "color_name": "Off-White / Cream",
        "color_hex": "#f0ebd3",
        "bg_color": (240, 235, 220),
        "text": "Crisp Formal Shirt",
        "warmth": 2,
        "formality": 5,
        "occasions": ["formal", "party", "date_night"]
    },
    {
        "category": "top",
        "subcategory": "hoodie",
        "color_name": "Heather Grey",
        "color_hex": "#8c8e91",
        "bg_color": (140, 142, 145),
        "text": "Cozy Oversized Hoodie",
        "warmth": 4,
        "formality": 1,
        "occasions": ["college", "home", "casual_outing"]
    },
    {
        "category": "top",
        "subcategory": "sweater",
        "color_name": "Burgundy / Maroon",
        "color_hex": "#5a1423",
        "bg_color": (90, 20, 35),
        "text": "Knit Crewneck Sweater",
        "warmth": 4,
        "formality": 3,
        "occasions": ["college", "date_night", "casual_outing"]
    },

    # BOTTOMS
    {
        "category": "bottom",
        "subcategory": "denim jeans",
        "color_name": "Denim / Indigo Blue",
        "color_hex": "#284678",
        "bg_color": (40, 70, 120),
        "text": "Slim Indigo Jeans",
        "warmth": 2,
        "formality": 2,
        "occasions": ["college", "casual_outing", "party", "date_night"]
    },
    {
        "category": "bottom",
        "subcategory": "chinos",
        "color_name": "Khaki / Beige",
        "color_hex": "#beaf8c",
        "bg_color": (190, 175, 140),
        "text": "Tailored Khaki Chinos",
        "warmth": 2,
        "formality": 3,
        "occasions": ["college", "casual_outing", "formal", "date_night"]
    },
    {
        "category": "bottom",
        "subcategory": "formal trousers",
        "color_name": "Charcoal",
        "color_hex": "#323237",
        "bg_color": (50, 50, 55),
        "text": "Charcoal Wool Trousers",
        "warmth": 3,
        "formality": 5,
        "occasions": ["formal", "party"]
    },
    {
        "category": "bottom",
        "subcategory": "sweatpants",
        "color_name": "Black",
        "color_hex": "#141414",
        "bg_color": (20, 20, 20),
        "text": "Athletic Joggers",
        "warmth": 2,
        "formality": 1,
        "occasions": ["gym", "home", "college"]
    },

    # FOOTWEAR
    {
        "category": "footwear",
        "subcategory": "sneakers",
        "color_name": "White",
        "color_hex": "#f5f5f5",
        "bg_color": (245, 245, 245),
        "text": "Clean White Sneakers",
        "warmth": 2,
        "formality": 2,
        "occasions": ["college", "casual_outing", "party", "date_night"]
    },
    {
        "category": "footwear",
        "subcategory": "running shoes",
        "color_name": "Black",
        "color_hex": "#141414",
        "bg_color": (20, 20, 20),
        "text": "Sport Running Shoes",
        "warmth": 2,
        "formality": 1,
        "occasions": ["gym", "home", "college"]
    },
    {
        "category": "footwear",
        "subcategory": "formal leather shoes",
        "color_name": "Dark Brown",
        "color_hex": "#3c2819",
        "bg_color": (60, 40, 25),
        "text": "Oxford Leather Shoes",
        "warmth": 2,
        "formality": 5,
        "occasions": ["formal", "party"]
    },
    {
        "category": "footwear",
        "subcategory": "boots",
        "color_name": "Camel / Tan",
        "color_hex": "#af7d4b",
        "bg_color": (175, 125, 75),
        "text": "Chelsea Suede Boots",
        "warmth": 4,
        "formality": 3,
        "occasions": ["college", "party", "date_night", "casual_outing"]
    },

    # OUTERWEAR
    {
        "category": "outerwear",
        "subcategory": "denim jacket",
        "color_name": "Denim / Indigo Blue",
        "color_hex": "#284678",
        "bg_color": (40, 70, 120),
        "text": "Classic Trucker Jacket",
        "warmth": 3,
        "formality": 2,
        "occasions": ["college", "casual_outing", "date_night"]
    },
    {
        "category": "outerwear",
        "subcategory": "blazer",
        "color_name": "Navy Blue",
        "color_hex": "#0f1e46",
        "bg_color": (15, 30, 70),
        "text": "Tailored Navy Blazer",
        "warmth": 3,
        "formality": 5,
        "occasions": ["formal", "party", "date_night"]
    }
]

def generate_item_image(bg_rgb: tuple, text: str, filename: str) -> str:
    """Generates an aesthetic item illustration placeholder."""
    img = Image.new("RGB", (400, 400), color=bg_rgb)
    draw = ImageDraw.Draw(img)
    
    # Add subtle border and styling card
    draw.rectangle([10, 10, 390, 390], outline=(255, 255, 255, 100), width=4)
    
    img_path = UPLOAD_DIR / filename
    img.save(img_path, "JPEG")
    return filename

def seed_database():
    db = SessionLocal()
    
    # Check if items exist
    count = db.query(ClothingItem).count()
    if count > 0:
        print(f"Database already contains {count} items. Preserving existing wardrobe and skipping seed.")
        db.close()
        return

    print("Seeding demo wardrobe with 15 curated items and extracting CLIP embeddings...")

    for idx, item_data in enumerate(SAMPLE_WARDROBE):
        filename = f"demo_item_{idx+1}.jpg"
        generate_item_image(item_data["bg_color"], item_data["text"], filename)
        
        full_img_path = str(UPLOAD_DIR / filename)
        emb = clip_service.extract_image_embedding(full_img_path)

        palette = [
            {"name": item_data["color_name"], "hex": item_data["color_hex"], "percentage": 85.0},
            {"name": "Off-White / Cream", "hex": "#f0ebd3", "percentage": 15.0}
        ]

        item = ClothingItem(
            image_path=filename,
            category=item_data["category"],
            subcategory=item_data["subcategory"],
            dominant_color_name=item_data["color_name"],
            dominant_color_hex=item_data["color_hex"],
            warmth_level=item_data["warmth"],
            formality_level=item_data["formality"],
            notes=item_data["text"]
        )
        item.clip_embedding = emb
        item.color_palette_json = json.dumps(palette)
        item.occasion_tags_json = json.dumps(item_data["occasions"])

        db.add(item)
    
    db.commit()
    print("[SUCCESS] Successfully seeded 15 items across Tops, Bottoms, Footwear, and Outerwear!")
    db.close()

if __name__ == "__main__":
    seed_database()
