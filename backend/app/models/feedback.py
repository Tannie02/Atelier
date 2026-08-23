import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class OutfitFeedback(Base):
    __tablename__ = "outfit_feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    outfit_id = Column(Integer, ForeignKey("outfit_recommendations.id"), nullable=False)
    
    # 1 for Thumbs Up (Like), -1 for Thumbs Down (Dislike)
    rating = Column(Integer, nullable=False)
    
    # Optional comment / reason
    feedback_reason = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="feedbacks")
    outfit = relationship("OutfitRecommendation", back_populates="feedback")
