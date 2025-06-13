from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .user import Base


class Profile(Base):
    __tablename__ = "profiles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    username = Column(String(30), nullable=False, index=True)
    display_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    last_checked = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    user = relationship("User", back_populates="profiles")
    alerts = relationship("Alert", back_populates="profile", cascade="all, delete-orphan")
    follower_records = relationship("FollowerRecord", back_populates="profile", cascade="all, delete-orphan")
