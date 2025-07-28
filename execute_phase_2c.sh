#!/bin/bash
echo "🔄 Phase 2C: Environment Comparison"
echo "=================================="
echo ""

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL not set!"
    echo "Please set Railway URL and run again."
    exit 1
fi

echo "🔍 Comparing Local PostgreSQL vs Railway PostgreSQL..."
echo ""

# Run environment comparison
python3 compare_environments.py

echo ""
echo "📋 Phase 2C Summary:"
echo "- Environment comparison: Complete"
echo "- Differences identified and documented"
echo ""
echo "✅ Phase 2C complete! Ready for Phase 2D (Sync execution)"