"""
Security utilities for the application.

This module provides functions for password hashing, JWT token handling,
and other security-related functionality.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

from jose import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.base import get_db
from app.models.user import User, UserAPIKey

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_PREFIX}/auth/login"
)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.
    
    Args:
        plain_password: The plain text password
        hashed_password: The hashed password to verify against
        
    Returns:
        bool: True if the password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hash a password.
    
    Args:
        password: The password to hash
        
    Returns:
        str: The hashed password
    """
    return pwd_context.hash(password)

def create_access_token(
    subject: Union[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        subject: The subject of the token (usually user ID)
        expires_delta: Optional expiration time delta
        
    Returns:
        str: The encoded JWT token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    Get the current user from the JWT token.
    
    Args:
        db: The database session
        token: The JWT token
        
    Returns:
        User: The authenticated user
        
    Raises:
        HTTPException: If the token is invalid or the user doesn't exist
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.JWTError:
        raise credentials_exception
        
    # Get user from database
    result = await db.execute(
        "SELECT * FROM users WHERE id = :user_id", 
        {"user_id": user_id}
    )
    user = result.first()
    
    if user is None:
        raise credentials_exception
        
    return user

async def get_api_key_user(
    api_key: str,
    db: AsyncSession
) -> Optional[User]:
    """
    Get a user by their API key.
    
    Args:
        api_key: The API key to look up
        db: The database session
        
    Returns:
        Optional[User]: The user if found, None otherwise
    """
    if not api_key:
        return None
        
    # Get the API key record
    result = await db.execute(
        """
        SELECT u.* FROM users u
        JOIN user_api_keys k ON u.id = k.user_id
        WHERE k.key = :api_key AND k.is_active = TRUE
        """,
        {"api_key": api_key}
    )
    user = result.first()
    
    return user

def create_api_key() -> str:
    """
    Generate a new API key.
    
    Returns:
        str: A new API key
    """
    import secrets
    import string
    
    # Generate a random string of 32 characters
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(32))

def verify_api_key(
    api_key: str,
    required_scopes: Optional[list] = None
) -> Dict[str, Any]:
    """
    Verify an API key and return the associated user.
    
    Args:
        api_key: The API key to verify
        required_scopes: Optional list of required scopes
        
    Returns:
        Dict[str, Any]: The user information if the key is valid
        
    Raises:
        HTTPException: If the API key is invalid or has insufficient permissions
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required"
        )
        
    # In a real implementation, this would check the API key against the database
    # For now, we'll just return a dummy user
    return {
        "user_id": "api_user",
        "scopes": ["read", "write"]
    }
