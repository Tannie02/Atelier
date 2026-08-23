import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(120), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    salt = Column(String(64), nullable=False)
    
    # Optional styling preferences / bio
    style_preference = Column(String(100), default="Minimalist Chic")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    clothing_items = relationship("ClothingItem", back_populates="user", cascade="all, delete-orphan")
    outfit_recommendations = relationship("OutfitRecommendation", back_populates="user", cascade="all, delete-orphan")
    feedbacks = relationship("OutfitFeedback", back_populates="user", cascade="all, delete-orphan")
