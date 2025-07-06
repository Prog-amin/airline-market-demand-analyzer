"""
Database session configuration for Supabase PostgreSQL.
"""
import ssl
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, Dict, Any

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy.engine.url import URL

from app.core.config import settings

def get_database_url() -> str:
    """
    Get the database URL with asyncpg driver and proper SSL configuration.
    
    Returns:
        str: Database connection URL with SSL settings
    """
    # If DATABASE_URL is already set with proper scheme, use it directly
    if settings.DATABASE_URL and settings.DATABASE_URL.startswith(("postgresql+asyncpg://", "postgresql://")):
        return str(settings.DATABASE_URL)
    
    # Build connection parameters
    ssl_mode = "require" if settings.ENVIRONMENT == "production" else "prefer"
    
    # Create URL with query parameters
    return str(
        URL.create(
            drivername="postgresql+asyncpg",
            username=settings.SUPABASE_USER or settings.POSTGRES_USER,
            password=settings.SUPABASE_PASSWORD or settings.POSTGRES_PASSWORD,
            host=settings.SUPABASE_HOST or settings.POSTGRES_SERVER,
            port=int(settings.SUPABASE_PORT) if settings.SUPABASE_PORT else 5432,
            database=settings.SUPABASE_DB or settings.POSTGRES_DB,
            query={"sslmode": ssl_mode}
        )
    )

def get_engine_options() -> Dict[str, Any]:
    """
    Get SQLAlchemy engine options with SSL configuration.
    
    Returns:
        Dict: Engine configuration options
    """
    ssl_ctx = None
    if settings.ENVIRONMENT == "production":
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
    
    return {
        "echo": settings.DEBUG,
        "future": True,
        "pool_pre_ping": True,
        "pool_size": 5,  # Reduced for Supabase connection limits
        "max_overflow": 10,
        "pool_recycle": 300,  # 5 minutes
        "pool_timeout": 30,  # seconds
        "poolclass": NullPool if settings.TESTING else QueuePool,
        "connect_args": {
            "ssl": ssl_ctx,
            "server_settings": {
                "application_name": "airline_market_backend",
                "timezone": "UTC"
            }
        } if ssl_ctx else {
            "server_settings": {
                "application_name": "airline_market_backend",
                "timezone": "UTC"
            }
        }
    }

# Create async database engine with proper configuration
engine = create_async_engine(
    get_database_url(),
    **get_engine_options()
)

# Create async session factory
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function that yields database sessions.
    
    Yields:
        AsyncSession: Async database session
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Async context manager for database sessions."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
