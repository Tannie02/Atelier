from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.schemas.wardrobe import ClothingItemResponse

class OutfitRecommendRequest(BaseModel):
    occasion: str = "college"
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    manual_temp_celsius: Optional[float] = None
    manual_weather_condition: Optional[str] = None
    top_n: int = 5
    include_outerwear: Optional[bool] = None

class WeatherContext(BaseModel):
    city: str
    temperature_c: float
    humidity_percent: float
    precipitation_mm: float
    weather_condition: str
    weather_icon: str
    warmth_recommendation: str

class OutfitScoreBreakdown(BaseModel):
    compatibility_score: float
    color_harmony_score: float
    neural_score: Optional[float] = None
    total_score: float
    scoring_model_used: str  # "Neural Scorer (Trained)" or "CLIP Cosine Base"

class OutfitItemDetail(BaseModel):
    id: int
    image_url: str
    category: str
    subcategory: str
    dominant_color_name: str
    dominant_color_hex: str
    warmth_level: int
    formality_level: int

class RecommendedOutfit(BaseModel):
    recommendation_id: Optional[int] = None
    top: OutfitItemDetail
    bottom: OutfitItemDetail
    footwear: OutfitItemDetail
    outerwear: Optional[OutfitItemDetail] = None
    scores: OutfitScoreBreakdown
    match_reasons: list[str]
    user_rating: Optional[int] = None  # 1 for liked, -1 for disliked

class OutfitRecommendResponse(BaseModel):
    occasion: str
    weather: Optional[WeatherContext] = None
    total_candidates_evaluated: int
    outfits: list[RecommendedOutfit]
