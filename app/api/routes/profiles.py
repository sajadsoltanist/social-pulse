from fastapi import APIRouter, Depends, HTTPException, status
from app.core.entities import User
from app.api.deps import get_current_user, get_profile_service
from app.api.schemas.profile import ProfileCreate, ProfileUpdate, ProfileResponse, ProfileListResponse
from app.services.profile_service import ProfileServiceImpl
from app.core.exceptions import ProfileNotFoundError, ProfileAlreadyExistsError

router = APIRouter()


@router.get("/", response_model=ProfileListResponse)
async def get_user_profiles(
    current_user: User = Depends(get_current_user),
    profile_service: ProfileServiceImpl = Depends(get_profile_service)
):
    profiles = await profile_service.get_user_profiles(current_user.id)
    profile_responses = [
        ProfileResponse(
            username=profile.username,
            display_name=profile.display_name,
            is_active=profile.is_active,
            last_checked=profile.last_checked,
            created_at=profile.created_at
        )
        for profile in profiles
    ]
    return ProfileListResponse(profiles=profile_responses, total=len(profile_responses))


@router.post("/", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    profile_data: ProfileCreate,
    current_user: User = Depends(get_current_user),
    profile_service: ProfileServiceImpl = Depends(get_profile_service)
):
    try:
        profile = await profile_service.create_profile(
            user_id=current_user.id,
            username=profile_data.username,
            display_name=profile_data.display_name
        )
        return ProfileResponse(
            username=profile.username,
            display_name=profile.display_name,
            is_active=profile.is_active,
            last_checked=profile.last_checked,
            created_at=profile.created_at
        )
    except ProfileAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.get("/{username}", response_model=ProfileResponse)
async def get_profile(
    username: str,
    current_user: User = Depends(get_current_user),
    profile_service: ProfileServiceImpl = Depends(get_profile_service)
):
    try:
        profile = await profile_service.get_profile_by_username(username, current_user.id)
        return ProfileResponse(
            username=profile.username,
            display_name=profile.display_name,
            is_active=profile.is_active,
            last_checked=profile.last_checked,
            created_at=profile.created_at
        )
    except ProfileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )


@router.put("/{username}", response_model=ProfileResponse)
async def update_profile(
    username: str,
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    profile_service: ProfileServiceImpl = Depends(get_profile_service)
):
    try:
        updates = profile_data.dict(exclude_unset=True)
        profile = await profile_service.update_profile_by_username(username, current_user.id, updates)
        return ProfileResponse(
            username=profile.username,
            display_name=profile.display_name,
            is_active=profile.is_active,
            last_checked=profile.last_checked,
            created_at=profile.created_at
        )
    except ProfileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )


@router.delete("/{username}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    username: str,
    current_user: User = Depends(get_current_user),
    profile_service: ProfileServiceImpl = Depends(get_profile_service)
):
    try:
        await profile_service.delete_profile_by_username(username, current_user.id)
    except ProfileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )


@router.patch("/{username}/toggle", response_model=ProfileResponse)
async def toggle_profile_monitoring(
    username: str,
    is_active: bool,
    current_user: User = Depends(get_current_user),
    profile_service: ProfileServiceImpl = Depends(get_profile_service)
):
    try:
        profile = await profile_service.toggle_profile_monitoring_by_username(username, current_user.id, is_active)
        return ProfileResponse(
            username=profile.username,
            display_name=profile.display_name,
            is_active=profile.is_active,
            last_checked=profile.last_checked,
            created_at=profile.created_at
        )
    except ProfileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
