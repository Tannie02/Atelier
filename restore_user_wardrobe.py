"""
Restore User Uploaded Wardrobe
==============================
Scans user images in backend/uploads/, removes all demo_item placeholders,
and restores all user clothes with CLIP embeddings and color swatches.
"""

import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.append(str(BACKEND_DIR))

from app.database import SessionLocal, engine, Base
from app.config import UPLOAD_DIR
from app.models.clothing_item import ClothingItem
from app.ml.clip_service import clip_service
from app.ml.color_extractor import extract_dominant_colors

def restore_user_items():
    db = SessionLocal()

    # 1. Delete all demo placeholders from DB
    demo_items = db.query(ClothingItem).filter(ClothingItem.image_path.like("demo_item%")).all()
    print(f"Removing {len(demo_items)} placeholder demo items from DB...")
    for d in demo_items:
        db.delete(d)
    db.commit()

    # 2. Delete demo placeholder files on disk
    for f in UPLOAD_DIR.glob("demo_item_*.jpg"):
        try:
            f.unlink()
            print(f"Deleted demo placeholder file: {f.name}")
        except Exception:
            pass

    # 3. Find all user uploaded items
    user_files = [f for f in UPLOAD_DIR.glob("item_*.*") if f.is_file()]
    print(f"\nFound {len(user_files)} real user clothing photos on disk!")

    # Check which user items are already in DB
    existing_paths = {i.image_path for i in db.query(ClothingItem).all()}

    restored_count = 0
    for file_path in user_files:
        filename = file_path.name
        if filename in existing_paths:
            print(f"• Already in DB: {filename}")
            continue

        print(f"• Processing real photo: {filename}...")
        full_path = str(file_path)

        # 1. CLIP Zero-Shot Classification
        best_match, top_candidates = clip_service.zero_shot_classify(full_path)
        cat = best_match.get("category", "top")
        subcat = best_match.get("subcategory", "t-shirt")
        warmth = best_match.get("default_warmth", 2)
        formality = best_match.get("default_formality", 2)

        # 2. K-Means Color Extraction
        color_name, color_hex, palette = extract_dominant_colors(full_path, n_colors=3)

        # 3. 512-dim CLIP Embedding
        emb = clip_service.extract_image_embedding(full_path)

        item = ClothingItem(
            image_path=filename,
            category=cat,
            subcategory=subcat,
            dominant_color_name=color_name,
            dominant_color_hex=color_hex,
            warmth_level=warmth,
            formality_level=formality,
            notes="My wardrobe piece"
        )
        item.clip_embedding = emb
        item.color_palette_json = json.dumps(palette)
        item.occasion_tags_json = json.dumps(["college", "casual_outing", "party"])

        db.add(item)
        restored_count += 1

    db.commit()
    total_in_db = db.query(ClothingItem).count()
    db.close()

    print(f"\n[SUCCESS] Restored {restored_count} user photos! Total items in closet: {total_in_db}")

if __name__ == "__main__":
    restore_user_items()
