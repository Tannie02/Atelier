import os
import shutil
import uuid
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import UPLOAD_DIR, CATEGORY_MAP, SUBCATEGORY_TO_MAIN
from app.models.clothing_item import ClothingItem
from app.models.user import User
from app.schemas.wardrobe import (
    AutoTagPreviewResponse, ClothingItemCreate, 
    ClothingItemUpdate, ClothingItemResponse, ColorInfo
)
from app.routes.auth import get_current_user
from app.ml.clip_service import clip_service
from app.ml.color_extractor import extract_dominant_colors

router = APIRouter(prefix="/api/wardrobe", tags=["Wardrobe"])

TEMP_DIR = UPLOAD_DIR / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

@router.get("/categories")
def get_category_taxonomy():
    """Returns available categories and subcategories."""
    return CATEGORY_MAP

@router.post("/upload-preview", response_model=AutoTagPreviewResponse)
async def upload_preview(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Accepts an uploaded image, saves it temporarily, and runs AI/ML feature extraction:
    - CLIP zero-shot classification for category & subcategory
    - K-Means dominant color clustering & fashion color naming
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")

    ext = Path(file.filename).suffix or ".jpg"
    temp_filename = f"temp_{uuid.uuid4().hex[:10]}{ext}"
    temp_path = TEMP_DIR / temp_filename

    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 1. Run CLIP Zero-Shot Classification
    best_match, top_candidates = clip_service.zero_shot_classify(str(temp_path))

    # 2. Run K-Means Color Extraction
    dom_color_name, dom_color_hex, palette = extract_dominant_colors(str(temp_path), n_colors=3)

    warmth = best_match.get("default_warmth", 2)
    formality = best_match.get("default_formality", 2)

    suggested_occasions = ["college", "casual_outing"]
    if formality >= 4:
        suggested_occasions = ["formal", "party"]
    elif formality == 1:
        suggested_occasions = ["home", "gym", "college"]

    return AutoTagPreviewResponse(
        temp_image_url=f"/uploads/temp/{temp_filename}",
        suggested_category=best_match.get("category", "top"),
        suggested_subcategory=best_match.get("subcategory", "t-shirt"),
        top_candidate_tags=top_candidates,
        dominant_color_name=dom_color_name,
        dominant_color_hex=dom_color_hex,
        color_palette=[ColorInfo(**c) for c in palette],
        suggested_warmth=warmth,
        suggested_formality=formality,
        suggested_occasions=suggested_occasions
    )

@router.post("/items", response_model=ClothingItemResponse)
def create_clothing_item(
    item_in: ClothingItemCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Confirms auto-tagged/user-edited item details, moves image to permanent storage,
    computes & stores the 512-dim CLIP embedding, and creates database record for current user.
    """
    temp_filename = Path(item_in.image_filename).name
    temp_path = TEMP_DIR / temp_filename
    
    perm_filename = f"item_{uuid.uuid4().hex[:12]}{temp_path.suffix or '.jpg'}"
    perm_path = UPLOAD_DIR / perm_filename

    if temp_path.exists():
        shutil.move(str(temp_path), str(perm_path))
    else:
        existing_path = UPLOAD_DIR / temp_filename
        if existing_path.exists():
            perm_filename = temp_filename
            perm_path = existing_path
        else:
            raise HTTPException(status_code=400, detail="Image file not found.")

    clip_emb = clip_service.extract_image_embedding(str(perm_path))

    category = item_in.category
    if not category or category not in CATEGORY_MAP:
        category = SUBCATEGORY_TO_MAIN.get(item_in.subcategory.lower(), "top")

    palette_data = [p.dict() for p in item_in.color_palette]

    new_item = ClothingItem(
        user_id=current_user.id,
        image_path=perm_filename,
        category=category,
        subcategory=item_in.subcategory.lower(),
        dominant_color_name=item_in.dominant_color_name,
        dominant_color_hex=item_in.dominant_color_hex,
        warmth_level=item_in.warmth_level,
        formality_level=item_in.formality_level,
        notes=item_in.notes or ""
    )
    new_item.clip_embedding = clip_emb
    new_item.color_palette_json = str(palette_data).replace("'", '"')
    new_item.occasion_tags_json = str(item_in.occasion_tags).replace("'", '"')

    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return ClothingItemResponse(
        id=new_item.id,
        image_url=f"/uploads/{new_item.image_path}",
        category=new_item.category,
        subcategory=new_item.subcategory,
        dominant_color_name=new_item.dominant_color_name,
        dominant_color_hex=new_item.dominant_color_hex,
        color_palette=[ColorInfo(**c) for c in new_item.color_palette],
        warmth_level=new_item.warmth_level,
        formality_level=new_item.formality_level,
        occasion_tags=new_item.occasion_tags,
        notes=new_item.notes or "",
        created_at=new_item.created_at
    )

@router.get("/items", response_model=list[ClothingItemResponse])
def list_clothing_items(
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    color: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists all wardrobe items for the authenticated user."""
    query = db.query(ClothingItem).filter(ClothingItem.user_id == current_user.id)
    if category:
        query = query.filter(ClothingItem.category == category.lower())
    if subcategory:
        query = query.filter(ClothingItem.subcategory == subcategory.lower())
    if color:
        query = query.filter(ClothingItem.dominant_color_name.ilike(f"%{color}%"))
        
    items = query.order_by(ClothingItem.id.desc()).all()
    results = []
    for item in items:
        results.append(ClothingItemResponse(
            id=item.id,
            image_url=f"/uploads/{item.image_path}",
            category=item.category,
            subcategory=item.subcategory,
            dominant_color_name=item.dominant_color_name,
            dominant_color_hex=item.dominant_color_hex,
            color_palette=[ColorInfo(**c) for c in item.color_palette],
            warmth_level=item.warmth_level,
            formality_level=item.formality_level,
            occasion_tags=item.occasion_tags,
            notes=item.notes or "",
            created_at=item.created_at
        ))
    return results

@router.get("/items/{item_id}", response_model=ClothingItemResponse)
def get_clothing_item(
    item_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = db.query(ClothingItem).filter(ClothingItem.id == item_id).first()
    if not item or (item.user_id and item.user_id != current_user.id):
        raise HTTPException(status_code=404, detail="Item not found")
    return ClothingItemResponse(
        id=item.id,
        image_url=f"/uploads/{item.image_path}",
        category=item.category,
        subcategory=item.subcategory,
        dominant_color_name=item.dominant_color_name,
        dominant_color_hex=item.dominant_color_hex,
        color_palette=[ColorInfo(**c) for c in item.color_palette],
        warmth_level=item.warmth_level,
        formality_level=item.formality_level,
        occasion_tags=item.occasion_tags,
        notes=item.notes or "",
        created_at=item.created_at
    )

@router.put("/items/{item_id}", response_model=ClothingItemResponse)
def update_clothing_item(
    item_id: int, 
    item_update: ClothingItemUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = db.query(ClothingItem).filter(ClothingItem.id == item_id).first()
    if not item or (item.user_id and item.user_id != current_user.id):
        raise HTTPException(status_code=404, detail="Item not found")

    if item_update.category:
        item.category = item_update.category.lower()
    if item_update.subcategory:
        item.subcategory = item_update.subcategory.lower()
    if item_update.dominant_color_name:
        item.dominant_color_name = item_update.dominant_color_name
    if item_update.dominant_color_hex:
        item.dominant_color_hex = item_update.dominant_color_hex
    if item_update.warmth_level is not None:
        item.warmth_level = item_update.warmth_level
    if item_update.formality_level is not None:
        item.formality_level = item_update.formality_level
    if item_update.occasion_tags is not None:
        item.occasion_tags_json = str(item_update.occasion_tags).replace("'", '"')
    if item_update.notes is not None:
        item.notes = item_update.notes

    db.commit()
    db.refresh(item)
    return ClothingItemResponse(
        id=item.id,
        image_url=f"/uploads/{item.image_path}",
        category=item.category,
        subcategory=item.subcategory,
        dominant_color_name=item.dominant_color_name,
        dominant_color_hex=item.dominant_color_hex,
        color_palette=[ColorInfo(**c) for c in item.color_palette],
        warmth_level=item.warmth_level,
        formality_level=item.formality_level,
        occasion_tags=item.occasion_tags,
        notes=item.notes or "",
        created_at=item.created_at
    )

@router.delete("/items/{item_id}")
def delete_clothing_item(
    item_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = db.query(ClothingItem).filter(ClothingItem.id == item_id).first()
    if not item or (item.user_id and item.user_id != current_user.id):
        raise HTTPException(status_code=404, detail="Item not found")

    img_file = UPLOAD_DIR / item.image_path
    if img_file.exists():
        try:
            img_file.unlink()
        except Exception:
            pass

    db.delete(item)
    db.commit()
    return {"message": "Piece removed from closet successfully", "item_id": item_id}
