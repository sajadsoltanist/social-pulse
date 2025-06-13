from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from ..database import Base


class FollowerRecord(Base):
    __tablename__ = "follower_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    followers_count = Column(Integer, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    profile = relationship("Profile", back_populates="follower_records")
    
    __table_args__ = (
        Index("ix_profile_recorded", "profile_id", "recorded_at"),
    )
