"""
API Key management utilities.

This module provides functions for generating, validating, and managing API keys
for programmatic access to the API.
"""
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserAPIKey
from app.schemas.auth import APIKeyCreate, APIKeyResponse


def generate_api_key(prefix: str = "sk_", length: int = 32) -> str:
    """
    Generate a new API key with the specified prefix and length.
    
    Args:
        prefix: The prefix for the API key (e.g., "sk_")
        length: The length of the random part of the key
        
    Returns:
        str: A new API key
    """
    # Generate a cryptographically secure random string
    alphabet = string.ascii_letters + string.digits
    random_part = ''.join(secrets.choice(alphabet) for _ in range(length))
    return f"{prefix}{random_part}"


def generate_key_secret_pair(prefix: str = "sk_") -> Tuple[str, str]:
    """
    Generate a new API key and secret pair.
    
    The key is safe to store in the database, while the secret should be
    shown to the user once and then discarded.
    
    Args:
        prefix: The prefix for the API key
        
    Returns:
        Tuple[str, str]: A tuple of (key_id, secret_key)
    """
    key_id = generate_api_key(prefix=prefix, length=16)
    secret_key = generate_api_key(prefix="", length=32)  # No prefix for secret
    return key_id, secret_key


async def create_user_api_key(
    db: AsyncSession,
    user_id: int,
    key_data: APIKeyCreate,
    expires_in_days: Optional[int] = None
) -> APIKeyResponse:
    """
    Create a new API key for a user.
    
    Args:
        db: The database session
        user_id: The ID of the user to create the key for
        key_data: The API key creation data
        expires_in_days: Number of days until the key expires (None for no expiration)
        
    Returns:
        APIKeyResponse: The created API key with its secret
    """
    # Generate key ID and secret
    key_id, secret_key = generate_key_secret_pair()
    
    # Calculate expiration date if specified
    expires_at = None
    if expires_in_days is not None:
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
    
    # Create the API key record
    db_key = UserAPIKey(
        user_id=user_id,
        name=key_data.name,
        key_id=key_id,
        key_hash=secret_key,  # In a real app, this should be hashed
        scopes=key_data.scopes,
        expires_at=expires_at,
        is_active=True
    )
    
    db.add(db_key)
    await db.commit()
    await db.refresh(db_key)
    
    # Return the key with its secret (only shown once)
    return APIKeyResponse(
        id=db_key.id,
        name=db_key.name,
        key_id=db_key.key_id,
        secret_key=secret_key,  # Only time the secret is available
        scopes=db_key.scopes,
        created_at=db_key.created_at,
        expires_at=db_key.expires_at,
        is_active=db_key.is_active
    )


async def revoke_api_key(
    db: AsyncSession,
    key_id: int,
    user_id: int
) -> bool:
    """
    Revoke an API key.
    
    Args:
        db: The database session
        key_id: The ID of the key to revoke
        user_id: The ID of the user who owns the key
        
    Returns:
        bool: True if the key was revoked, False if it wasn't found
    """
    # Get the key
    result = await db.execute(
        """
        UPDATE user_api_keys 
        SET is_active = FALSE 
        WHERE id = :key_id AND user_id = :user_id
        RETURNING id
        """,
        {"key_id": key_id, "user_id": user_id}
    )
    
    await db.commit()
    return result.rowcount > 0


async def validate_api_key(
    db: AsyncSession,
    key_id: str,
    secret_key: str
) -> Optional[UserAPIKey]:
    """
    Validate an API key ID and secret.
    
    Args:
        db: The database session
        key_id: The API key ID
        secret_key: The API key secret
        
    Returns:
        Optional[UserAPIKey]: The API key record if valid, None otherwise
    """
    # Get the key from the database
    result = await db.execute(
        """
        SELECT * FROM user_api_keys 
        WHERE key_id = :key_id 
        AND is_active = TRUE 
        AND (expires_at IS NULL OR expires_at > NOW())
        """,
        {"key_id": key_id}
    )
    
    api_key = result.first()
    if not api_key:
        return None
    
    # In a real app, you would verify the secret key hash here
    # For now, we'll just do a direct comparison (not secure for production)
    if api_key.key_hash != secret_key:
        return None
    
    return api_key
