# DEPRECATED - SQLite Models

These files were used for SQLite database setup and are now DEPRECATED:

- `setup_db.py` - SQLite schema creation
- `seed_teams.py` - SQLite team data seeding  
- `create_competition_aware_schema.py` - SQLite competition schema

## Replacement

All database setup is now handled by:
- PostgreSQL schema creation in `migrate_sqlite_to_local_postgres.py`
- Local PostgreSQL via Docker (`docker-compose.local.yml`)
- Production PostgreSQL on Railway

These SQLite scripts are kept for historical reference but should NOT be used.