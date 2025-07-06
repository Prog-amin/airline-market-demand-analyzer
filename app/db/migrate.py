"""
Database migration management commands.

This module provides commands for managing database migrations using Alembic.
"""
import os
import subprocess
import sys
from typing import List, Optional

import alembic.config
from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine

from app.core.config import settings
from app.db.session import engine

# Get the directory containing this file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ALEMBIC_INI = os.path.join(BASE_DIR, "alembic.ini")
ALEMBIC_SCRIPT_LOCATION = os.path.join(BASE_DIR, "alembic")

def get_alembic_config() -> Config:
    """Create and configure an Alembic Config instance."""
    # Create the Alembic configuration
    config = Config(ALEMBIC_INI)
    
    # Set the script location
    config.set_main_option("script_location", ALEMBIC_SCRIPT_LOCATION)
    
    # Set the database URL
    config.set_main_option("sqlalchemy.url", str(settings.DATABASE_URL))
    
    return config

def get_current_revision() -> Optional[str]:
    """Get the current database revision."""
    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        return context.get_current_revision()

def get_latest_revision() -> str:
    """Get the latest revision from the migrations directory."""
    config = get_alembic_config()
    script = alembic.script.ScriptDirectory.from_config(config)
    return script.get_current_head()

def is_database_synced() -> bool:
    """Check if the database is up-to-date with the latest migration."""
    current = get_current_revision()
    latest = get_latest_revision()
    return current == latest if current and latest else False

def create_migration(message: str = None, autogenerate: bool = False) -> None:
    """
    Create a new database migration.
    
    Args:
        message: Description of the migration
        autogenerate: Whether to auto-generate migration code
    """
    config = get_alembic_config()
    
    if autogenerate:
        # Run autogenerate to detect changes
        command.revision(config, message=message, autogenerate=True)
    else:
        # Create an empty migration
        command.revision(config, message=message)

def upgrade(revision: str = "head") -> None:
    """
    Upgrade the database to the specified revision.
    
    Args:
        revision: Target revision (defaults to 'head')
    """
    config = get_alembic_config()
    command.upgrade(config, revision)

def downgrade(revision: str) -> None:
    """
    Downgrade the database to the specified revision.
    
    Args:
        revision: Target revision
    """
    config = get_alembic_config()
    command.downgrade(config, revision)

def show_migrations() -> None:
    """Show the current migration status."""
    config = get_alembic_config()
    command.history(config)

def run_migrations() -> None:
    """Run all pending migrations."""
    upgrade()

def reset_migrations() -> None:
    """Reset all migrations (WARNING: This will drop all data)."""
    print("WARNING: This will drop all data in the database!")
    confirm = input("Are you sure you want to continue? (y/N): ")
    
    if confirm.lower() == 'y':
        # Drop all tables
        from app.db.init_db import drop_db
        drop_db()
        
        # Remove all migration versions
        versions_dir = os.path.join(ALEMBIC_SCRIPT_LOCATION, "versions")
        if os.path.exists(versions_dir):
            for filename in os.listdir(versions_dir):
                if filename.endswith(".py") and filename != "__init__.py":
                    os.remove(os.path.join(versions_dir, filename))
        
        # Create initial migration
        create_migration("Initial migration")
        
        # Run migrations
        upgrade()
        
        print("Database has been reset and migrations recreated.")
    else:
        print("Operation cancelled.")

def main() -> None:
    """Handle command-line arguments for migration management."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database migration management")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Create migration command
    create_parser = subparsers.add_parser("create", help="Create a new migration")
    create_parser.add_argument(
        "-m", "--message", 
        required=True, 
        help="Description of the migration"
    )
    create_parser.add_argument(
        "--autogenerate", 
        action="store_true", 
        help="Auto-generate migration code"
    )
    
    # Upgrade command
    upgrade_parser = subparsers.add_parser("upgrade", help="Upgrade the database")
    upgrade_parser.add_argument(
        "revision", 
        nargs="?", 
        default="head", 
        help="Target revision (default: head)"
    )
    
    # Downgrade command
    downgrade_parser = subparsers.add_parser("downgrade", help="Downgrade the database")
    downgrade_parser.add_argument("revision", help="Target revision")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show migration status")
    
    # Reset command
    reset_parser = subparsers.add_parser(
        "reset", 
        help="Reset all migrations (WARNING: drops all data)"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute the appropriate command
    if args.command == "create":
        create_migration(args.message, args.autogenerate)
    elif args.command == "upgrade":
        upgrade(args.revision)
    elif args.command == "downgrade":
        downgrade(args.revision)
    elif args.command == "status":
        show_migrations()
    elif args.command == "reset":
        reset_migrations()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
