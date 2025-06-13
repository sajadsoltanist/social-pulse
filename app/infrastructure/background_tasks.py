import asyncio
import logging
from typing import Dict, Any

from celery import Celery
from celery.schedules import crontab

from app.config import get_config
from app.infrastructure.db.database import AsyncSessionLocal
from app.infrastructure.db.repositories import (
    ProfileRepositoryImpl,
    FollowerRepositoryImpl,
    AlertRepositoryImpl
)
from app.infrastructure.external.instagram_client import InstagramClientImpl
from app.services.monitoring_service import MonitoringServiceImpl

logger = logging.getLogger(__name__)

# Initialize Celery
config = get_config()
celery_app = Celery(
    "socialpulse",
    broker=config.CELERY_BROKER_URL,
    backend=config.CELERY_RESULT_BACKEND
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
)

# Periodic task schedule
celery_app.conf.beat_schedule = {
    'monitor-all-profiles': {
        'task': 'app.infrastructure.background_tasks.monitor_all_profiles',
        'schedule': crontab(minute=f'*/{config.MONITORING_INTERVAL_MINUTES}'),
    },
}


def run_async_task(coro):
    """Helper function to run async code in Celery tasks safely"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def run_monitoring_cycle():
    """Run complete monitoring cycle"""
    # Create Instagram service
    instagram_service = InstagramClientImpl()
    await instagram_service.initialize()
    
    # Create database session
    async with AsyncSessionLocal() as session:
        # Create repositories
        profile_repo = ProfileRepositoryImpl(session)
        follower_repo = FollowerRepositoryImpl(session)
        alert_repo = AlertRepositoryImpl(session)
        
        # Create monitoring service
        monitoring_service = MonitoringServiceImpl(
            profile_repository=profile_repo,
            follower_repository=follower_repo,
            alert_repository=alert_repo,
            instagram_service=instagram_service
        )
        
        # Run monitoring cycle
        return await monitoring_service.run_monitoring_cycle()


async def run_profile_check(profile_id: int):
    """Check specific profile"""
    # Create Instagram service
    instagram_service = InstagramClientImpl()
    await instagram_service.initialize()
    
    # Create database session
    async with AsyncSessionLocal() as session:
        # Create repositories
        profile_repo = ProfileRepositoryImpl(session)
        follower_repo = FollowerRepositoryImpl(session)
        alert_repo = AlertRepositoryImpl(session)
        
        # Create monitoring service
        monitoring_service = MonitoringServiceImpl(
            profile_repository=profile_repo,
            follower_repository=follower_repo,
            alert_repository=alert_repo,
            instagram_service=instagram_service
        )
        
        # Check single profile
        result = await monitoring_service.check_single_profile(profile_id)
        
        if result:
            # Process alerts
            alerts = await monitoring_service.process_alerts(profile_id, result.followers_count)
            
            return {
                "profile_id": profile_id,
                "follower_count": result.followers_count,
                "alerts_triggered": len(alerts),
                "status": "updated"
            }
        else:
            return {
                "profile_id": profile_id,
                "status": "no_change"
            }


@celery_app.task(bind=True, name='monitor_all_profiles')
def monitor_all_profiles(self) -> Dict[str, Any]:
    """Celery task to monitor all active profiles"""
    try:
        logger.info("Starting scheduled monitoring task")
        
        # Use helper function for safe async execution in Celery
        results = run_async_task(run_monitoring_cycle())
        
        logger.info(f"Monitoring task completed: {results}")
        return results
            
    except Exception as e:
        logger.error(f"Monitoring task failed: {e}")
        # Retry with exponential backoff
        raise self.retry(
            exc=e,
            countdown=60 * (2 ** self.request.retries),
            max_retries=3
        )


@celery_app.task(bind=True, name='check_profile_followers')
def check_profile_followers(self, profile_id: int) -> Dict[str, Any]:
    """Celery task to check a specific profile's followers"""
    try:
        logger.info(f"Starting profile check task for profile {profile_id}")
        
        # Use helper function for safe async execution in Celery
        response = run_async_task(run_profile_check(profile_id))
        
        logger.info(f"Profile check completed: {response}")
        return response
            
    except Exception as e:
        logger.error(f"Profile check task failed for profile {profile_id}: {e}")
        # Retry with exponential backoff
        raise self.retry(
            exc=e,
            countdown=30 * (2 ** self.request.retries),
            max_retries=3
        )


@celery_app.task(name='test_instagram_connection')
def test_instagram_connection() -> Dict[str, Any]:
    """Test Instagram connection and authentication"""
    try:
        logger.info("Testing Instagram connection")
        
        async def _test_connection():
            instagram_service = InstagramClientImpl()
            success = await instagram_service.initialize()
            
            if success:
                # Test with a known public account
                follower_count = await instagram_service.get_follower_count("instagram")
                
                return {
                    "status": "success",
                    "authenticated": True,
                    "test_account": "instagram",
                    "test_follower_count": follower_count
                }
            else:
                return {
                    "status": "failed",
                    "authenticated": False,
                    "error": "Failed to initialize Instagram client"
                }
        
        # Use helper function for safe async execution in Celery
        return run_async_task(_test_connection())
            
    except Exception as e:
        logger.error(f"Instagram connection test failed: {e}")
        return {
            "status": "error",
            "authenticated": False,
            "error": str(e)
        }


# Task routing
celery_app.conf.task_routes = {
    'app.infrastructure.background_tasks.monitor_all_profiles': {'queue': 'monitoring'},
    'app.infrastructure.background_tasks.check_profile_followers': {'queue': 'monitoring'},
    'app.infrastructure.background_tasks.test_instagram_connection': {'queue': 'testing'},
}

# Error handling
@celery_app.task(bind=True)
def task_failure_handler(self, task_id, error, traceback):
    """Handle task failures"""
    logger.error(f"Task {task_id} failed: {error}")
    logger.error(f"Traceback: {traceback}")


# Health check task
@celery_app.task(name='health_check')
def health_check() -> Dict[str, Any]:
    """Health check task for monitoring system status"""
    import time
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "worker_id": celery_app.control.inspect().active()
    }
