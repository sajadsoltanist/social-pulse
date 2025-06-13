from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List

from app.api.schemas.analytics import (
    TopChangesResponse,
    UserDashboard,
    ProfileGrowthInsight,
    ProfileHistoryResponse,
    ProfileChangeAnalysis,
    ProfileComparisonResponse,
    ProfileComparisonItem
)
from app.services.analytics_service import AnalyticsServiceImpl
from app.api.deps import get_current_user, get_analytics_service
from app.core.entities import User
from app.core.exceptions import ProfileNotFoundError

router = APIRouter(prefix="/insights", tags=["analytics"])


@router.get("/my-top-changes", response_model=TopChangesResponse)
async def get_my_top_changes(
    period: str = Query("24h", regex="^(24h|7d|30d)$", description="Time period: 24h, 7d, or 30d"),
    current_user: User = Depends(get_current_user),
    analytics_service: AnalyticsServiceImpl = Depends(get_analytics_service)
):
    """Get top follower count changes for user's profiles within specified period"""
    try:
        # Map period string to hours
        period_mapping = {
            "24h": 24,
            "7d": 168,  # 7 * 24
            "30d": 720  # 30 * 24
        }
        
        period_hours = period_mapping[period]
        result = await analytics_service.get_user_top_changes(current_user.id, period_hours)
        
        return TopChangesResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving top changes: {str(e)}"
        )


@router.get("/dashboard", response_model=UserDashboard)
async def get_user_dashboard(
    current_user: User = Depends(get_current_user),
    analytics_service: AnalyticsServiceImpl = Depends(get_analytics_service)
):
    """Get comprehensive dashboard analytics for current user"""
    try:
        result = await analytics_service.get_user_dashboard(current_user.id)
        return UserDashboard(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving dashboard: {str(e)}"
        )


@router.get("/profiles/{username}/growth", response_model=ProfileGrowthInsight)
async def get_profile_growth(
    username: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze (1-365)"),
    current_user: User = Depends(get_current_user),
    analytics_service: AnalyticsServiceImpl = Depends(get_analytics_service)
):
    """Get detailed growth analysis for a specific profile"""
    try:
        result = await analytics_service.get_profile_growth_analysis(
            username, current_user.id, days
        )
        return ProfileGrowthInsight(**result)
        
    except ProfileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile '{username}' not found or not owned by user"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving growth analysis: {str(e)}"
        )


@router.get("/profiles/{username}/history", response_model=ProfileHistoryResponse)
async def get_profile_history(
    username: str,
    days: int = Query(30, ge=1, le=365, description="Number of days of history (1-365)"),
    current_user: User = Depends(get_current_user),
    analytics_service: AnalyticsServiceImpl = Depends(get_analytics_service)
):
    """Get historical follower data for a specific profile"""
    try:
        result = await analytics_service.get_profile_insights(
            username, current_user.id, days
        )
        return ProfileHistoryResponse(**result)
        
    except ProfileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile '{username}' not found or not owned by user"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving profile history: {str(e)}"
        )


@router.get("/profiles/compare", response_model=ProfileComparisonResponse)
async def compare_profiles(
    period: str = Query("7d", regex="^(24h|7d|30d)$", description="Comparison period: 24h, 7d, or 30d"),
    current_user: User = Depends(get_current_user),
    analytics_service: AnalyticsServiceImpl = Depends(get_analytics_service)
):
    """Compare all user's profiles by growth in specified period"""
    try:
        # Map period string to hours
        period_mapping = {
            "24h": 24,
            "7d": 168,
            "30d": 720
        }
        
        period_hours = period_mapping[period]
        top_changes = await analytics_service.get_user_top_changes(current_user.id, period_hours)
        
        # Combine all profiles and rank them
        all_profiles = []
        all_profiles.extend(top_changes["increases"])
        all_profiles.extend(top_changes["decreases"])
        all_profiles.extend(top_changes["no_changes"])
        
        # Sort by absolute change (descending)
        all_profiles.sort(key=lambda x: x["absolute_change"], reverse=True)
        
        # Create comparison items with rankings
        comparison_items = []
        for rank, profile in enumerate(all_profiles, 1):
            comparison_items.append(ProfileComparisonItem(
                username=profile["username"],
                current_followers=profile["current_followers"],
                change=profile["absolute_change"],
                percentage_change=profile["percentage_change"],
                rank=rank
            ))
        
        return ProfileComparisonResponse(
            period=period,
            profiles=comparison_items,
            total_profiles=len(comparison_items)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error comparing profiles: {str(e)}"
        )


@router.get("/profiles/{username}/summary")
async def get_profile_summary(
    username: str,
    current_user: User = Depends(get_current_user),
    analytics_service: AnalyticsServiceImpl = Depends(get_analytics_service)
):
    """Get quick summary of profile performance across multiple time periods"""
    try:
        # Get data for multiple periods
        growth_30d = await analytics_service.get_profile_growth_analysis(
            username, current_user.id, 30
        )
        growth_7d = await analytics_service.get_profile_growth_analysis(
            username, current_user.id, 7
        )
        
        # Get recent changes
        top_changes_24h = await analytics_service.get_user_top_changes(current_user.id, 24)
        
        # Find this profile in 24h changes
        profile_24h_change = None
        for profile_list in [top_changes_24h["increases"], top_changes_24h["decreases"], top_changes_24h["no_changes"]]:
            for profile in profile_list:
                if profile["username"] == username:
                    profile_24h_change = profile
                    break
            if profile_24h_change:
                break
        
        return {
            "username": username,
            "current_followers": growth_30d["current_followers"],
            "changes": {
                "24h": profile_24h_change["absolute_change"] if profile_24h_change else 0,
                "7d": growth_7d["total_change"],
                "30d": growth_30d["total_change"]
            },
            "percentage_changes": {
                "24h": profile_24h_change["percentage_change"] if profile_24h_change else 0.0,
                "7d": growth_7d["percentage_change"],
                "30d": growth_30d["percentage_change"]
            },
            "growth_metrics": {
                "average_daily_growth_30d": growth_30d["average_daily_growth"],
                "peak_followers": growth_30d["peak_followers"],
                "peak_date": growth_30d["peak_date"],
                "data_points_30d": growth_30d["data_points"]
            }
        }
        
    except ProfileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile '{username}' not found or not owned by user"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving profile summary: {str(e)}"
        )
