
from sqlalchemy.orm import Session as DBSession
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Tuple
import hashlib

from shared.models.tables import User, RefreshToken, Subscription, UserRole
from shared.schemas.auth import UserCreate, UserLogin, UserResponse, TokenResponse
from shared.auth.jwt_handler import JWTHandler
from shared.utils.redis_client import RedisClient
from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, db: DBSession, jwt_handler: JWTHandler, redis: RedisClient):
        self.db = db
        self.jwt = jwt_handler
        self.redis = redis

    async def register(self, data: UserCreate) -> TokenResponse:
        
        existing = self.db.query(User).filter(User.email == data.email).first()
        if existing:
            raise ValueError("Email already registered")
        
        user = User(
            email=data.email,
            full_name=data.full_name,
            password_hash=pwd_context.hash(data.password),
            role=UserRole.FREE
        )
        self.db.add(user)
        self.db.flush()
        
        from shared.models.tables import UserProfile
        profile = UserProfile(user_id=user.id)
        self.db.add(profile)
        
        subscription = Subscription(
            user_id=user.id,
            plan=UserRole.FREE,
            sessions_limit=3,
            sessions_used_this_month=0
        )
        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(user)
        
        return await self._generate_token_response(user)

    async def login(self, data: UserLogin) -> TokenResponse:
        user = self.db.query(User).filter(User.email == data.email).first()
        if not user:
            raise ValueError("Invalid email or password")
        
        if not user.password_hash or not pwd_context.verify(data.password, user.password_hash):
            raise ValueError("Invalid email or password")
        
        if not user.is_active:
            raise ValueError("Account is disabled")
        
        return await self._generate_token_response(user)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        
        payload = self.jwt.validate_refresh_token(refresh_token)
        if not payload:
            raise ValueError("Invalid refresh token")
        
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        if await self.redis.is_token_blacklisted(token_hash):
            raise ValueError("Token has been revoked")
        
        await self.redis.blacklist_token(token_hash)
        
        user_id = payload.get("sub")
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")
        
        return await self._generate_token_response(user)

    async def logout(self, refresh_token: str):
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        await self.redis.blacklist_token(token_hash)

    async def validate_token(self, token: str) -> dict:
        payload = self.jwt.validate_access_token(token)
        if not payload:
            return {"valid": False}
        
        return {
            "valid": True,
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role")
        }

    async def _generate_token_response(self, user: User) -> TokenResponse:
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value
        }
        
        access_token = self.jwt.create_access_token(
            token_data,
            expires_minutes=settings.access_token_expire_minutes
        )
        refresh_token = self.jwt.create_refresh_token(
            token_data,
            expires_days=settings.refresh_token_expire_days
        )
        
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            avatar_url=user.avatar_url,
            is_email_verified=user.is_email_verified,
            created_at=user.created_at
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
            user=user_response
        )

    async def get_current_user(self, token_payload: dict) -> UserResponse:
        user_id = token_payload.get("sub")
        if not user_id:
            raise ValueError("Invalid token payload")
            
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
            
        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value if hasattr(user.role, 'value') else user.role,
            avatar_url=user.avatar_url,
            is_email_verified=user.is_email_verified,
            created_at=user.created_at
        )
