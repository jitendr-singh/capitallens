from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class SavingsGoalCreate(BaseModel):
    title: str
    target_amount: float
    saved_amount: Optional[float] = 0.0
    monthly_contribution: Optional[float] = 0.0
    deadline: Optional[datetime] = None
    icon: Optional[str] = "🎯"

class SavingsGoalUpdate(BaseModel):
    title: Optional[str] = None
    target_amount: Optional[float] = None
    saved_amount: Optional[float] = None
    monthly_contribution: Optional[float] = None
    deadline: Optional[datetime] = None
    icon: Optional[str] = None
    is_completed: Optional[bool] = None

class SavingsGoalResponse(BaseModel):
    id: int
    user_id: int
    title: str
    target_amount: float
    saved_amount: float
    monthly_contribution: float
    deadline: Optional[datetime]
    icon: str
    is_completed: bool
    progress_percentage: Optional[float] = None
    months_remaining: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True