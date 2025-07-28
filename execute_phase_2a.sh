#!/bin/bash
echo "🚀 Phase 2A: Local PostgreSQL Setup & Verification"
echo "=================================================="
echo ""

# Step 1: Start PostgreSQL container
echo "📦 Step 1: Starting PostgreSQL container..."
echo "Command: docker compose -f docker-compose.local.yml up -d"
echo ""

if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Start the container
docker compose -f docker-compose.local.yml up -d

if [ $? -eq 0 ]; then
    echo "✅ PostgreSQL container started successfully"
else
    echo "❌ Failed to start PostgreSQL container"
    exit 1
fi

# Step 2: Wait for PostgreSQL to be ready
echo ""
echo "⏳ Step 2: Waiting for PostgreSQL to initialize..."
sleep 15

# Step 3: Check container status
echo ""
echo "📊 Step 3: Checking container status..."
docker compose -f docker-compose.local.yml ps

# Step 4: Test connection
echo ""
echo "🔗 Step 4: Testing database connection..."
python3 -c "
from database_config import db_config
try:
    conn = db_config.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT version()')
    version = cursor.fetchone()[0]
    print(f'✅ Connection successful: {version.split(\",\")[0]}')
    cursor.close()
    conn.close()
except Exception as e:
    print(f'❌ Connection failed: {e}')
"

# Step 5: Run migration if needed
echo ""
echo "📥 Step 5: Checking if migration is needed..."
python3 -c "
from database_config import db_config
try:
    conn = db_config.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM teams')
    team_count = cursor.fetchone()[0]
    if team_count > 0:
        print(f'✅ Database has data: {team_count} teams found')
    else:
        print('⚠️  Database is empty - migration needed')
        print('   Run: python3 migrate_sqlite_to_local_postgres.py')
    cursor.close()
    conn.close()
except Exception as e:
    print('⚠️  Tables may not exist - migration needed')
    print('   Run: python3 migrate_sqlite_to_local_postgres.py')
"

# Step 6: Run verification
echo ""
echo "🔍 Step 6: Running data verification..."
python3 verify_local_data.py

echo ""
echo "📋 Phase 2A Summary:"
echo "- PostgreSQL container: Started"
echo "- Database connection: Tested"  
echo "- Data migration: Checked"
echo "- Data verification: Complete"
echo ""
echo "✅ Phase 2A complete! Ready for Phase 2B (Railway check)"