"""
Database initialization and migration utilities.
"""
import asyncio
import logging
from typing import Optional, List, Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine

from app.core.config import settings
from app.db.base_class import Base
from app.db.session import engine, get_database_url

logger = logging.getLogger(__name__)

async def init_db(engine: AsyncEngine = engine) -> None:
    """
    Initialize the database by creating all tables.
    
    This should be used for development and testing only.
    In production, use migrations instead.
    """
    try:
        logger.info("Creating database tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully.")
    except SQLAlchemyError as e:
        logger.error(f"Error initializing database: {e}")
        raise

async def drop_db(engine: AsyncEngine = engine) -> None:
    """
    Drop all database tables.
    
    WARNING: This will delete all data in the database.
    Only use for development and testing.
    """
    try:
        logger.warning("Dropping all database tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.warning("All database tables dropped.")
    except SQLAlchemyError as e:
        logger.error(f"Error dropping database: {e}")
        raise

async def reset_db(engine: AsyncEngine = engine) -> None:
    """
    Reset the database by dropping and recreating all tables.
    
    WARNING: This will delete all data in the database.
    Only use for development and testing.
    """
    await drop_db(engine)
    await init_db(engine)

async def check_db_connection(engine: AsyncEngine = engine) -> bool:
    """
    Check if the database is accessible.
    
    Returns:
        bool: True if the database is accessible, False otherwise
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError as e:
        logger.error(f"Database connection failed: {e}")
        return False

def get_database_url() -> str:
    """
    Get the database URL from settings.
    
    Returns:
        str: The database URL
    """
    return str(settings.DATABASE_URL)

async def async_main() -> None:
    """Asynchronous entry point for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database management commands")
    parser.add_argument(
        "--init", 
        action="store_true", 
        help="Initialize the database (create tables)"
    )
    parser.add_argument(
        "--drop", 
        action="store_true", 
        help="Drop all database tables (WARNING: deletes all data)"
    )
    parser.add_argument(
        "--reset", 
        action="store_true", 
        help="Reset the database (drop and create all tables)"
    )
    parser.add_argument(
        "--check", 
        action="store_true", 
        help="Check database connection"
    )
    parser.add_argument(
        "--url", 
        action="store_true", 
        help="Display the database URL"
    )
    
    args = parser.parse_args()
    
    if not any([args.init, args.drop, args.reset, args.check, args.url]):
        parser.print_help()
        return
    
    try:
        if args.url:
            print(f"Database URL: {get_database_url()}")
            return
            
        if args.check:
            is_connected = await check_db_connection()
            print(f"Database connection: {'✅ Successful' if is_connected else '❌ Failed'}")
        
        if args.init:
            print("Initializing database...")
            await init_db()
            print("✅ Database initialized successfully")
        
        if args.drop:
            confirm = input("⚠️  WARNING: This will delete ALL data. Are you sure? (y/N): ")
            if confirm.lower() == 'y':
                print("Dropping all tables...")
                await drop_db()
                print("✅ Database dropped successfully")
            else:
                print("Operation cancelled")
        
        if args.reset:
            confirm = input("⚠️  WARNING: This will delete ALL data and recreate the schema. Are you sure? (y/N): ")
            if confirm.lower() == 'y':
                print("Resetting database...")
                await reset_db()
                print("✅ Database reset successfully")
            else:
                print("Operation cancelled")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise

# Synchronous wrapper for backward compatibility
def sync_main() -> None:
    """Synchronous entry point for command-line usage."""
    import asyncio
    asyncio.run(async_main())

if __name__ == "__main__":
    asyncio.run(async_main())
