import json
import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class ClothingItem(Base):
    __tablename__ = "clothing_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    image_path = Column(String(255), nullable=False)
    
    # Classification
    category = Column(String(50), nullable=False, index=True)  # top, bottom, footwear, outerwear
    subcategory = Column(String(50), nullable=False, index=True)  # e.g., t-shirt, jeans, blazer
    
    # Visual Attributes
    dominant_color_name = Column(String(50), nullable=False)  # e.g., Navy Blue, Beige
    dominant_color_hex = Column(String(10), nullable=False)   # e.g., #000080
    color_palette_json = Column(Text, default="[]")           # Secondary colors list
    
    # Practical Attributes
    warmth_level = Column(Integer, default=2)     # 1 (Light/Summer) to 5 (Heavy/Winter)
    formality_level = Column(Integer, default=2)  # 1 (Loungewear) to 5 (Black-tie / Formal)
    occasion_tags_json = Column(Text, default="[]")  # e.g., ["college", "casual_outing"]
    
    # ML Embedding (512-dim normalized CLIP vector as JSON list of floats)
    clip_embedding_json = Column(Text, nullable=True)
    
    # Metadata & Custom notes
    notes = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="clothing_items")

    @property
    def clip_embedding(self) -> list[float]:
        if self.clip_embedding_json:
            try:
                return json.loads(self.clip_embedding_json)
            except Exception:
                return []
        return []

    @clip_embedding.setter
    def clip_embedding(self, embedding_list: list[float]):
        self.clip_embedding_json = json.dumps(embedding_list)

    @property
    def color_palette(self) -> list[dict]:
        if self.color_palette_json:
            try:
                return json.loads(self.color_palette_json)
            except Exception:
                return []
        return []

    @property
    def occasion_tags(self) -> list[str]:
        if self.occasion_tags_json:
            try:
                return json.loads(self.occasion_tags_json)
            except Exception:
                return []
        return []
