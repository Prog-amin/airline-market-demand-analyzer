"""
Dependencies for the API.

This module contains FastAPI dependencies that can be used across multiple endpoints.
"""
from typing import Optional, Generator, Union

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.security import oauth2_scheme, get_api_key_user
from app.db.base import get_db
from app.models.user import User, UserRole
from app.schemas.auth import TokenData, UserResponse

# OAuth2 scheme for token authentication
security = HTTPBearer()

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Get the current authenticated user from the JWT token.
    
    Args:
        db: The database session
        credentials: The HTTP Authorization credentials
        
    Returns:
        User: The authenticated user
        
    Raises:
        HTTPException: If the token is invalid or the user is not found
    """
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=["HS256"]
        )
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except (jwt.JWTError, ValidationError):
        raise credentials_exception
    
    # Get user from database
    result = await db.execute(select(User).where(User.id == token_data.user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
        
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current active user.
    
    Args:
        current_user: The current authenticated user
        
    Returns:
        User: The active user
        
    Raises:
        HTTPException: If the user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_active_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get the current active admin user.
    
    Args:
        current_user: The current authenticated user
        
    Returns:
        User: The admin user
        
    Raises:
        HTTPException: If the user is not an admin
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user

def get_api_key_optional(
    api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> Optional[str]:
    """
    Get the API key from the header if provided.
    
    Args:
        api_key: The API key from the header
        
    Returns:
        Optional[str]: The API key if provided, None otherwise
    """
    return api_key

async def get_optional_user(
    db: AsyncSession = Depends(get_db),
    api_key: Optional[str] = Depends(get_api_key_optional),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security, use_cache=False)
) -> Optional[User]:
    """
    Get the current user if authenticated, otherwise return None.
    
    This is useful for endpoints that should work for both authenticated and
    unauthenticated users, but need to know who's making the request if they are
    authenticated.
    
    Args:
        db: The database session
        api_key: Optional API key from the header
        credentials: Optional HTTP Authorization credentials
        
    Returns:
        Optional[User]: The authenticated user if credentials are valid, None otherwise
    """
    # Try to authenticate with API key first
    if api_key:
        return await get_api_key_user(api_key, db)
    
    # Then try with JWT token
    if credentials:
        try:
            return await get_current_user(db, credentials)
        except HTTPException:
            pass
    
    return None
