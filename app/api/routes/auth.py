from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import get_auth_service, get_current_user
from app.api.schemas.auth import UserRegister, UserLogin, TokenResponse, UserResponse
from app.services.auth_service import AuthServiceImpl
from app.core.entities import User
from app.core.exceptions import InvalidCredentialsError, UserNotFoundError

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegister,
    auth_service: AuthServiceImpl = Depends(get_auth_service)
):
    try:
        user = await auth_service.register_user(user_data.email, user_data.password)
        return UserResponse(
            email=user.email,
            telegram_chat_id=user.telegram_chat_id,
            created_at=user.created_at
        )
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=TokenResponse)
async def login_user(
    user_data: UserLogin,
    auth_service: AuthServiceImpl = Depends(get_auth_service)
):
    try:
        user = await auth_service.authenticate_user(user_data.email, user_data.password)
        access_token = auth_service.create_access_token({"sub": str(user.id)})
        return TokenResponse(access_token=access_token)
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return UserResponse(
        email=current_user.email,
        telegram_chat_id=current_user.telegram_chat_id,
        created_at=current_user.created_at
    )
