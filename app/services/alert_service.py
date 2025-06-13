import logging
from typing import List, Dict, Any, Optional

from app.core.entities import Alert, Profile
from app.core.interfaces import AlertRepository, ProfileRepository
from app.core.exceptions import AlertNotFoundError, ProfileNotFoundError

logger = logging.getLogger(__name__)


class AlertServiceImpl:
    def __init__(
        self,
        alert_repository: AlertRepository,
        profile_repository: ProfileRepository
    ):
        self.alert_repository = alert_repository
        self.profile_repository = profile_repository

    async def create_alert(self, profile_username: str, user_id: int, threshold: int) -> Alert:
        """Create a new alert for a profile"""
        # Validate profile ownership
        profile = await self.profile_repository.get_by_username_and_user_id(profile_username, user_id)
        if not profile:
            raise ProfileNotFoundError(f"Profile {profile_username} not found")
        
        # Validate threshold limits
        if not await self.validate_threshold_limit(profile_username, user_id, threshold):
            raise ValueError("Alert limit exceeded or invalid threshold")
        
        # Create alert
        alert = Alert(
            profile_id=profile.id,
            threshold=threshold,
            is_active=True
        )
        
        created_alert = await self.alert_repository.create(alert)
        logger.info(f"Created alert for profile {profile_username} with threshold {threshold}")
        return created_alert

    async def get_profile_alerts(self, profile_username: str, user_id: int) -> List[Alert]:
        """Get all alerts for a profile"""
        # Validate profile ownership
        profile = await self.profile_repository.get_by_username_and_user_id(profile_username, user_id)
        if not profile:
            raise ProfileNotFoundError(f"Profile {profile_username} not found")
        
        # Get all alerts for this profile (both active and triggered)
        alerts = await self.alert_repository.get_all_by_profile_id(profile.id)
        return alerts

    async def update_alert(self, alert_id: int, user_id: int, updates: Dict[str, Any]) -> Alert:
        """Update an existing alert"""
        # Validate alert ownership
        alert = await self.validate_alert_ownership(alert_id, user_id)
        
        # Update alert fields
        if 'threshold' in updates:
            alert.threshold = updates['threshold']
        if 'is_active' in updates:
            alert.is_active = updates['is_active']
        
        updated_alert = await self.alert_repository.update(alert)
        logger.info(f"Updated alert {alert_id}")
        return updated_alert

    async def delete_alert(self, alert_id: int, user_id: int) -> bool:
        """Delete an alert"""
        # Validate alert ownership
        await self.validate_alert_ownership(alert_id, user_id)
        
        # Delete alert
        success = await self.alert_repository.delete(alert_id)
        if success:
            logger.info(f"Deleted alert {alert_id}")
        return success

    async def get_alert(self, alert_id: int, user_id: int) -> Alert:
        """Get a specific alert"""
        return await self.validate_alert_ownership(alert_id, user_id)

    async def validate_alert_ownership(self, alert_id: int, user_id: int) -> Alert:
        """Validate that user owns the alert"""
        alert = await self.alert_repository.get_by_id(alert_id)
        if not alert:
            raise AlertNotFoundError(f"Alert {alert_id} not found")
        
        # Get profile to check ownership
        profile = await self.profile_repository.get_by_id(alert.profile_id)
        if not profile or profile.user_id != user_id:
            raise AlertNotFoundError(f"Alert {alert_id} not found")
        
        return alert

    async def validate_threshold_limit(self, profile_username: str, user_id: int, threshold: int) -> bool:
        """Validate threshold and alert limits"""
        # Threshold validation
        if threshold < 10:
            logger.warning(f"Threshold too low: {threshold}")
            return False
        if threshold > 10_000_000:
            logger.warning(f"Threshold too high: {threshold}")
            return False
        
        # Get profile
        profile = await self.profile_repository.get_by_username_and_user_id(profile_username, user_id)
        if not profile:
            return False
        
        # Check alert count limit (max 5 per profile)
        existing_alerts = await self.alert_repository.get_active_by_profile_id(profile.id)
        if len(existing_alerts) >= 5:
            logger.warning(f"Alert limit exceeded for profile {profile_username}")
            return False
        
        return True
