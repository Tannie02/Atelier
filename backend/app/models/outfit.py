import json
import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class OutfitRecommendation(Base):
    __tablename__ = "outfit_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # Items in outfit
    top_id = Column(Integer, ForeignKey("clothing_items.id"), nullable=False)
    bottom_id = Column(Integer, ForeignKey("clothing_items.id"), nullable=False)
    footwear_id = Column(Integer, ForeignKey("clothing_items.id"), nullable=False)
    outerwear_id = Column(Integer, ForeignKey("clothing_items.id"), nullable=True)
    
    # Context
    occasion = Column(String(50), nullable=False)
    weather_temp = Column(Float, nullable=True)
    weather_condition = Column(String(100), nullable=True)
    city_name = Column(String(100), nullable=True)
    
    # Scores
    compatibility_score = Column(Float, default=0.0)
    color_harmony_score = Column(Float, default=0.0)
    neural_score = Column(Float, nullable=True)
    total_score = Column(Float, default=0.0)
    
    # Explanation
    match_reason = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="outfit_recommendations")
    top = relationship("ClothingItem", foreign_keys=[top_id])
    bottom = relationship("ClothingItem", foreign_keys=[bottom_id])
    footwear = relationship("ClothingItem", foreign_keys=[footwear_id])
    outerwear = relationship("ClothingItem", foreign_keys=[outerwear_id])
    feedback = relationship("OutfitFeedback", back_populates="outfit", cascade="all, delete-orphan")
