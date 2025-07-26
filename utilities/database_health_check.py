#!/usr/bin/env python3
"""
Database Health Check
Verifies database connectivity and data integrity
"""
import os
import sys
# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Change to parent directory to access db folder
os.chdir(parent_dir)

from database_config import db_config
from datetime import datetime

def check_database_connection():
    """Test database connection"""
    print("🔍 Checking database connection...")
    try:
        conn = db_config.get_connection()
        print(f"✅ Connected to {db_config.get_db_type()}")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def check_table_counts():
    """Check record counts in all tables"""
    print("\n📊 Checking table record counts...")
    tables = ['teams', 'competitions', 'competition_team_strength', 'matches']
    
    try:
        with db_config.get_db_connection() as conn:
            cursor = conn.cursor()
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"   {table}: {count} records")
                except Exception as e:
                    print(f"   {table}: ❌ Error - {e}")
        return True
    except Exception as e:
        print(f"❌ Failed to check tables: {e}")
        return False

def check_data_integrity():
    """Check for common data integrity issues"""
    print("\n🔍 Checking data integrity...")
    issues = []
    
    try:
        with db_config.get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check for orphaned strength records
            cursor.execute("""
                SELECT COUNT(*) FROM competition_team_strength cts
                WHERE NOT EXISTS (SELECT 1 FROM teams t WHERE t.id = cts.team_id)
            """)
            orphaned = cursor.fetchone()[0]
            if orphaned > 0:
                issues.append(f"Found {orphaned} orphaned team strength records")
            
            # Check for teams without strength data
            cursor.execute("""
                SELECT COUNT(*) FROM teams t
                WHERE NOT EXISTS (
                    SELECT 1 FROM competition_team_strength cts 
                    WHERE cts.team_id = t.id
                )
            """)
            missing = cursor.fetchone()[0]
            if missing > 0:
                issues.append(f"Found {missing} teams without strength data")
            
            # Check for null strength values
            cursor.execute("""
                SELECT COUNT(*) FROM competition_team_strength
                WHERE overall_strength IS NULL OR local_league_strength IS NULL
            """)
            nulls = cursor.fetchone()[0]
            if nulls > 0:
                issues.append(f"Found {nulls} records with null strength values")
        
        if issues:
            print("⚠️  Data integrity issues found:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        else:
            print("✅ No data integrity issues found")
            return True
            
    except Exception as e:
        print(f"❌ Failed to check data integrity: {e}")
        return False

def check_last_update():
    """Check when data was last updated"""
    print("\n📅 Checking last data update...")
    try:
        with db_config.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT MAX(last_updated) FROM competition_team_strength
                WHERE last_updated IS NOT NULL
            """)
            result = cursor.fetchone()
            if result and result[0]:
                print(f"✅ Last updated: {result[0]}")
                return True
            else:
                print("⚠️  No update timestamp found")
                return False
    except Exception as e:
        print(f"❌ Failed to check last update: {e}")
        return False

def main():
    print("=" * 60)
    print("🏥 DATABASE HEALTH CHECK")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Environment: {db_config.get_db_type()}")
    print("=" * 60)
    
    checks = [
        check_database_connection(),
        check_table_counts(),
        check_data_integrity(),
        check_last_update()
    ]
    
    passed = sum(checks)
    total = len(checks)
    
    print("\n" + "=" * 60)
    print(f"📊 RESULTS: {passed}/{total} checks passed")
    print("=" * 60)
    
    if passed == total:
        print("🎉 Database is healthy!")
        return 0
    else:
        print("⚠️  Some checks failed. Review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())