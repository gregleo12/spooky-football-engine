# Local PostgreSQL Setup Guide

## Quick Start

### 1. Start Local PostgreSQL
```bash
# Start the PostgreSQL container
docker compose -f docker-compose.local.yml up -d

# Verify it's running
docker compose -f docker-compose.local.yml ps
```

### 2. Run Migration (First Time Only)
```bash
# Migrate all data from SQLite to local PostgreSQL
python3 migrate_sqlite_to_local_postgres.py
```

### 3. Test Connection
```bash
# Test database connection
python3 -c "from database_config import db_config; print(db_config.get_db_info())"
```

### 4. Remove SQLite (After Successful Migration)
```bash
# Backup first (just in case)
cp db/football_strength.db db/football_strength.db.backup

# Remove SQLite database
rm db/football_strength.db
```

## Database Architecture

### Local Development (No DATABASE_URL)
- **Database**: Local PostgreSQL in Docker
- **Host**: localhost:5432
- **Database Name**: football_strength
- **User**: football_user
- **Password**: local_dev_password

### Production (DATABASE_URL Set)
- **Database**: Railway PostgreSQL
- **Connection**: Via DATABASE_URL environment variable

## Running Agents

### Local Development
```bash
# Agents will automatically use local PostgreSQL
python3 agents/team_strength/competition_elo_agent.py
```

### Production Updates
```bash
# Set Railway DATABASE_URL first
export DATABASE_URL="your-railway-postgresql-url"
python3 agents/team_strength/competition_elo_agent.py
```

## Docker Commands

### Start PostgreSQL
```bash
docker compose -f docker-compose.local.yml up -d
```

### Stop PostgreSQL
```bash
docker compose -f docker-compose.local.yml down
```

### View Logs
```bash
docker compose -f docker-compose.local.yml logs -f local-postgres
```

### Connect to PostgreSQL CLI
```bash
docker compose -f docker-compose.local.yml exec local-postgres psql -U football_user -d football_strength
```

## Troubleshooting

### Connection Refused
```bash
# Check if container is running
docker compose -f docker-compose.local.yml ps

# Check logs
docker compose -f docker-compose.local.yml logs local-postgres
```

### Migration Fails
- Ensure PostgreSQL container is running
- Check if port 5432 is available
- Verify SQLite database exists at db/football_strength.db

### Agents Can't Connect
- Verify no DATABASE_URL is set for local development
- Check PostgreSQL container is healthy
- Test connection with the test command above