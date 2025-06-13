from typing import List, Optional
from app.core.entities import Profile
from app.core.interfaces import ProfileRepository
from app.core.exceptions import ProfileNotFoundError, ProfileAlreadyExistsError


class ProfileServiceImpl:
    def __init__(self, profile_repository: ProfileRepository):
        self.profile_repository = profile_repository

    async def create_profile(self, user_id: int, username: str, display_name: Optional[str] = None) -> Profile:
        existing_profile = await self.profile_repository.get_by_username_and_user_id(username, user_id)
        if existing_profile:
            raise ProfileAlreadyExistsError(f"Profile with username '{username}' already exists")
        
        profile = Profile(
            user_id=user_id,
            username=username,
            display_name=display_name
        )
        return await self.profile_repository.create(profile)

    async def get_user_profiles(self, user_id: int) -> List[Profile]:
        return await self.profile_repository.get_by_user_id(user_id)

    async def get_profile_by_id(self, profile_id: int, user_id: int) -> Profile:
        return await self.validate_profile_ownership(profile_id, user_id)

    async def get_profile_by_username(self, username: str, user_id: int) -> Profile:
        profile = await self.profile_repository.get_by_username_and_user_id(username, user_id)
        if not profile:
            raise ProfileNotFoundError("Profile not found")
        return profile

    async def update_profile(self, profile_id: int, user_id: int, updates: dict) -> Profile:
        profile = await self.validate_profile_ownership(profile_id, user_id)
        
        if 'display_name' in updates:
            profile.display_name = updates['display_name']
        if 'is_active' in updates:
            profile.is_active = updates['is_active']
        
        return await self.profile_repository.update(profile)

    async def update_profile_by_username(self, username: str, user_id: int, updates: dict) -> Profile:
        profile = await self.get_profile_by_username(username, user_id)
        
        if 'display_name' in updates:
            profile.display_name = updates['display_name']
        if 'is_active' in updates:
            profile.is_active = updates['is_active']
        
        return await self.profile_repository.update(profile)

    async def delete_profile(self, profile_id: int, user_id: int) -> bool:
        await self.validate_profile_ownership(profile_id, user_id)
        return await self.profile_repository.delete(profile_id)

    async def delete_profile_by_username(self, username: str, user_id: int) -> bool:
        profile = await self.get_profile_by_username(username, user_id)
        return await self.profile_repository.delete(profile.id)

    async def validate_profile_ownership(self, profile_id: int, user_id: int) -> Profile:
        profile = await self.profile_repository.get_by_id(profile_id)
        if not profile or profile.user_id != user_id:
            raise ProfileNotFoundError("Profile not found")
        return profile

    async def check_username_availability(self, username: str, user_id: int) -> bool:
        existing_profile = await self.profile_repository.get_by_username_and_user_id(username, user_id)
        return existing_profile is None

    async def toggle_profile_monitoring(self, profile_id: int, user_id: int, is_active: bool) -> Profile:
        profile = await self.validate_profile_ownership(profile_id, user_id)
        profile.is_active = is_active
        return await self.profile_repository.update(profile)

    async def toggle_profile_monitoring_by_username(self, username: str, user_id: int, is_active: bool) -> Profile:
        profile = await self.get_profile_by_username(username, user_id)
        profile.is_active = is_active
        return await self.profile_repository.update(profile)
