#!/bin/bash
echo "🚀 Starting Local PostgreSQL for Railway Sync"
echo "============================================="

# Start PostgreSQL container
echo "📦 Starting PostgreSQL container..."
docker compose -f docker-compose.local.yml up -d

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to start..."
sleep 10

# Check if running
echo "🔍 Checking container status..."
docker compose -f docker-compose.local.yml ps

echo ""
echo "✅ Local PostgreSQL should now be running!"
echo ""
echo "Next steps:"
echo "1. Run migration: python3 migrate_sqlite_to_local_postgres.py"
echo "2. Verify data: python3 verify_local_data.py"
echo "3. Compare with Railway: python3 compare_environments.py"