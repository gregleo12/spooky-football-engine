#!/usr/bin/env python3
"""
Verify Railway PostgreSQL Data
Quick check of Railway database state
"""
import os
from datetime import datetime
from database_config import db_config

def verify_railway():
    """Verify Railway PostgreSQL data"""
    print("☁️  Railway PostgreSQL Data Verification")
    print("=" * 60)
    
    # Check DATABASE_URL
    if not os.environ.get('DATABASE_URL'):
        print("❌ DATABASE_URL not set!")
        print("\nTo check Railway data:")
        print("  export DATABASE_URL='your-railway-postgresql-url'")
        print("  python3 verify_railway_data.py")
        return False
    
    print(f"Database: {db_config.get_db_info()}")
    
    # Run the same verification as local
    try:
        from verify_local_data import verify_local_data
        # This will now check Railway since DATABASE_URL is set
        return verify_local_data()
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run verification"""
    print("🚀 Railway Data Verification")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    if verify_railway():
        print("\n✅ Railway data verification complete!")
    else:
        print("\n❌ Railway verification failed")

if __name__ == "__main__":
    main()