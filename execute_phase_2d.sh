#!/bin/bash
echo "🚀 Phase 2D: Sync Data to Railway"
echo "================================="
echo ""

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL not set!"
    echo "Please set Railway URL and run again."
    exit 1
fi

echo "☁️  Syncing all data to Railway PostgreSQL..."
echo "⚠️  This will run all agents and may take several minutes"
echo ""

# Confirmation prompt
read -p "Proceed with Railway sync? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Sync cancelled."
    exit 0
fi

echo ""
echo "🤖 Starting agent sync process..."

# Run the sync
python3 sync_to_railway.py

echo ""
echo "📋 Phase 2D Summary:"
echo "- Agent sync execution: Complete"
echo "- Railway data updated with fresh values"
echo ""
echo "✅ Phase 2D complete! Ready for Phase 2E (Final verification)"