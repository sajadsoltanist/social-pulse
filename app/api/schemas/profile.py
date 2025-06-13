from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ProfileCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=30, pattern=r'^[a-zA-Z0-9._]+$')
    display_name: Optional[str] = Field(None, max_length=100)


class ProfileUpdate(BaseModel):
    display_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class ProfileResponse(BaseModel):
    username: str
    display_name: Optional[str]
    is_active: bool
    last_checked: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ProfileListResponse(BaseModel):
    profiles: List[ProfileResponse]
    total: int
