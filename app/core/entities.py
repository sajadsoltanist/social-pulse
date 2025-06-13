import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    email: str
    password_hash: str
    id: Optional[int] = None
    telegram_chat_id: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self._is_valid_email(self.email):
            raise ValueError("Invalid email format")
    
    def can_receive_notifications(self) -> bool:
        return self.telegram_chat_id is not None
    
    def _is_valid_email(self, email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))


@dataclass
class Profile:
    user_id: int
    username: str
    id: Optional[int] = None
    display_name: Optional[str] = None
    is_active: bool = True
    last_checked: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self._is_valid_username(self.username):
            raise ValueError("Invalid Instagram username")
    
    def can_be_monitored(self) -> bool:
        return self.is_active and self.username is not None
    
    def update_last_check(self) -> None:
        self.last_checked = datetime.utcnow()
    
    def _is_valid_username(self, username: str) -> bool:
        if not username or len(username) > 30:
            return False
        pattern = r'^[a-zA-Z0-9._]+$'
        return bool(re.match(pattern, username))


@dataclass
class Alert:
    profile_id: int
    threshold: int
    id: Optional[int] = None
    is_active: bool = True
    triggered_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.threshold <= 0:
            raise ValueError("Threshold must be positive")
    
    def should_trigger(self, current_count: int) -> bool:
        return (self.is_active and 
                self.triggered_at is None and 
                current_count >= self.threshold)
    
    def trigger(self) -> None:
        self.triggered_at = datetime.utcnow()


@dataclass
class FollowerRecord:
    profile_id: int
    followers_count: int
    id: Optional[int] = None
    recorded_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.followers_count < 0:
            raise ValueError("Followers count cannot be negative")
        if self.recorded_at is None:
            self.recorded_at = datetime.utcnow() 