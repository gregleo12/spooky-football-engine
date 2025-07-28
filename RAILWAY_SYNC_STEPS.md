# Railway Sync - Step by Step Guide

## Current Status
- ✅ SQLite database exists with current data (3.4MB)
- ✅ All sync tools created and ready
- ⏳ Need to start local PostgreSQL container

## Execute These Steps:

### Step 1: Start Local PostgreSQL
```bash
# Start the PostgreSQL container
docker compose -f docker-compose.local.yml up -d

# Wait for it to start (about 10 seconds)
sleep 10

# Verify it's running
docker compose -f docker-compose.local.yml ps
```

### Step 2: Migrate SQLite to Local PostgreSQL
```bash
# Run the migration script
python3 migrate_sqlite_to_local_postgres.py
```

### Step 3: Verify Local Data
```bash
# Check local PostgreSQL has complete data
python3 verify_local_data.py
```

### Step 4: Compare with Railway (Set DATABASE_URL first)
```bash
# Set your Railway PostgreSQL URL
export DATABASE_URL="your-railway-postgresql-connection-string"

# Compare local vs Railway
python3 compare_environments.py
```

### Step 5: Sync to Railway (if needed)
```bash
# Sync all data to Railway
python3 sync_to_railway.py
```

### Step 6: Final Verification
```bash
# Verify both environments match
python3 compare_environments.py
```

## Expected Results

### After Step 3 (Local Verification):
- Total teams: 96
- Total competitions: 6-8  
- Arsenal strength: ~93.4
- All parameters populated

### After Step 6 (Final Verification):
- Local and Railway data identical
- All sample teams showing same values
- Recent timestamps in both environments

## Troubleshooting

### If PostgreSQL won't start:
```bash
# Check Docker is running
docker --version

# Check if port 5432 is in use
lsof -i :5432

# Force restart
docker compose -f docker-compose.local.yml down
docker compose -f docker-compose.local.yml up -d
```

### If migration fails:
- Ensure PostgreSQL container is healthy
- Check SQLite database exists (it does - 3.4MB)
- Verify no other process using port 5432

### If Railway sync fails:
- Verify DATABASE_URL is correctly set
- Check Railway PostgreSQL is accessible
- Try individual agents if batch fails

## Next Action: 
**Run Step 1 to start local PostgreSQL container**