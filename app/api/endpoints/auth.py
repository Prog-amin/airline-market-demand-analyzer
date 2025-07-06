from datetime import timedelta
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.base import get_db
from app.models.user import User, UserRole
from app.schemas.auth import (
    Token, UserCreate, UserInDB, UserResponse, 
    APIKeyCreate, APIKeyResponse, PasswordResetRequest,
    PasswordReset, UserUpdate
)
from app.services.auth import AuthService
from app.api.deps import get_current_active_user, get_current_active_admin

router = APIRouter()

@router.post("/login/access-token", response_model=Token)
async def login_access_token(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = await AuthService.authenticate_user(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return await AuthService.create_access_token_for_user(user)

@router.post("/login/test-token", response_model=UserResponse)
async def test_token(current_user: User = Depends(get_current_active_user)) -> Any:
    """
    Test access token
    """
    return current_user

@router.post("/register", response_model=UserResponse)
async def register_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """
    Create new user without the need to be logged in
    """
    user = await db.execute(
        select(User).where(User.email == user_in.email)
    )
    if user.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )
    
    return await AuthService.create_user(db=db, user_in=user_in)

@router.get("/me", response_model=UserResponse)
async def read_user_me(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get current user.
    """
    return current_user

@router.patch("/me", response_model=UserResponse)
async def update_user_me(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update own user.
    """
    return await AuthService.update_user(db, current_user.id, user_in, current_user)

@router.post("/password-recovery/{email}", response_model=dict)
async def recover_password(
    email: str,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Password Recovery
    """
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Don't reveal that the user doesn't exist
        return {"message": "If this email is registered, you will receive a password reset link."}
    
    # In a real app, send an email with the password reset link
    # For now, we'll just return a message
    return {"message": "If this email is registered, you will receive a password reset link."}

@router.post("/reset-password/", response_model=dict)
async def reset_password(
    *,
    db: AsyncSession = Depends(get_db),
    body: PasswordReset
) -> Any:
    """
    Reset password
    """
    # In a real app, verify the reset token here
    # For now, we'll just update the password directly
    result = await db.execute(
        select(User).where(User.email == body.email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )
    
    # Update the password
    hashed_password = get_password_hash(body.new_password)
    user.hashed_password = hashed_password
    db.add(user)
    await db.commit()
    
    return {"message": "Password updated successfully"}

@router.post("/api-keys/", response_model=APIKeyResponse)
async def create_api_key(
    *,
    db: AsyncSession = Depends(get_db),
    api_key_in: APIKeyCreate,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Create a new API key for the current user
    """
    return await AuthService.create_api_key(db, current_user.id, api_key_in)

@router.get("/api-keys/", response_model=List[APIKeyResponse])
async def read_api_keys(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get all API keys for the current user
    """
    return await AuthService.get_user_api_keys(db, current_user.id)

@router.delete("/api-keys/{key_id}", response_model=dict)
async def revoke_api_key(
    key_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Revoke an API key
    """
    success = await AuthService.revoke_api_key(db, key_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="API key not found",
        )
    return {"message": "API key revoked successfully"}
