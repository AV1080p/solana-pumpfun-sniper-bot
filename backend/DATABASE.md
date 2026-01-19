# Database Management Guide

This document provides comprehensive information about the database management system for the Tourist App backend.

## Overview

The application uses **PostgreSQL** as the primary database with:
- SQLAlchemy ORM for database operations
- Alembic for database migrations
- Connection pooling for optimal performance
- Comprehensive database management utilities

## Quick Start

### 1. Set Up PostgreSQL

#### Option A: Using Docker Compose (Recommended)

```bash
# Start PostgreSQL container
docker-compose -f docker-compose.db.yml up -d

# The database will be available at:
# Host: localhost
# Port: 5432
# Database: tourist_db
# User: postgres
# Password: postgres
```

#### Option B: Local PostgreSQL Installation

1. Install PostgreSQL on your system
2. Create a database:
   ```sql
   CREATE DATABASE tourist_db;
   CREATE USER tourist_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE tourist_db TO tourist_user;
   ```

### 2. Configure Environment Variables

Copy `env.example` to `.env` and update the database URL:

```bash
cp env.example .env
```

Edit `.env` and set:
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/tourist_db
```

### 3. Initialize Database

#### Using the CLI:
```bash
python init_db.py --seed
```

#### Using Alembic (Recommended for production):
```bash
# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

#### Using the database CLI:
```bash
python db_cli.py init
python db_cli.py stats
```

## Database Management

### Database CLI

The `db_cli.py` script provides a command-line interface for database operations:

```bash
# Initialize database
python db_cli.py init [--drop]

# Create backup
python db_cli.py backup [--name custom_backup_name]

# Restore from backup
python db_cli.py restore backup_path [--drop]

# List all backups
python db_cli.py list-backups

# Show database statistics
python db_cli.py stats

# Health check
python db_cli.py health

# Optimize database
python db_cli.py optimize
```

### Database Utilities (Python API)

You can also use the database utilities programmatically:

```python
from db_utils import DatabaseManager

manager = DatabaseManager()

# Initialize database
result = manager.initialize_database(drop_existing=False)

# Create backup
backup = manager.backup_database()

# Get statistics
stats = manager.get_table_stats()

# Health check
health = manager.health_check()
```

## Database Migrations

### Using Alembic

Alembic is configured for managing database schema changes:

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show migration history
alembic history

# Show current revision
alembic current
```

### Migration Best Practices

1. **Always review auto-generated migrations** before applying them
2. **Test migrations on a development database first**
3. **Create backups before running migrations in production**
4. **Use descriptive migration messages**
5. **Never edit existing migrations** - create new ones instead

## Database Models

### Tour
- Stores tour information (name, description, price, location, etc.)
- Has relationships with Bookings

### Booking
- Stores booking information
- Linked to Tours and Payments
- Uses enum for status (PENDING, CONFIRMED, CANCELLED, COMPLETED)

### Payment
- Stores payment transactions
- Supports multiple payment methods (Stripe, Solana, Bitcoin, Ethereum)
- Uses enum for status (PENDING, PROCESSING, COMPLETED, FAILED, REFUNDED, CANCELLED)

## Connection Pooling

The database connection uses SQLAlchemy's connection pooling:

- **Pool Size**: Number of connections maintained (default: 10)
- **Max Overflow**: Additional connections beyond pool size (default: 20)
- **Pool Timeout**: Seconds to wait for a connection (default: 30)
- **Pool Recycle**: Seconds before recycling a connection (default: 3600)

Configure these in `.env`:
```env
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
```

## Backup and Restore

### Creating Backups

```bash
# Automatic backup with timestamp
python db_cli.py backup

# Custom backup name
python db_cli.py backup --name my_backup.sql
```

Backups are stored in the `backups/` directory.

### Restoring Backups

```bash
# Restore from backup
python db_cli.py restore backups/backup_20240101_120000.sql

# Restore and drop existing objects
python db_cli.py restore backups/backup_20240101_120000.sql --drop
```

### Listing Backups

```bash
python db_cli.py list-backups
```

## Health Monitoring

### Health Check Endpoint

The API provides health check endpoints:

```bash
# Basic health check
curl http://localhost:8000/health

# Comprehensive database health check
curl http://localhost:8000/health/database

# Database information
curl http://localhost:8000/database/info

# Database statistics
curl http://localhost:8000/database/stats

# Connection pool statistics
curl http://localhost:8000/database/pool-stats
```

### Health Check Response

```json
{
  "timestamp": "2024-01-01T12:00:00",
  "healthy": true,
  "connection": true,
  "database_info": {
    "status": "connected",
    "type": "PostgreSQL",
    "version": "PostgreSQL 15.0",
    "database": "tourist_db",
    "user": "postgres"
  },
  "pool_stats": {
    "pool_size": 10,
    "checked_in": 8,
    "checked_out": 2,
    "overflow": 0
  },
  "table_stats": {
    "tables": {
      "tours": {"row_count": 6, "size": "64 kB"},
      "bookings": {"row_count": 10, "size": "32 kB"},
      "payments": {"row_count": 5, "size": "16 kB"}
    }
  }
}
```

## Database Optimization

### Automatic Optimization

```bash
python db_cli.py optimize
```

This runs `VACUUM ANALYZE` on PostgreSQL to:
- Reclaim storage space
- Update table statistics for query planner
- Improve query performance

### Manual Optimization

For PostgreSQL, you can also run optimization manually:

```sql
-- Analyze all tables
ANALYZE;

-- Vacuum and analyze specific table
VACUUM ANALYZE tours;

-- Full vacuum (requires exclusive lock)
VACUUM FULL;
```

## Troubleshooting

### Connection Issues

1. **Check database is running**:
   ```bash
   docker ps  # If using Docker
   pg_isready -h localhost -p 5432  # If using local PostgreSQL
   ```

2. **Verify connection string**:
   ```bash
   # Test connection
   psql postgresql://user:password@localhost:5432/tourist_db
   ```

3. **Check connection pool**:
   ```bash
   curl http://localhost:8000/database/pool-stats
   ```

### Migration Issues

1. **Check current migration status**:
   ```bash
   alembic current
   alembic history
   ```

2. **Resolve migration conflicts**:
   ```bash
   # Show pending migrations
   alembic heads
   
   # Merge branches if needed
   alembic merge -m "Merge branches" head1 head2
   ```

### Performance Issues

1. **Check table statistics**:
   ```bash
   python db_cli.py stats
   ```

2. **Optimize database**:
   ```bash
   python db_cli.py optimize
   ```

3. **Monitor connection pool**:
   ```bash
   curl http://localhost:8000/database/pool-stats
   ```

## Production Considerations

1. **Use connection pooling** - Already configured
2. **Regular backups** - Set up automated backups
3. **Monitor database health** - Use health check endpoints
4. **Use migrations** - Never modify database schema directly
5. **Index optimization** - Review and add indexes as needed
6. **Connection limits** - Configure PostgreSQL max_connections appropriately
7. **SSL connections** - Use SSL for production database connections

## Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `DB_POOL_SIZE` | Connection pool size | 10 |
| `DB_MAX_OVERFLOW` | Max overflow connections | 20 |
| `DB_POOL_TIMEOUT` | Pool timeout (seconds) | 30 |
| `DB_POOL_RECYCLE` | Connection recycle time (seconds) | 3600 |
| `DB_ECHO` | Log SQL queries | false |

## Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)

