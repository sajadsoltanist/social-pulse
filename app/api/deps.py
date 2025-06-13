from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.db.database import get_db
from app.infrastructure.db.repositories import UserRepositoryImpl, ProfileRepositoryImpl
from app.services.auth_service import AuthServiceImpl
from app.services.profile_service import ProfileServiceImpl
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
