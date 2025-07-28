#!/bin/bash
echo "☁️  Phase 2B: Railway PostgreSQL Current State Check"
echo "=================================================="
echo ""

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL not set!"
    echo ""
    echo "Please set your Railway PostgreSQL URL:"
    echo "  export DATABASE_URL='postgresql://user:password@host:port/database'"
    echo ""
    echo "Then run this script again."
    exit 1
fi

echo "✅ DATABASE_URL is set"
echo "🔗 Connecting to Railway PostgreSQL..."
echo ""

# Test Railway connection
echo "📊 Step 1: Testing Railway connection..."
python3 -c "
import os
from database_config import db_config
print(f'Target: {db_config.get_db_info()}')
try:
    conn = db_config.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT version()')
    version = cursor.fetchone()[0]
    print(f'✅ Railway connection successful: {version.split(\",\")[0]}')
    cursor.close()
    conn.close()
except Exception as e:
    print(f'❌ Railway connection failed: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Cannot proceed without Railway connection"
    exit 1
fi

# Check Railway current data state
echo ""
echo "🔍 Step 2: Analyzing Railway current data state..."
python3 verify_railway_data.py

echo ""
echo "📋 Phase 2B Summary:"
echo "- Railway connection: Verified"
echo "- Current data state: Analyzed"
echo ""
echo "✅ Phase 2B complete! Ready for Phase 2C (Environment comparison)"