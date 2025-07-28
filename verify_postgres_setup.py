#!/usr/bin/env python3
"""
Verify PostgreSQL Setup
Quick check that everything is configured correctly
"""
import os
import sys
import psycopg2
from database_config import db_config

def check_local_postgres():
    """Check if local PostgreSQL is accessible"""
    print("🐘 Checking Local PostgreSQL Setup")
    print("=" * 60)
    
    # Force local connection (no DATABASE_URL)
    saved_url = os.environ.get('DATABASE_URL')
    if saved_url:
        del os.environ['DATABASE_URL']
    
    try:
        print("Attempting connection to local PostgreSQL...")
        print(f"  Host: localhost")
        print(f"  Port: 5432")
        print(f"  Database: football_strength")
        print(f"  User: football_user")
        
        conn = psycopg2.connect(
            host='localhost',
            port='5432',
            database='football_strength',
            user='football_user',
            password='local_dev_password'
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        
        print("\n✅ Local PostgreSQL is running and accessible!")
        
        # Test through database_config
        test_conn = db_config.get_connection()
        test_conn.close()
        print("✅ database_config.py can connect to local PostgreSQL!")
        
        return True
        
    except psycopg2.OperationalError as e:
        print(f"\n❌ Cannot connect to local PostgreSQL: {e}")
        print("\n💡 To fix:")
        print("1. Make sure Docker is running")
        print("2. Start PostgreSQL container:")
        print("   docker compose -f docker-compose.local.yml up -d")
        print("3. Wait a few seconds for PostgreSQL to start")
        print("4. Try again")
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False
        
    finally:
        # Restore DATABASE_URL if it was set
        if saved_url:
            os.environ['DATABASE_URL'] = saved_url

def check_data_exists():
    """Check if database has data"""
    print("\n📊 Checking Database Content")
    print("=" * 60)
    
    try:
        conn = db_config.get_connection()
        cursor = conn.cursor()
        
        # Check tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        print(f"Tables found: {len(tables)}")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"  - {table[0]}: {count} records")
        
        cursor.close()
        conn.close()
        
        if len(tables) == 0:
            print("\n⚠️  No tables found! Run migration:")
            print("   python3 migrate_sqlite_to_local_postgres.py")
            return False
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error checking data: {e}")
        return False

def main():
    """Run all checks"""
    print("🚀 PostgreSQL Setup Verification")
    print()
    
    # Check local PostgreSQL
    local_ok = check_local_postgres()
    
    if local_ok:
        # Check data exists
        data_ok = check_data_exists()
        
        if data_ok:
            print("\n✅ Everything is set up correctly!")
            print("\nYou can now:")
            print("1. Run agents locally (they'll use local PostgreSQL)")
            print("2. Test with: python3 test_database_connections.py")
            print("3. Update data with: python3 agents/team_strength/competition_elo_agent.py")
        else:
            print("\n⚠️  PostgreSQL is running but has no data")
            print("Run: python3 migrate_sqlite_to_local_postgres.py")
    else:
        print("\n❌ Please fix PostgreSQL connection first")

if __name__ == "__main__":
    main()