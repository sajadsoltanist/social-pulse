import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta

from app.core.entities import Profile, FollowerRecord
from app.core.interfaces import FollowerRepository, ProfileRepository
from app.core.exceptions import ProfileNotFoundError

logger = logging.getLogger(__name__)


class AnalyticsServiceImpl:
    def __init__(
        self,
        follower_repository: FollowerRepository,
        profile_repository: ProfileRepository
    ):
        self.follower_repository = follower_repository
        self.profile_repository = profile_repository

    async def get_user_top_changes(self, user_id: int, period_hours: int = 24) -> Dict[str, Any]:
        """Get top follower count changes for user's profiles within specified period"""
        try:
            # Get all user's profiles
            profiles = await self.profile_repository.get_by_user_id(user_id)
            
            increases = []
            decreases = []
            no_changes = []
            
            for profile in profiles:
                if not profile.is_active:
                    continue
                    
                try:
                    current_count, previous_count = await self._get_period_comparison(
                        profile.id, period_hours
                    )
                    
                    if current_count is None:
                        continue
                    
                    absolute_change = current_count - (previous_count or current_count)
                    percentage_change = self._calculate_percentage_change(
                        previous_count or current_count, current_count
                    )
                    
                    change_data = {
                        "username": profile.username,
                        "current_followers": current_count,
                        "previous_followers": previous_count or current_count,
                        "absolute_change": absolute_change,
                        "percentage_change": percentage_change,
                        "change_type": "increase" if absolute_change > 0 else "decrease" if absolute_change < 0 else "no_change",
                        "last_updated": datetime.utcnow()
                    }
                    
                    if absolute_change > 0:
                        increases.append(change_data)
                    elif absolute_change < 0:
                        decreases.append(change_data)
                    else:
                        no_changes.append(change_data)
                        
                except Exception as e:
                    logger.error(f"Error analyzing profile {profile.username}: {e}")
                    continue
            
            # Sort by magnitude of change
            increases.sort(key=lambda x: x["absolute_change"], reverse=True)
            decreases.sort(key=lambda x: abs(x["absolute_change"]), reverse=True)
            
            period_str = f"{period_hours}h" if period_hours < 168 else f"{period_hours//24}d"
            
            return {
                "period": period_str,
                "total_profiles": len(profiles),
                "increases": increases,
                "decreases": decreases,
                "no_changes": no_changes
            }
            
        except Exception as e:
            logger.error(f"Error getting top changes for user {user_id}: {e}")
            raise

    async def get_profile_growth_analysis(self, profile_username: str, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get detailed growth analysis for a specific profile"""
        try:
            profile = await self._validate_profile_ownership(profile_username, user_id)
            
            # Get historical data
            records = await self.follower_repository.get_history(profile.id, days)
            
            if not records:
                return {
                    "username": profile_username,
                    "current_followers": 0,
                    "period_start_followers": 0,
                    "total_change": 0,
                    "percentage_change": 0.0,
                    "average_daily_growth": 0.0,
                    "peak_followers": 0,
                    "peak_date": datetime.utcnow(),
                    "low_followers": 0,
                    "low_date": datetime.utcnow(),
                    "data_points": 0
                }
            
            # Calculate growth metrics
            growth_metrics = await self._calculate_growth_metrics(records)
            
            return {
                "username": profile_username,
                "current_followers": records[0].followers_count,
                "period_start_followers": records[-1].followers_count,
                "total_change": records[0].followers_count - records[-1].followers_count,
                "percentage_change": self._calculate_percentage_change(
                    records[-1].followers_count, records[0].followers_count
                ),
                "average_daily_growth": growth_metrics["average_daily_growth"],
                "peak_followers": growth_metrics["peak_followers"],
                "peak_date": growth_metrics["peak_date"],
                "low_followers": growth_metrics["low_followers"],
                "low_date": growth_metrics["low_date"],
                "data_points": len(records)
            }
            
        except Exception as e:
            logger.error(f"Error getting growth analysis for profile {profile_username}: {e}")
            raise

    async def get_user_dashboard(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive dashboard analytics for user"""
        try:
            profiles = await self.profile_repository.get_by_user_id(user_id)
            active_profiles = [p for p in profiles if p.is_active]
            
            if not active_profiles:
                return {
                    "total_profiles": 0,
                    "total_followers": 0,
                    "total_growth_24h": 0,
                    "total_growth_7d": 0,
                    "best_performer": None,
                    "worst_performer": None,
                    "last_updated": datetime.utcnow()
                }
            
            total_followers = 0
            total_growth_24h = 0
            total_growth_7d = 0
            profile_changes_24h = []
            
            for profile in active_profiles:
                try:
                    # Get current follower count
                    latest_record = await self.follower_repository.get_latest(profile.id)
                    if latest_record:
                        total_followers += latest_record.followers_count
                    
                    # Get 24h and 7d changes
                    current_24h, previous_24h = await self._get_period_comparison(profile.id, 24)
                    current_7d, previous_7d = await self._get_period_comparison(profile.id, 168)
                    
                    if current_24h is not None and previous_24h is not None:
                        change_24h = current_24h - previous_24h
                        total_growth_24h += change_24h
                        
                        profile_changes_24h.append({
                            "username": profile.username,
                            "current_followers": current_24h,
                            "previous_followers": previous_24h,
                            "absolute_change": change_24h,
                            "percentage_change": self._calculate_percentage_change(previous_24h, current_24h),
                            "change_type": "increase" if change_24h > 0 else "decrease" if change_24h < 0 else "no_change",
                            "last_updated": datetime.utcnow()
                        })
                    
                    if current_7d is not None and previous_7d is not None:
                        total_growth_7d += current_7d - previous_7d
                        
                except Exception as e:
                    logger.error(f"Error processing profile {profile.username} for dashboard: {e}")
                    continue
            
            # Find best and worst performers
            best_performer = None
            worst_performer = None
            
            if profile_changes_24h:
                best_performer = max(profile_changes_24h, key=lambda x: x["absolute_change"])
                worst_performer = min(profile_changes_24h, key=lambda x: x["absolute_change"])
                
                # Don't show as worst if it's actually positive growth
                if worst_performer["absolute_change"] >= 0:
                    worst_performer = None
            
            return {
                "total_profiles": len(active_profiles),
                "total_followers": total_followers,
                "total_growth_24h": total_growth_24h,
                "total_growth_7d": total_growth_7d,
                "best_performer": best_performer,
                "worst_performer": worst_performer,
                "last_updated": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard for user {user_id}: {e}")
            raise

    async def get_profile_insights(self, profile_username: str, user_id: int, period_days: int = 7) -> Dict[str, Any]:
        """Get detailed insights for a specific profile with historical data"""
        try:
            profile = await self._validate_profile_ownership(profile_username, user_id)
            
            records = await self.follower_repository.get_history(profile.id, period_days)
            
            if not records:
                return {
                    "username": profile_username,
                    "period_days": period_days,
                    "current_followers": 0,
                    "total_change": 0,
                    "data": []
                }
            
            # Prepare historical data with daily changes
            historical_data = []
            for i, record in enumerate(records):
                daily_change = None
                if i < len(records) - 1:
                    daily_change = record.followers_count - records[i + 1].followers_count
                
                historical_data.append({
                    "date": record.recorded_at,
                    "followers": record.followers_count,
                    "daily_change": daily_change
                })
            
            return {
                "username": profile_username,
                "period_days": period_days,
                "current_followers": records[0].followers_count,
                "total_change": records[0].followers_count - records[-1].followers_count,
                "data": historical_data
            }
            
        except Exception as e:
            logger.error(f"Error getting insights for profile {profile_username}: {e}")
            raise

    async def _calculate_growth_metrics(self, records: List[FollowerRecord]) -> Dict[str, Any]:
        """Calculate growth metrics from follower records"""
        if not records:
            return {
                "average_daily_growth": 0.0,
                "peak_followers": 0,
                "peak_date": datetime.utcnow(),
                "low_followers": 0,
                "low_date": datetime.utcnow()
            }
        
        # Find peak and low points
        peak_record = max(records, key=lambda x: x.followers_count)
        low_record = min(records, key=lambda x: x.followers_count)
        
        # Calculate average daily growth
        if len(records) > 1:
            total_change = records[0].followers_count - records[-1].followers_count
            days_span = (records[0].recorded_at - records[-1].recorded_at).days
            average_daily_growth = total_change / max(days_span, 1)
        else:
            average_daily_growth = 0.0
        
        return {
            "average_daily_growth": average_daily_growth,
            "peak_followers": peak_record.followers_count,
            "peak_date": peak_record.recorded_at,
            "low_followers": low_record.followers_count,
            "low_date": low_record.recorded_at
        }

    async def _get_period_comparison(self, profile_id: int, hours_ago: int) -> Tuple[Optional[int], Optional[int]]:
        """Get current and previous follower counts for comparison"""
        try:
            # Get current count
            latest_record = await self.follower_repository.get_latest(profile_id)
            current_count = latest_record.followers_count if latest_record else None
            
            # Get historical data to find count from hours_ago
            days_to_check = max(1, (hours_ago // 24) + 1)
            records = await self.follower_repository.get_history(profile_id, days_to_check)
            
            if not records:
                return current_count, None
            
            # Find the record closest to the target time
            target_time = datetime.utcnow() - timedelta(hours=hours_ago)
            previous_record = None
            
            for record in reversed(records):  # Start from oldest
                if record.recorded_at <= target_time:
                    previous_record = record
                else:
                    break
            
            previous_count = previous_record.followers_count if previous_record else None
            
            return current_count, previous_count
            
        except Exception as e:
            logger.error(f"Error getting period comparison for profile {profile_id}: {e}")
            return None, None

    def _calculate_percentage_change(self, old_value: int, new_value: int) -> float:
        """Calculate percentage change between two values"""
        if old_value == 0:
            return 100.0 if new_value > 0 else 0.0
        
        return ((new_value - old_value) / old_value) * 100.0

    async def _validate_profile_ownership(self, profile_username: str, user_id: int) -> Profile:
        """Validate that the profile belongs to the user"""
        profile = await self.profile_repository.get_by_username_and_user_id(profile_username, user_id)
        
        if not profile:
            raise ProfileNotFoundError(f"Profile {profile_username} not found or not owned by user")
        
        return profile
