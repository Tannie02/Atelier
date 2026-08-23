from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class FeedbackCreate(BaseModel):
    outfit_id: int
    rating: int = Field(..., description="1 for Thumbs Up, -1 for Thumbs Down")
    feedback_reason: Optional[str] = ""

class FeedbackResponse(BaseModel):
    id: int
    outfit_id: int
    rating: int
    feedback_reason: str
    created_at: datetime
    message: str

class FeedbackStatsResponse(BaseModel):
    total_feedback_count: int
    thumbs_up_count: int
    thumbs_down_count: int
    ready_for_training: bool
    recommended_training_samples: int
