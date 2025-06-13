from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks

from app.api.deps import get_monitoring_service, get_current_user
from app.services.monitoring_service import MonitoringServiceImpl
from app.core.entities import User
from app.infrastructure.background_tasks import check_profile_followers, monitor_all_profiles

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.post("/check-all", response_model=Dict[str, Any])
async def check_all_profiles(
    current_user: User = Depends(get_current_user),
    monitoring_service: MonitoringServiceImpl = Depends(get_monitoring_service)
):
    """Manually trigger monitoring for all active profiles"""
    try:
        results = await monitoring_service.run_monitoring_cycle()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Monitoring failed: {str(e)}")


@router.post("/check-profile/{username}", response_model=Dict[str, Any])
async def check_profile_by_username(
    username: str,
    current_user: User = Depends(get_current_user),
    monitoring_service: MonitoringServiceImpl = Depends(get_monitoring_service)
):
    """Manually check a specific profile by username"""
    try:
        # Verify profile ownership using username
        profile = await monitoring_service.get_profile_by_username_and_user(username, current_user.id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        result = await monitoring_service.check_single_profile(profile.id)
        
        if result:
            # Process alerts
            alerts = await monitoring_service.process_alerts(profile.id, result.followers_count)
            return {
                "username": profile.username,
                "follower_count": result.followers_count,
                "alerts_triggered": len(alerts),
                "status": "updated"
            }
        else:
            return {
                "username": profile.username,
                "status": "no_change"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Profile check failed: {str(e)}")


@router.get("/status/{username}", response_model=Dict[str, Any])
async def get_profile_status_by_username(
    username: str,
    current_user: User = Depends(get_current_user),
    monitoring_service: MonitoringServiceImpl = Depends(get_monitoring_service)
):
    """Get monitoring status for a specific profile by username"""
    try:
        # Verify profile ownership using username
        profile = await monitoring_service.get_profile_by_username_and_user(username, current_user.id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        status = await monitoring_service.get_profile_monitoring_status(profile.id)
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.post("/background/check-all")
async def trigger_background_monitoring(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Trigger background monitoring task"""
    task = monitor_all_profiles.delay()
    return {
        "message": "Background monitoring task started",
        "task_id": task.id
    }


@router.post("/background/check-profile/{username}")
async def trigger_background_profile_check_by_username(
    username: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    monitoring_service: MonitoringServiceImpl = Depends(get_monitoring_service)
):
    """Trigger background check for specific profile by username"""
    try:
        # Verify profile ownership using username
        profile = await monitoring_service.get_profile_by_username_and_user(username, current_user.id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        task = check_profile_followers.delay(profile.id)
        return {
            "message": f"Background check started for profile {profile.username}",
            "task_id": task.id,
            "username": profile.username
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start background task: {str(e)}")


@router.get("/my-profiles", response_model=Dict[str, Any])
async def get_my_monitored_profiles(
    current_user: User = Depends(get_current_user),
    monitoring_service: MonitoringServiceImpl = Depends(get_monitoring_service)
):
    """Get all user's profiles with monitoring status"""
    try:
        # Get all user's profiles
        user_profiles = await monitoring_service.profile_repository.get_by_user_id(current_user.id)
        
        profiles_with_status = []
        for profile in user_profiles:
            # Get monitoring status for each profile
            status = await monitoring_service.get_profile_monitoring_status(profile.id)
            
            profile_info = {
                "username": profile.username,
                "display_name": profile.display_name,
                "is_active": profile.is_active,
                "last_checked": profile.last_checked.isoformat() if profile.last_checked else None,
                "created_at": profile.created_at.isoformat(),
                "monitoring_status": status
            }
            profiles_with_status.append(profile_info)
        
        return {
            "total_profiles": len(profiles_with_status),
            "active_profiles": len([p for p in profiles_with_status if p["is_active"]]),
            "profiles": profiles_with_status
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get profiles: {str(e)}")


@router.get("/health")
async def monitoring_health():
    """Health check for monitoring system"""
    return {
        "status": "healthy",
        "service": "monitoring",
        "timestamp": "2024-01-01T00:00:00Z"
    } 