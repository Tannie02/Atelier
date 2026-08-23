import itertools
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.clothing_item import ClothingItem
from app.models.outfit import OutfitRecommendation
from app.models.feedback import OutfitFeedback
from app.models.user import User
from app.schemas.outfit import (
    OutfitRecommendRequest, OutfitRecommendResponse, 
    RecommendedOutfit, OutfitItemDetail, OutfitScoreBreakdown, WeatherContext
)
from app.routes.auth import get_current_user
from app.ml.weather_service import get_current_weather_context
from app.ml.rules_engine import is_item_suitable_for_occasion, is_item_suitable_for_weather
from app.ml.compatibility import score_outfit_baseline
from app.ml.neural_scorer import neural_scorer

router = APIRouter(prefix="/api/recommend", tags=["Outfit Recommender"])

@router.post("/outfits", response_model=OutfitRecommendResponse)
def generate_recommendations(
    req: OutfitRecommendRequest, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generates intelligent, ranked outfit combinations from user's wardrobe based on:
    1. Occasion constraints (formality matching)
    2. Real-time Weather conditions (warmth level matching)
    3. Multi-item visual embedding compatibility (CLIP + Color Harmony)
    4. Neural Outfit Compatibility Model (if trained by user)
    """
    # 1. Fetch & parse weather
    weather_data = get_current_weather_context(
        city=req.city,
        lat=req.latitude,
        lon=req.longitude,
        manual_temp=req.manual_temp_celsius,
        manual_condition=req.manual_weather_condition
    )
    temp_c = weather_data["temperature_c"]

    # Handle direct python function calls without FastAPI dependency injection
    if not isinstance(current_user, User):
        from app.routes.auth import get_or_create_default_user
        current_user = get_or_create_default_user(db)

    # 2. Fetch all wardrobe items belonging to current user
    all_items = db.query(ClothingItem).filter(ClothingItem.user_id == current_user.id).all()
    
    if not all_items:
        raise HTTPException(
            status_code=400, 
            detail="Your digital closet is empty! Please upload some tops, bottoms, and footwear items first."
        )

    # 3. Categorize and filter items
    tops = []
    bottoms = []
    footwear = []
    outerwear = []

    for item in all_items:
        # Check occasion suitability
        occ_ok, occ_reason = is_item_suitable_for_occasion(item, req.occasion)
        if not occ_ok:
            continue

        # Check weather warmth suitability
        w_ok, w_penalty = is_item_suitable_for_weather(item, temp_c)
        if not w_ok:
            continue

        # Group by category
        if item.category == "top":
            tops.append((item, w_penalty))
        elif item.category == "bottom":
            bottoms.append((item, w_penalty))
        elif item.category == "footwear":
            footwear.append((item, w_penalty))
        elif item.category == "outerwear":
            outerwear.append((item, w_penalty))

    if not tops or not bottoms or not footwear:
        missing = []
        if not tops: missing.append("Tops")
        if not bottoms: missing.append("Bottoms")
        if not footwear: missing.append("Footwear")
        raise HTTPException(
            status_code=400,
            detail=f"Not enough matching items in your closet for {req.occasion} in {temp_c}°C weather. Missing suitable: {', '.join(missing)}. Try adjusting occasion or adding more items!"
        )

    # 4. Generate Candidate Combinations
    candidate_triplets = list(itertools.product(tops, bottoms, footwear))
    total_candidates = len(candidate_triplets)

    # Determine if outerwear should be included
    need_outerwear = req.include_outerwear or (temp_c < 16.0 and len(outerwear) > 0)
    has_neural_model = neural_scorer.is_trained_model_available()

    scored_outfits = []

    for (t, t_pen), (b, b_pen), (f, f_pen) in candidate_triplets:
        layer = None
        layer_pen = 1.0
        if need_outerwear and outerwear:
            layer, layer_pen = outerwear[0]

        # Calculate Baseline Cosine & Color Harmony
        compat_val, harmony_val, base_total, reasons = score_outfit_baseline(
            top=t,
            bottom=b,
            footwear=f,
            outerwear=layer,
            weather_temp=temp_c
        )

        # Apply weather penalties
        if layer:
            combined_weather_penalty = (t_pen + b_pen + f_pen + layer_pen) / 4.0
        else:
            combined_weather_penalty = (t_pen + b_pen + f_pen) / 3.0
            
        adjusted_base_score = min(base_total * combined_weather_penalty, 99.9)

        # Evaluate Neural Model if available
        neural_val = None
        if has_neural_model:
            neural_val = neural_scorer.score_outfit(top=t, bottom=b, footwear=f)
            if neural_val is not None:
                final_score = round(min(((neural_val * 0.70) + (harmony_val * 0.30)) * combined_weather_penalty, 99.9), 1)
                model_used = "Personalized AI Stylist"
            else:
                final_score = round(adjusted_base_score, 1)
                model_used = "Curated Style Match"
        else:
            final_score = round(adjusted_base_score, 1)
            model_used = "Curated Style Match"

        scored_outfits.append({
            "top": t,
            "bottom": b,
            "footwear": f,
            "outerwear": layer,
            "compat_score": compat_val,
            "color_score": harmony_val,
            "neural_score": neural_val,
            "final_score": final_score,
            "model_used": model_used,
            "reasons": reasons
        })

    # Sort descending by final score
    scored_outfits.sort(key=lambda x: x["final_score"], reverse=True)
    top_outfits = scored_outfits[:req.top_n]

    # Save recommendations to database for feedback tracking
    response_list = []
    for item in top_outfits:
        rec_record = OutfitRecommendation(
            user_id=current_user.id,
            top_id=item["top"].id,
            bottom_id=item["bottom"].id,
            footwear_id=item["footwear"].id,
            outerwear_id=item["outerwear"].id if item["outerwear"] else None,
            occasion=req.occasion,
            weather_temp=temp_c,
            weather_condition=weather_data["weather_condition"],
            city_name=weather_data["city"],
            compatibility_score=item["compat_score"],
            color_harmony_score=item["color_score"],
            neural_score=item["neural_score"],
            total_score=item["final_score"],
            match_reason="; ".join(item["reasons"])
        )
        db.add(rec_record)
        db.commit()
        db.refresh(rec_record)

        existing_fb = db.query(OutfitFeedback).filter(
            OutfitFeedback.outfit_id == rec_record.id,
            OutfitFeedback.user_id == current_user.id
        ).first()
        rating_val = existing_fb.rating if existing_fb else None

        response_list.append(RecommendedOutfit(
            recommendation_id=rec_record.id,
            top=OutfitItemDetail(
                id=item["top"].id,
                image_url=f"/uploads/{item['top'].image_path}",
                category=item["top"].category,
                subcategory=item["top"].subcategory,
                dominant_color_name=item["top"].dominant_color_name,
                dominant_color_hex=item["top"].dominant_color_hex,
                warmth_level=item["top"].warmth_level,
                formality_level=item["top"].formality_level
            ),
            bottom=OutfitItemDetail(
                id=item["bottom"].id,
                image_url=f"/uploads/{item['bottom'].image_path}",
                category=item["bottom"].category,
                subcategory=item["bottom"].subcategory,
                dominant_color_name=item["bottom"].dominant_color_name,
                dominant_color_hex=item["bottom"].dominant_color_hex,
                warmth_level=item["bottom"].warmth_level,
                formality_level=item["bottom"].formality_level
            ),
            footwear=OutfitItemDetail(
                id=item["footwear"].id,
                image_url=f"/uploads/{item['footwear'].image_path}",
                category=item["footwear"].category,
                subcategory=item["footwear"].subcategory,
                dominant_color_name=item["footwear"].dominant_color_name,
                dominant_color_hex=item["footwear"].dominant_color_hex,
                warmth_level=item["footwear"].warmth_level,
                formality_level=item["footwear"].formality_level
            ),
            outerwear=OutfitItemDetail(
                id=item["outerwear"].id,
                image_url=f"/uploads/{item['outerwear'].image_path}",
                category=item["outerwear"].category,
                subcategory=item["outerwear"].subcategory,
                dominant_color_name=item["outerwear"].dominant_color_name,
                dominant_color_hex=item["outerwear"].dominant_color_hex,
                warmth_level=item["outerwear"].warmth_level,
                formality_level=item["outerwear"].formality_level
            ) if item["outerwear"] else None,
            scores=OutfitScoreBreakdown(
                compatibility_score=item["compat_score"],
                color_harmony_score=item["color_score"],
                neural_score=item["neural_score"],
                total_score=item["final_score"],
                scoring_model_used=item["model_used"]
            ),
            match_reasons=item["reasons"],
            user_rating=rating_val
        ))

    return OutfitRecommendResponse(
        occasion=req.occasion,
        weather=WeatherContext(**weather_data),
        total_candidates_evaluated=total_candidates,
        outfits=response_list
    )
