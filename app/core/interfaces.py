from abc import ABC, abstractmethod
from typing import List, Optional
from .entities import User, Profile, Alert, FollowerRecord


class UserRepository(ABC):
    @abstractmethod
    async def create(self, user: User) -> User:
        pass
    
    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]:
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        pass


class ProfileRepository(ABC):
    @abstractmethod
    async def create(self, profile: Profile) -> Profile:
        pass
    
    @abstractmethod
    async def get_by_id(self, profile_id: int) -> Optional[Profile]:
        pass
    
    @abstractmethod
    async def get_by_user_id(self, user_id: int) -> List[Profile]:
        pass
    
    @abstractmethod
    async def get_by_username_and_user_id(self, username: str, user_id: int) -> Optional[Profile]:
        pass
    
    @abstractmethod
    async def get_all_active(self) -> List[Profile]:
        pass
    
    @abstractmethod
    async def update(self, profile: Profile) -> Profile:
        pass
    
    @abstractmethod
    async def delete(self, profile_id: int) -> bool:
        pass
    
    @abstractmethod
    async def update_last_checked(self, profile_id: int) -> None:
        pass


class AlertRepository(ABC):
    @abstractmethod
    async def create(self, alert: Alert) -> Alert:
        pass
    
    @abstractmethod
    async def get_active_by_profile_id(self, profile_id: int) -> List[Alert]:
        pass
    
    @abstractmethod
    async def mark_as_triggered(self, alert_id: int) -> None:
        pass


class FollowerRepository(ABC):
    @abstractmethod
    async def create(self, record: FollowerRecord) -> FollowerRecord:
        pass
    
    @abstractmethod
    async def get_latest(self, profile_id: int) -> Optional[FollowerRecord]:
        pass
    
    @abstractmethod
    async def get_history(self, profile_id: int, days: int = 30) -> List[FollowerRecord]:
        pass


class InstagramService(ABC):
    @abstractmethod
    async def get_follower_count(self, username: str) -> Optional[int]:
        pass


class TelegramService(ABC):
    @abstractmethod
    async def send_milestone_alert(self, chat_id: str, username: str, threshold: int, current_count: int) -> bool:
        pass


class AuthService(ABC):
    @abstractmethod
    def create_access_token(self, user_data: dict) -> str:
        pass
    
    @abstractmethod
    def verify_token(self, token: str) -> Optional[dict]:
        pass 