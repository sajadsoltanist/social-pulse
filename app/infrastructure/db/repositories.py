from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.interfaces import UserRepository, ProfileRepository, AlertRepository, FollowerRepository
from app.core.entities import User, Profile, Alert, FollowerRecord
from .models import User as UserModel, Profile as ProfileModel, Alert as AlertModel, FollowerRecord as FollowerRecordModel


class UserRepositoryImpl(UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, user: User) -> User:
        user_model = UserModel(
            email=user.email,
            password_hash=user.password_hash,
            telegram_chat_id=user.telegram_chat_id
        )
        self.session.add(user_model)
        await self.session.flush()
        await self.session.refresh(user_model)
        return self._to_entity(user_model)
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.session.execute(select(UserModel).where(UserModel.id == user_id))
        user_model = result.scalar_one_or_none()
        return self._to_entity(user_model) if user_model else None
    
    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(select(UserModel).where(UserModel.email == email))
        user_model = result.scalar_one_or_none()
        return self._to_entity(user_model) if user_model else None
    
    def _to_entity(self, model: UserModel) -> User:
        return User(
            id=model.id,
            email=model.email,
            password_hash=model.password_hash,
            telegram_chat_id=model.telegram_chat_id,
            created_at=model.created_at
        )


class ProfileRepositoryImpl(ProfileRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, profile: Profile) -> Profile:
        profile_model = ProfileModel(
            user_id=profile.user_id,
            username=profile.username,
            display_name=profile.display_name,
            is_active=profile.is_active
        )
        self.session.add(profile_model)
        await self.session.flush()
        await self.session.refresh(profile_model)
        return self._to_entity(profile_model)
    
    async def get_by_id(self, profile_id: int) -> Optional[Profile]:
        result = await self.session.execute(select(ProfileModel).where(ProfileModel.id == profile_id))
        profile_model = result.scalar_one_or_none()
        return self._to_entity(profile_model) if profile_model else None
    
    async def get_by_user_id(self, user_id: int) -> List[Profile]:
        result = await self.session.execute(select(ProfileModel).where(ProfileModel.user_id == user_id))
        profile_models = result.scalars().all()
        return [self._to_entity(model) for model in profile_models]
    
    async def get_all_active(self) -> List[Profile]:
        result = await self.session.execute(select(ProfileModel).where(ProfileModel.is_active == True))
        profile_models = result.scalars().all()
        return [self._to_entity(model) for model in profile_models]
    
    async def update_last_checked(self, profile_id: int) -> None:
        await self.session.execute(
            update(ProfileModel)
            .where(ProfileModel.id == profile_id)
            .values(last_checked=datetime.utcnow())
        )
    
    def _to_entity(self, model: ProfileModel) -> Profile:
        return Profile(
            id=model.id,
            user_id=model.user_id,
            username=model.username,
            display_name=model.display_name,
            is_active=model.is_active,
            last_checked=model.last_checked,
            created_at=model.created_at
        )


class AlertRepositoryImpl(AlertRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, alert: Alert) -> Alert:
        alert_model = AlertModel(
            profile_id=alert.profile_id,
            threshold=alert.threshold,
            is_active=alert.is_active
        )
        self.session.add(alert_model)
        await self.session.flush()
        await self.session.refresh(alert_model)
        return self._to_entity(alert_model)
    
    async def get_active_by_profile_id(self, profile_id: int) -> List[Alert]:
        result = await self.session.execute(
            select(AlertModel).where(
                AlertModel.profile_id == profile_id,
                AlertModel.is_active == True,
                AlertModel.triggered_at.is_(None)
            )
        )
        alert_models = result.scalars().all()
        return [self._to_entity(model) for model in alert_models]
    
    async def mark_as_triggered(self, alert_id: int) -> None:
        await self.session.execute(
            update(AlertModel)
            .where(AlertModel.id == alert_id)
            .values(triggered_at=datetime.utcnow())
        )
    
    def _to_entity(self, model: AlertModel) -> Alert:
        return Alert(
            id=model.id,
            profile_id=model.profile_id,
            threshold=model.threshold,
            is_active=model.is_active,
            triggered_at=model.triggered_at,
            created_at=model.created_at
        )


class FollowerRepositoryImpl(FollowerRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, record: FollowerRecord) -> FollowerRecord:
        record_model = FollowerRecordModel(
            profile_id=record.profile_id,
            followers_count=record.followers_count
        )
        self.session.add(record_model)
        await self.session.flush()
        await self.session.refresh(record_model)
        return self._to_entity(record_model)
    
    async def get_latest(self, profile_id: int) -> Optional[FollowerRecord]:
        result = await self.session.execute(
            select(FollowerRecordModel)
            .where(FollowerRecordModel.profile_id == profile_id)
            .order_by(FollowerRecordModel.recorded_at.desc())
            .limit(1)
        )
        record_model = result.scalar_one_or_none()
        return self._to_entity(record_model) if record_model else None
    
    async def get_history(self, profile_id: int, days: int = 30) -> List[FollowerRecord]:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        result = await self.session.execute(
            select(FollowerRecordModel)
            .where(
                FollowerRecordModel.profile_id == profile_id,
                FollowerRecordModel.recorded_at >= cutoff_date
            )
            .order_by(FollowerRecordModel.recorded_at.desc())
        )
        record_models = result.scalars().all()
        return [self._to_entity(model) for model in record_models]
    
    def _to_entity(self, model: FollowerRecordModel) -> FollowerRecord:
        return FollowerRecord(
            id=model.id,
            profile_id=model.profile_id,
            followers_count=model.followers_count,
            recorded_at=model.recorded_at
        ) 