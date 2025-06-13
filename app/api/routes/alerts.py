from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.entities import User
from app.core.exceptions import AlertNotFoundError, ProfileNotFoundError
from app.api.deps import get_current_user, get_alert_service
from app.api.schemas.alert import AlertCreate, AlertUpdate, AlertResponse, AlertListResponse
from app.services.alert_service import AlertServiceImpl

router = APIRouter()


@router.get("/profiles/{username}/alerts", response_model=AlertListResponse)
async def get_profile_alerts(
    username: str,
    current_user: User = Depends(get_current_user),
    alert_service: AlertServiceImpl = Depends(get_alert_service)
):
    """Get all alerts for a specific profile"""
    try:
        alerts = await alert_service.get_profile_alerts(username, current_user.id)
        
        alert_responses = [
            AlertResponse(
                id=alert.id,
                threshold=alert.threshold,
                is_active=alert.is_active,
                triggered_at=alert.triggered_at,
                created_at=alert.created_at
            )
            for alert in alerts
        ]
        
        return AlertListResponse(
            alerts=alert_responses,
            profile_username=username,
            total=len(alert_responses)
        )
        
    except ProfileNotFoundError:
        raise HTTPException(status_code=404, detail="Profile not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")


@router.post("/profiles/{username}/alerts", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    username: str,
    alert_data: AlertCreate,
    current_user: User = Depends(get_current_user),
    alert_service: AlertServiceImpl = Depends(get_alert_service)
):
    """Create a new alert for a profile"""
    try:
        alert = await alert_service.create_alert(username, current_user.id, alert_data.threshold)
        
        return AlertResponse(
            id=alert.id,
            threshold=alert.threshold,
            is_active=alert.is_active,
            triggered_at=alert.triggered_at,
            created_at=alert.created_at
        )
        
    except ProfileNotFoundError:
        raise HTTPException(status_code=404, detail="Profile not found")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create alert: {str(e)}")


@router.get("/alerts/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    alert_service: AlertServiceImpl = Depends(get_alert_service)
):
    """Get a specific alert"""
    try:
        alert = await alert_service.get_alert(alert_id, current_user.id)
        
        return AlertResponse(
            id=alert.id,
            threshold=alert.threshold,
            is_active=alert.is_active,
            triggered_at=alert.triggered_at,
            created_at=alert.created_at
        )
        
    except AlertNotFoundError:
        raise HTTPException(status_code=404, detail="Alert not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alert: {str(e)}")


@router.put("/alerts/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: int,
    alert_data: AlertUpdate,
    current_user: User = Depends(get_current_user),
    alert_service: AlertServiceImpl = Depends(get_alert_service)
):
    """Update an existing alert"""
    try:
        updates = {}
        if alert_data.threshold is not None:
            updates['threshold'] = alert_data.threshold
        if alert_data.is_active is not None:
            updates['is_active'] = alert_data.is_active
        
        alert = await alert_service.update_alert(alert_id, current_user.id, updates)
        
        return AlertResponse(
            id=alert.id,
            threshold=alert.threshold,
            is_active=alert.is_active,
            triggered_at=alert.triggered_at,
            created_at=alert.created_at
        )
        
    except AlertNotFoundError:
        raise HTTPException(status_code=404, detail="Alert not found")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update alert: {str(e)}")


@router.delete("/alerts/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    alert_service: AlertServiceImpl = Depends(get_alert_service)
):
    """Delete an alert"""
    try:
        success = await alert_service.delete_alert(alert_id, current_user.id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete alert")
        
    except AlertNotFoundError:
        raise HTTPException(status_code=404, detail="Alert not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete alert: {str(e)}")
