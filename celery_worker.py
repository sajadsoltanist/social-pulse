#!/usr/bin/env python3
"""
Celery worker entry point for SocialPulse background tasks.

Usage:
    # Start worker
    celery -A celery_worker.celery_app worker --loglevel=info

    # Start beat scheduler
    celery -A celery_worker.celery_app beat --loglevel=info

    # Start both worker and beat
    celery -A celery_worker.celery_app worker --beat --loglevel=info

    # Monitor tasks
    celery -A celery_worker.celery_app flower
"""

from app.infrastructure.background_tasks import celery_app

# Import tasks to register them
from app.infrastructure.background_tasks import (
    monitor_all_profiles,
    check_profile_followers,
    test_instagram_connection,
    health_check
)

if __name__ == '__main__':
    celery_app.start() 