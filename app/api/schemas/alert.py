from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class AlertCreate(BaseModel):
    threshold: int = Field(..., gt=0, description="Follower count threshold")


class AlertUpdate(BaseModel):
    threshold: Optional[int] = Field(None, gt=0)
    is_active: Optional[bool] = None


class AlertResponse(BaseModel):
    id: int
    threshold: int
    is_active: bool
    triggered_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AlertListResponse(BaseModel):
    alerts: List[AlertResponse]
    profile_username: str
    total: int
