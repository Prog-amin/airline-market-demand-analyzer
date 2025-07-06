"""
Database management commands.

This module provides a command-line interface for managing the database,
including initialization, migrations, and other database-related tasks.
"""
import argparse
import logging
import os
import sys
from typing import Optional

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings
from app.db.init_db import init_db, drop_db, reset_db, check_db_connection, get_database_url
from app.db.migrate import (
    create_migration, upgrade, downgrade, show_migrations,
    is_database_synced, get_current_revision, get_latest_revision
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def print_status() -> None:
    """Print the current database status."""
    try:
        current = get_current_revision() or "No migrations applied"
        latest = get_latest_revision() or "No migrations found"
        synced = is_database_synced()
        
        print("\n=== Database Status ===")
        print(f"Database URL: {get_database_url()}")
        print(f"Current revision: {current}")
        print(f"Latest revision: {latest}")
        print(f"In sync: {'✅' if synced else '❌'}")
        
        if not synced and current:
            print("\n⚠️  Database is not up to date. Run 'db upgrade' to apply pending migrations.")
        
        print()
    except Exception as e:
        logger.error(f"Error getting database status: {e}")
        sys.exit(1)

def main() -> None:
    """Handle command-line arguments for database management."""
    parser = argparse.ArgumentParser(description="Database management commands")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize the database")
    
    # Drop command
    drop_parser = subparsers.add_parser(
        "drop", 
        help="Drop all database tables (WARNING: deletes all data)"
    )
    
    # Reset command
    reset_parser = subparsers.add_parser(
        "reset", 
        help="Reset the database (drop and recreate all tables, WARNING: deletes all data)"
    )
    
    # Check command
    check_parser = subparsers.add_parser("check", help="Check database connection")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show database status")
    
    # Migration commands
    migration_parser = subparsers.add_parser("migrate", help="Migration commands")
    migration_subparsers = migration_parser.add_subparsers(dest="migration_command")
    
    # Create migration
    migrate_create = migration_subparsers.add_parser("create", help="Create a new migration")
    migrate_create.add_argument(
        "-m", "--message", 
        required=True, 
        help="Description of the migration"
    )
    migrate_create.add_argument(
        "--autogenerate", 
        action="store_true", 
        help="Auto-generate migration code"
    )
    
    # Upgrade
    migrate_up = migration_subparsers.add_parser("upgrade", help="Upgrade the database")
    migrate_up.add_argument(
        "revision", 
        nargs="?", 
        default="head", 
        help="Target revision (default: head)"
    )
    
    # Downgrade
    migrate_down = migration_subparsers.add_parser("downgrade", help="Downgrade the database")
    migrate_down.add_argument("revision", help="Target revision")
    
    # Show migrations
    migration_subparsers.add_parser("show", help="Show migration history")
    
    # Reset migrations
    migration_subparsers.add_parser(
        "reset", 
        help="Reset all migrations (WARNING: drops all data)"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    try:
        # Handle commands
        if args.command == "init":
            init_db()
            print("✅ Database initialized successfully")
        
        elif args.command == "drop":
            confirm = input("⚠️  WARNING: This will delete all data in the database. Continue? (y/N): ")
            if confirm.lower() == 'y':
                drop_db()
                print("✅ Database dropped successfully")
            else:
                print("Operation cancelled")
        
        elif args.command == "reset":
            confirm = input("⚠️  WARNING: This will delete all data in the database. Continue? (y/N): ")
            if confirm.lower() == 'y':
                reset_db()
                print("✅ Database reset successfully")
            else:
                print("Operation cancelled")
        
        elif args.command == "check":
            if check_db_connection():
                print("✅ Database connection successful")
            else:
                print("❌ Database connection failed")
                sys.exit(1)
        
        elif args.command == "status":
            print_status()
        
        elif args.command == "migrate":
            if args.migration_command == "create":
                create_migration(args.message, args.autogenerate)
                print("✅ Migration created successfully")
            
            elif args.migration_command == "upgrade":
                upgrade(args.revision)
                print(f"✅ Database upgraded to revision: {args.revision}")
            
            elif args.migration_command == "downgrade":
                downgrade(args.revision)
                print(f"✅ Database downgraded to revision: {args.revision}")
            
            elif args.migration_command == "show":
                show_migrations()
            
            elif args.migration_command == "reset":
                from app.db.migrate import reset_migrations
                reset_migrations()
            
            else:
                migration_parser.print_help()
        
        else:
            parser.print_help()
            print("\nCurrent status:")
            print_status()
    
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
