from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.db.database import get_db
from app.infrastructure.db.repositories import (
    UserRepositoryImpl, 
    ProfileRepositoryImpl,
    FollowerRepositoryImpl,
    AlertRepositoryImpl
)
from app.infrastructure.external.instagram_client import InstagramClientImpl
from app.services.auth_service import AuthServiceImpl
from app.services.profile_service import ProfileServiceImpl
from app.services.monitoring_service import MonitoringServiceImpl
from app.services.alert_service import AlertServiceImpl
from app.services.analytics_service import AnalyticsServiceImpl
from app.infrastructure.external.telegram_client import TelegramClientImpl
from app.core.entities import User
from app.core.exceptions import InvalidCredentialsError, UserNotFoundError, TokenExpiredError

security = HTTPBearer()


async def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepositoryImpl:
    return UserRepositoryImpl(db)


async def get_auth_service(user_repo: UserRepositoryImpl = Depends(get_user_repository)) -> AuthServiceImpl:
    return AuthServiceImpl(user_repo)


async def get_profile_repository(db: AsyncSession = Depends(get_db)) -> ProfileRepositoryImpl:
    return ProfileRepositoryImpl(db)


async def get_profile_service(profile_repo: ProfileRepositoryImpl = Depends(get_profile_repository)) -> ProfileServiceImpl:
    return ProfileServiceImpl(profile_repo)


async def get_follower_repository(db: AsyncSession = Depends(get_db)) -> FollowerRepositoryImpl:
    return FollowerRepositoryImpl(db)


async def get_alert_repository(db: AsyncSession = Depends(get_db)) -> AlertRepositoryImpl:
    return AlertRepositoryImpl(db)


async def get_instagram_service() -> InstagramClientImpl:
    service = InstagramClientImpl()
    await service.initialize()
    return service


async def get_telegram_service() -> TelegramClientImpl:
    from app.config import get_config
    config = get_config()
    return TelegramClientImpl(config)


async def get_alert_service(
    alert_repo: AlertRepositoryImpl = Depends(get_alert_repository),
    profile_repo: ProfileRepositoryImpl = Depends(get_profile_repository)
) -> AlertServiceImpl:
    return AlertServiceImpl(alert_repo, profile_repo)


async def get_monitoring_service(
    user_repo: UserRepositoryImpl = Depends(get_user_repository),
    profile_repo: ProfileRepositoryImpl = Depends(get_profile_repository),
    follower_repo: FollowerRepositoryImpl = Depends(get_follower_repository),
    alert_repo: AlertRepositoryImpl = Depends(get_alert_repository),
    instagram_service: InstagramClientImpl = Depends(get_instagram_service),
    telegram_service: TelegramClientImpl = Depends(get_telegram_service)
) -> MonitoringServiceImpl:
    return MonitoringServiceImpl(user_repo, profile_repo, follower_repo, alert_repo, instagram_service, telegram_service)


async def get_analytics_service(
    follower_repo: FollowerRepositoryImpl = Depends(get_follower_repository),
    profile_repo: ProfileRepositoryImpl = Depends(get_profile_repository)
) -> AnalyticsServiceImpl:
    return AnalyticsServiceImpl(follower_repo, profile_repo)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthServiceImpl = Depends(get_auth_service)
) -> User:
    try:
        return await auth_service.get_user_by_token(credentials.credentials)
    except (InvalidCredentialsError, TokenExpiredError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
