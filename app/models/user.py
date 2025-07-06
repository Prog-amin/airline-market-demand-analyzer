"""
User and authentication related models.

This module contains the User model and related authentication models.
"""
import enum
from datetime import datetime, timedelta
from typing import List, Optional

import jwt
from sqlalchemy import (
    Boolean, 
    Column, 
    DateTime, 
    Enum, 
    ForeignKey, 
    Integer, 
    String, 
    Text,
    event
)
from sqlalchemy.orm import relationship, Session

from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models.base import Base, TimestampMixin, SoftDeleteMixin

class UserRole(str, enum.Enum):
    """User roles for authorization."""
    USER = "user"
    ADMIN = "admin"
    AGENT = "agent"
    ANALYST = "analyst"

class UserStatus(str, enum.Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"

class User(Base, TimestampMixin, SoftDeleteMixin):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    # Authentication fields
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    
    # User information
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    status = Column(
        Enum(UserStatus), 
        default=UserStatus.PENDING, 
        nullable=False
    )
    
    # Roles and permissions
    role = Column(
        Enum(UserRole), 
        default=UserRole.USER, 
        nullable=False
    )
    
    # Email verification
    email_verified = Column(Boolean, default=False, nullable=False)
    email_verified_at = Column(DateTime, nullable=True)
    
    # Password reset
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)
    
    # Relationships
    api_keys = relationship("UserAPIKey", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    
    # Audit fields
    last_login_at = Column(DateTime, nullable=True)
    last_login_ip = Column(String(45), nullable=True)
    
    @property
    def full_name(self) -> str:
        """Get the user's full name."""
        return f"{self.first_name or ''} {self.last_name or ''}".strip() or self.email
    
    @property
    def is_admin(self) -> bool:
        """Check if the user has admin privileges."""
        return self.role == UserRole.ADMIN
    
    @property
    def is_authenticated(self) -> bool:
        """Check if the user is authenticated."""
        return self.is_active and not self.is_deleted
    
    def set_password(self, password: str) -> None:
        """Set the user's password."""
        self.hashed_password = get_password_hash(password)
    
    def verify_password(self, password: str) -> bool:
        """Verify the user's password."""
        return verify_password(password, self.hashed_password)
    
    def create_access_token(self, expires_delta: Optional[timedelta] = None) -> str:
        """Create an access token for the user."""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
            
        to_encode = {
            "sub": str(self.id),
            "email": self.email,
            "role": self.role,
            "exp": expire
        }
        
        return jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
    
    def create_refresh_token(self) -> str:
        """Create a refresh token for the user."""
        expire = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        
        to_encode = {
            "sub": str(self.id),
            "token_type": "refresh",
            "exp": expire
        }
        
        return jwt.encode(
            to_encode,
            settings.REFRESH_TOKEN_SECRET,
            algorithm=settings.ALGORITHM
        )
    
    def update_last_login(self, ip_address: Optional[str] = None) -> None:
        """Update the user's last login information."""
        self.last_login_at = datetime.utcnow()
        if ip_address:
            self.last_login_ip = ip_address

class UserAPIKey(Base, TimestampMixin):
    """API keys for programmatic access to the API."""
    
    __tablename__ = "user_api_keys"
    
    # Key information
    name = Column(String(100), nullable=False)
    key_id = Column(String(50), unique=True, index=True, nullable=False)
    key_hash = Column(String(255), nullable=False)
    
    # Scopes (stored as comma-separated values)
    scopes = Column(String(255), default="", nullable=False)
    
    # Expiration
    expires_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    user_id = Column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False
    )
    user = relationship("User", back_populates="api_keys")
    
    @property
    def is_expired(self) -> bool:
        """Check if the API key has expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def get_scopes(self) -> List[str]:
        """Get the list of scopes for this API key."""
        if not self.scopes:
            return []
        return [s.strip() for s in self.scopes.split(",") if s.strip()]
    
    def has_scope(self, scope: str) -> bool:
        """Check if the API key has the specified scope."""
        if not self.scopes:
            return False
        return scope in self.get_scopes()
    
    def update_last_used(self) -> None:
        """Update the last used timestamp."""
        self.last_used_at = datetime.utcnow()

class UserSession(Base, TimestampMixin):
    """User login sessions."""
    
    __tablename__ = "user_sessions"
    
    # Session information
    token = Column(String(255), unique=True, index=True, nullable=False)
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    
    # Session status
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    
    # Relationships
    user_id = Column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False
    )
    user = relationship("User", back_populates="sessions")
    
    @property
    def is_expired(self) -> bool:
        """Check if the session has expired."""
        return datetime.utcnow() > self.expires_at
    
    @classmethod
    def create_session(
        cls,
        user_id: int,
        token: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        expires_in_days: int = 30
    ) -> 'UserSession':
        """Create a new user session."""
        return cls(
            user_id=user_id,
            token=token,
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=datetime.utcnow() + timedelta(days=expires_in_days)
        )

# Event listeners
@event.listens_for(User, 'before_insert')
def hash_user_password(mapper, connection, user):
    """Hash the user's password before inserting into the database."""
    if hasattr(user, 'password'):
        user.set_password(user.password)
        delattr(user, 'password')  # Remove the plain password

@event.listens_for(User, 'before_update')
def update_timestamp_before_update(mapper, connection, user):
    """Update the updated_at timestamp before updating a user."""
    user.updated_at = datetime.utcnow()
    
    # If password was updated, hash it
    if hasattr(user, 'password'):
        user.set_password(user.password)
        delattr(user, 'password')  # Remove the plain password
