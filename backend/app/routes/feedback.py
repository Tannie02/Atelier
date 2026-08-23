import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pathlib import Path

from app.database import get_db
from app.models.outfit import OutfitRecommendation
from app.models.feedback import OutfitFeedback
from app.models.clothing_item import ClothingItem
from app.models.user import User
from app.schemas.feedback import FeedbackCreate, FeedbackResponse, FeedbackStatsResponse
from app.routes.auth import get_current_user

router = APIRouter(prefix="/api/feedback", tags=["Feedback Loop"])

@router.post("", response_model=FeedbackResponse)
def submit_feedback(
    fb_in: FeedbackCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submits Thumbs Up (+1) or Thumbs Down (-1) on a suggested outfit for current user.
    """
    outfit = db.query(OutfitRecommendation).filter(OutfitRecommendation.id == fb_in.outfit_id).first()
    if not outfit:
        raise HTTPException(status_code=404, detail="Outfit recommendation not found")

    if fb_in.rating not in [1, -1]:
        raise HTTPException(status_code=400, detail="Rating must be +1 (Like) or -1 (Dislike)")

    # Check if feedback already exists for this outfit by this user
    existing = db.query(OutfitFeedback).filter(
        OutfitFeedback.outfit_id == fb_in.outfit_id,
        OutfitFeedback.user_id == current_user.id
    ).first()
    
    if existing:
        existing.rating = fb_in.rating
        existing.feedback_reason = fb_in.feedback_reason or ""
        db.commit()
        db.refresh(existing)
        fb_record = existing
    else:
        fb_record = OutfitFeedback(
            user_id=current_user.id,
            outfit_id=fb_in.outfit_id,
            rating=fb_in.rating,
            feedback_reason=fb_in.feedback_reason or ""
        )
        db.add(fb_record)
        db.commit()
        db.refresh(fb_record)

    msg = "Impression saved to your style profile! ❤️" if fb_in.rating == 1 else "Noted! We'll adjust your style profile."
    return FeedbackResponse(
        id=fb_record.id,
        outfit_id=fb_record.outfit_id,
        rating=fb_record.rating,
        feedback_reason=fb_record.feedback_reason,
        created_at=fb_record.created_at,
        message=msg
    )

@router.get("/stats", response_model=FeedbackStatsResponse)
def get_feedback_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns total likes and dislikes logged to date for current user."""
    feedbacks = db.query(OutfitFeedback).filter(
        OutfitFeedback.user_id == current_user.id
    ).all()
    
    up_count = sum(1 for f in feedbacks if f.rating == 1)
    down_count = sum(1 for f in feedbacks if f.rating == -1)
    total = len(feedbacks)

    return FeedbackStatsResponse(
        total_feedback_count=total,
        thumbs_up_count=up_count,
        thumbs_down_count=down_count,
        ready_for_training=total >= 5,
        recommended_training_samples=max(0, 10 - total)
    )

@router.get("/export-dataset")
def export_feedback_dataset(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Exports feedback samples with full item embeddings for training."""
    feedbacks = db.query(OutfitFeedback).filter(
        OutfitFeedback.user_id == current_user.id
    ).all()
    
    dataset_records = []
    for fb in feedbacks:
        outfit = fb.outfit
        if not outfit:
            continue

        top = db.query(ClothingItem).filter(ClothingItem.id == outfit.top_id).first()
        bottom = db.query(ClothingItem).filter(ClothingItem.id == outfit.bottom_id).first()
        shoes = db.query(ClothingItem).filter(ClothingItem.id == outfit.footwear_id).first()

        if top and bottom and shoes:
            dataset_records.append({
                "feedback_id": fb.id,
                "label": 1 if fb.rating == 1 else 0,
                "top_id": top.id,
                "bottom_id": bottom.id,
                "footwear_id": shoes.id,
                "top_embedding": top.clip_embedding,
                "bottom_embedding": bottom.clip_embedding,
                "footwear_embedding": shoes.clip_embedding,
                "occasion": outfit.occasion,
                "created_at": str(fb.created_at)
            })

    return {
        "count": len(dataset_records),
        "records": dataset_records
    }
