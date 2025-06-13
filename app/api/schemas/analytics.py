from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ProfileChangeAnalysis(BaseModel):
    username: str
    current_followers: int
    previous_followers: int
    absolute_change: int
    percentage_change: float
    change_type: str = Field(..., description="increase | decrease | no_change")
    last_updated: datetime


class TopChangesResponse(BaseModel):
    period: str = Field(..., description="24h, 7d, or 30d")
    total_profiles: int
    increases: List[ProfileChangeAnalysis]
    decreases: List[ProfileChangeAnalysis]
    no_changes: List[ProfileChangeAnalysis]


class ProfileGrowthInsight(BaseModel):
    username: str
    current_followers: int
    period_start_followers: int
    total_change: int
    percentage_change: float
    average_daily_growth: float
    peak_followers: int
    peak_date: datetime
    low_followers: int
    low_date: datetime
    data_points: int


class UserDashboard(BaseModel):
    total_profiles: int
    total_followers: int
    total_growth_24h: int
    total_growth_7d: int
    best_performer: Optional[ProfileChangeAnalysis]
    worst_performer: Optional[ProfileChangeAnalysis]
    last_updated: datetime


class HistoricalData(BaseModel):
    date: datetime
    followers: int
    daily_change: Optional[int]


class ProfileHistoryResponse(BaseModel):
    username: str
    period_days: int
    current_followers: int
    total_change: int
    data: List[HistoricalData]


class ProfileComparisonItem(BaseModel):
    username: str
    current_followers: int
    change: int
    percentage_change: float
    rank: int


class ProfileComparisonResponse(BaseModel):
    period: str
    profiles: List[ProfileComparisonItem]
    total_profiles: int
