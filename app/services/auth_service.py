from datetime import datetime, timedelta
from typing import Optional
import bcrypt
import jwt
from app.core.entities import User
from app.core.interfaces import UserRepository, AuthService
from app.core.exceptions import InvalidCredentialsError, UserNotFoundError, TokenExpiredError
from app.config import get_config


class AuthServiceImpl(AuthService):
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        self.config = get_config()

    def create_access_token(self, user_data: dict) -> str:
        to_encode = user_data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.config.JWT_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.config.SECRET_KEY, algorithm=self.config.JWT_ALGORITHM)

    def verify_token(self, token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(token, self.config.SECRET_KEY, algorithms=[self.config.JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token has expired")
        except jwt.JWTError:
            return None

    def hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def verify_password(self, password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

    async def register_user(self, email: str, password: str) -> User:
        existing_user = await self.user_repository.get_by_email(email)
        if existing_user:
            raise InvalidCredentialsError("Email already registered")
        
        hashed_password = self.hash_password(password)
        user = User(email=email, password_hash=hashed_password)
        return await self.user_repository.create(user)

    async def authenticate_user(self, email: str, password: str) -> User:
        user = await self.user_repository.get_by_email(email)
        if not user or not self.verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")
        return user

    async def get_user_by_token(self, token: str) -> User:
        payload = self.verify_token(token)
        if not payload:
            raise InvalidCredentialsError("Invalid token")
        
        user_id = payload.get("sub")
        if not user_id:
            raise InvalidCredentialsError("Invalid token payload")
        
        user = await self.user_repository.get_by_id(int(user_id))
        if not user:
            raise UserNotFoundError("User not found")
        return user
