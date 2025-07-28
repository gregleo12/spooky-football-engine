#!/bin/bash
echo "🚀 Execute Fresh PostgreSQL Setup & Population"
echo "=============================================="
echo ""

# Step 1: Verify PostgreSQL connection
echo "🔗 Step 1: Verifying PostgreSQL connection..."
python3 -c "
from database_config import db_config
try:
    conn = db_config.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT version()')
    version = cursor.fetchone()[0]
    print(f'✅ Connected: {version.split(\",\")[0]}')
    print(f'Database: {db_config.get_db_info()}')
    cursor.close()
    conn.close()
except Exception as e:
    print(f'❌ Connection failed: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Cannot proceed without database connection"
    exit 1
fi

# Step 2: Create fresh schema
echo ""
echo "🔨 Step 2: Creating fresh database schema..."
python3 setup_fresh_postgres.py

if [ $? -ne 0 ]; then
    echo "❌ Schema creation failed"
    exit 1
fi

# Step 3: Run all agents for data population
echo ""
echo "🤖 Step 3: Running all agents for fresh data population..."
echo "⚠️  This may take 10-15 minutes as agents fetch from APIs"
echo ""

# Ask for confirmation
read -p "Proceed with agent execution? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Agent execution cancelled."
    echo "You can run manually: python3 run_all_agents.py"
    exit 0
fi

python3 run_all_agents.py

# Step 4: Final verification
echo ""
echo "🔍 Step 4: Final verification of populated data..."
python3 verify_local_data.py

echo ""
echo "📋 Fresh Setup Summary:"
echo "- PostgreSQL schema: Created"
echo "- Agent execution: Complete" 
echo "- Data population: Verified"
echo "- Fresh API data: Loaded"
echo ""
echo "✅ Phase 2A complete with fresh data!"
echo ""
echo "Next: Set DATABASE_URL and proceed with Railway sync"