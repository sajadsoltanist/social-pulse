import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.core.entities import Profile, FollowerRecord, Alert
from app.core.interfaces import (
    UserRepository,
    ProfileRepository, 
    FollowerRepository, 
    AlertRepository, 
    InstagramService,
    TelegramService
)
from app.core.exceptions import InstagramServiceError

logger = logging.getLogger(__name__)


class MonitoringServiceImpl:
    def __init__(
        self,
        user_repository: UserRepository,
        profile_repository: ProfileRepository,
        follower_repository: FollowerRepository,
        alert_repository: AlertRepository,
        instagram_service: InstagramService,
        telegram_service: Optional[TelegramService] = None
    ):
        self.user_repository = user_repository
        self.profile_repository = profile_repository
        self.follower_repository = follower_repository
        self.alert_repository = alert_repository
        self.instagram_service = instagram_service
        self.telegram_service = telegram_service

    async def get_profile_by_username_and_user(self, username: str, user_id: int) -> Optional[Profile]:
        """Helper method for username-based profile lookup with ownership validation"""
        return await self.profile_repository.get_by_username_and_user_id(username, user_id)

    async def check_all_profiles(self) -> Dict[str, Any]:
        """Check all active profiles for follower count changes"""
        results = {
            "checked": 0,
            "updated": 0,
            "errors": 0,
            "alerts_triggered": 0,
            "profiles": []
        }
        
        try:
            # Get all active profiles
            active_profiles = await self.profile_repository.get_all_active()
            logger.info(f"Found {len(active_profiles)} active profiles to check")
            
            for profile in active_profiles:
                try:
                    result = await self.check_single_profile(profile.id)
                    results["checked"] += 1
                    
                    profile_result = {
                        "username": profile.username,
                        "status": "success"
                    }
                    
                    # Always check for alerts, regardless of whether follower count changed
                    current_count = await self.instagram_service.get_follower_count(profile.username)
                    if current_count is not None:
                        triggered_alerts = await self.process_alerts(profile.id, current_count)
                        if triggered_alerts:
                            results["alerts_triggered"] += len(triggered_alerts)
                            profile_result["alerts_triggered"] = len(triggered_alerts)
                    
                    if result:
                        results["updated"] += 1
                        profile_result["follower_count"] = result.followers_count
                        profile_result["previous_count"] = await self._get_previous_count(profile.id)
                    
                    results["profiles"].append(profile_result)
                    
                    # Update last checked timestamp
                    await self.profile_repository.update_last_checked(profile.id)
                    
                except Exception as e:
                    logger.error(f"Error checking profile {profile.username}: {e}")
                    results["errors"] += 1
                    results["profiles"].append({
                        "username": profile.username,
                        "status": "error",
                        "error": str(e)
                    })
            
            logger.info(f"Monitoring cycle completed: {results['checked']} checked, "
                       f"{results['updated']} updated, {results['errors']} errors, "
                       f"{results['alerts_triggered']} alerts triggered")
            
        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}")
            results["error"] = str(e)
        
        return results

    async def check_single_profile(self, profile_id: int) -> Optional[FollowerRecord]:
        """Check a single profile for follower count changes"""
        try:
            # Get profile
            profile = await self.profile_repository.get_by_id(profile_id)
            if not profile:
                logger.error(f"Profile {profile_id} not found")
                return None
            
            # Get current follower count from Instagram
            current_count = await self.instagram_service.get_follower_count(profile.username)
            if current_count is None:
                logger.warning(f"Could not get follower count for {profile.username}")
                return None
            
            # Get latest stored record
            latest_record = await self.follower_repository.get_latest(profile_id)
            
            # Only create new record if count changed or no previous record
            if not latest_record or latest_record.followers_count != current_count:
                new_record = FollowerRecord(
                    profile_id=profile_id,
                    followers_count=current_count
                )
                
                created_record = await self.follower_repository.create(new_record)
                logger.info(f"Updated follower count for {profile.username}: "
                           f"{latest_record.followers_count if latest_record else 'N/A'} -> {current_count}")
                return created_record
            
            logger.debug(f"No change in follower count for {profile.username}: {current_count}")
            return None
            
        except InstagramServiceError as e:
            logger.error(f"Instagram service error for profile {profile_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error checking profile {profile_id}: {e}")
            raise

    async def process_alerts(self, profile_id: int, current_count: int) -> List[Alert]:
        """Process alerts for a profile based on current follower count"""
        triggered_alerts = []
        
        try:
            # Get active alerts for this profile
            active_alerts = await self.alert_repository.get_active_by_profile_id(profile_id)
            
            for alert in active_alerts:
                if current_count >= alert.threshold:
                    # Mark alert as triggered
                    await self.alert_repository.mark_as_triggered(alert.id)
                    triggered_alerts.append(alert)
                    
                    logger.info(f"Alert triggered for profile {profile_id}: "
                               f"reached {current_count} followers (threshold: {alert.threshold})")
                    
                    # Send notification if Telegram service is available
                    if self.telegram_service:
                        try:
                            profile = await self.profile_repository.get_by_id(profile_id)
                            if profile:
                                await self._send_alert_notification(
                                    profile, alert, current_count
                                )
                            else:
                                logger.error(f"Profile {profile_id} not found for notification")
                        except Exception as e:
                            logger.error(f"Failed to send alert notification: {e}")
                    else:
                        logger.warning("Telegram service not available for notification")
            
        except Exception as e:
            logger.error(f"Error processing alerts for profile {profile_id}: {e}")
        
        return triggered_alerts

    async def run_monitoring_cycle(self) -> Dict[str, Any]:
        """Run a complete monitoring cycle"""
        start_time = datetime.utcnow()
        logger.info("Starting monitoring cycle")
        
        try:
            results = await self.check_all_profiles()
            results["start_time"] = start_time.isoformat()
            results["end_time"] = datetime.utcnow().isoformat()
            results["duration_seconds"] = (datetime.utcnow() - start_time).total_seconds()
            
            return results
            
        except Exception as e:
            logger.error(f"Monitoring cycle failed: {e}")
            return {
                "error": str(e),
                "start_time": start_time.isoformat(),
                "end_time": datetime.utcnow().isoformat(),
                "checked": 0,
                "updated": 0,
                "errors": 1,
                "alerts_triggered": 0
            }

    async def get_profile_monitoring_status(self, profile_id: int) -> Dict[str, Any]:
        """Get monitoring status for a specific profile"""
        try:
            profile = await self.profile_repository.get_by_id(profile_id)
            if not profile:
                return {"error": "Profile not found"}
            
            latest_record = await self.follower_repository.get_latest(profile_id)
            active_alerts = await self.alert_repository.get_active_by_profile_id(profile_id)
            
            return {
                "username": profile.username,
                "is_active": profile.is_active,
                "last_checked": profile.last_checked.isoformat() if profile.last_checked else None,
                "current_followers": latest_record.followers_count if latest_record else None,
                "last_updated": latest_record.recorded_at.isoformat() if latest_record else None,
                "active_alerts": len(active_alerts),
                "alert_thresholds": [alert.threshold for alert in active_alerts]
            }
            
        except Exception as e:
            logger.error(f"Error getting monitoring status for profile {profile_id}: {e}")
            return {"error": str(e)}

    async def _get_previous_count(self, profile_id: int) -> Optional[int]:
        """Get previous follower count for comparison"""
        try:
            history = await self.follower_repository.get_history(profile_id, days=1)
            if len(history) >= 2:
                return history[1].followers_count  # Second most recent
            return None
        except Exception:
            return None

    async def _send_alert_notification(self, profile: Profile, alert: Alert, current_count: int):
        """Send alert notification via Telegram"""
        if not self.telegram_service:
            logger.warning("Telegram service not available")
            return
        
        try:
            # Get user to retrieve telegram_chat_id
            user = await self.user_repository.get_by_id(profile.user_id)
            
            if not user:
                logger.error(f"User not found for user_id: {profile.user_id}")
                return
            
            if not user.telegram_chat_id:
                logger.warning(f"No Telegram chat ID found for user {profile.user_id} (profile: {profile.username})")
                return
            
            success = await self.telegram_service.send_milestone_alert(
                chat_id=user.telegram_chat_id,
                username=profile.username,
                threshold=alert.threshold,
                current_count=current_count
            )
            
            if success:
                logger.info(f"Telegram notification sent for profile {profile.username}")
            else:
                logger.error(f"Failed to send Telegram notification for profile {profile.username}")
                
        except Exception as e:
            logger.error(f"Exception in _send_alert_notification: {e}")
