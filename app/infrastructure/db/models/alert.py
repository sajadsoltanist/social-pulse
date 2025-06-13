from datetime import datetime
from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .user import Base


class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    threshold = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    triggered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    profile = relationship("Profile", back_populates="alerts")
