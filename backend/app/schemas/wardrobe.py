from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ColorInfo(BaseModel):
    name: str
    hex: str
    percentage: float = 0.0

class AutoTagPreviewResponse(BaseModel):
    temp_image_url: str
    suggested_category: str
    suggested_subcategory: str
    top_candidate_tags: list[dict]
    dominant_color_name: str
    dominant_color_hex: str
    color_palette: list[ColorInfo]
    suggested_warmth: int
    suggested_formality: int
    suggested_occasions: list[str]

class ClothingItemCreate(BaseModel):
    image_filename: str
    category: str
    subcategory: str
    dominant_color_name: str
    dominant_color_hex: str
    color_palette: list[ColorInfo] = []
    warmth_level: int = Field(default=2, ge=1, le=5)
    formality_level: int = Field(default=2, ge=1, le=5)
    occasion_tags: list[str] = []
    notes: Optional[str] = ""

class ClothingItemUpdate(BaseModel):
    category: Optional[str] = None
    subcategory: Optional[str] = None
    dominant_color_name: Optional[str] = None
    dominant_color_hex: Optional[str] = None
    warmth_level: Optional[int] = Field(default=None, ge=1, le=5)
    formality_level: Optional[int] = Field(default=None, ge=1, le=5)
    occasion_tags: Optional[list[str]] = None
    notes: Optional[str] = None

class ClothingItemResponse(BaseModel):
    id: int
    image_url: str
    category: str
    subcategory: str
    dominant_color_name: str
    dominant_color_hex: str
    color_palette: list[ColorInfo] = []
    warmth_level: int
    formality_level: int
    occasion_tags: list[str] = []
    notes: str = ""
    created_at: datetime

    class Config:
        from_attributes = True
