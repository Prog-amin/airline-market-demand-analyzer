# Database Management

This document provides information about the database setup, migrations, and management for the Airline Market Demand Web App.

## Database Setup

The application uses PostgreSQL as the primary database. The database connection is configured via environment variables (see `.env` file).

### Prerequisites

- PostgreSQL 12+
- Python 3.8+
- Required Python packages (install with `pip install -r requirements.txt`)

## Database Models

The application uses SQLAlchemy ORM for database operations. The main models are:

- `User`: User accounts and authentication
- `UserAPIKey`: API keys for programmatic access
- `UserSession`: Active user sessions
- `Airport`: Airport information
- `Flight`: Flight schedules and availability
- `Booking`: Flight bookings
- `MarketData`: Aggregated market demand data

## Database Migrations

The application uses Alembic for database migrations. Migrations are stored in the `alembic/versions` directory.

### Migration Commands

Use the `scripts/db.py` script to manage database migrations:

```bash
# Show database status
python scripts/db.py status

# Create a new migration (auto-generate)
python scripts/db.py migrate create -m "Your migration message" --autogenerate

# Upgrade to the latest migration
python scripts/db.py migrate upgrade

# Downgrade to a specific revision
python scripts/db.py migrate downgrade <revision>

# Show migration history
python scripts/db.py migrate show

# Reset all migrations (WARNING: drops all data)
python scripts/db.py migrate reset
```

### Creating Migrations

1. Make changes to your models in `app/models/`
2. Create a new migration:
   ```bash
   python scripts/db.py migrate create -m "Your descriptive message" --autogenerate
   ```
3. Review the generated migration script in `alembic/versions/`
4. Run the migration:
   ```bash
   python scripts/db.py migrate upgrade
   ```

## Database Initialization

### Development

For development, you can initialize the database with test data:

```bash
# Initialize the database (creates tables)
python scripts/db.py init

# Reset the database (WARNING: drops all data)
python scripts/db.py reset
```

### Production

In production, always use migrations:

```bash
# Apply all pending migrations
python scripts/db.py migrate upgrade
```

## Database Backups

It's recommended to set up regular database backups in production. You can use PostgreSQL's built-in tools:

```bash
# Create a backup
pg_dump -U username -d dbname > backup_$(date +%Y%m%d).sql

# Restore from backup
psql -U username -d dbname < backup_file.sql
```

## Connection Pooling

The application uses SQLAlchemy's connection pooling with these settings:

- `pool_size`: 20 connections
- `max_overflow`: 10 additional connections when pool is full
- `pool_recycle`: 1 hour (connections are recycled after this time)

Adjust these values in `app/db/session.py` based on your application's needs.

## Troubleshooting

### Database Connection Issues

1. Check if PostgreSQL is running
2. Verify the connection string in your `.env` file
3. Check the PostgreSQL logs for errors

### Migration Issues

If you encounter issues with migrations:

1. Check the Alembic version table: `SELECT * FROM alembic_version;`
2. Manually fix any issues in the database if needed
3. Consider creating a new migration with `--autogenerate` to sync the database state

## Best Practices

1. Always create a new migration for schema changes
2. Test migrations in a development environment first
3. Backup the database before running migrations in production
4. Keep migration files in version control
5. Write idempotent migration scripts that can be run multiple times safely
