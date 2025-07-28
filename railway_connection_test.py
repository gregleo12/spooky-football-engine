#!/usr/bin/env python3
"""
Quick Railway Connection Test
Test Railway PostgreSQL connection before full sync process
"""
import os
import sys
from datetime import datetime

def test_railway_connection():
    """Quick test of Railway PostgreSQL connection"""
    railway_url = os.environ.get('DATABASE_URL')
    
    if not railway_url:
        print("❌ DATABASE_URL not set!")
        print("\nPlease set your Railway PostgreSQL URL:")
        print("  export DATABASE_URL='postgresql://user:password@host:port/database'")
        return False
    
    print(f"🔗 Testing Railway connection...")
    print(f"URL format: {railway_url[:20]}...{railway_url[-20:] if len(railway_url) > 40 else railway_url[20:]}")
    
    try:
        import psycopg2
        conn = psycopg2.connect(railway_url)
        cursor = conn.cursor()
        
        # Test basic connection
        cursor.execute("SELECT version(), current_database(), current_user")
        version, database, user = cursor.fetchone()
        
        print(f"✅ Connection successful!")
        print(f"  Database: {database}")
        print(f"  User: {user}")
        print(f"  Version: {version.split(',')[0]}")
        
        # Quick data check
        try:
            cursor.execute("SELECT COUNT(*) FROM teams")
            team_count = cursor.fetchone()[0]
            print(f"  Teams found: {team_count}")
        except:
            print(f"  Teams table: Not found or empty")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Railway PostgreSQL Connection Test")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    if test_railway_connection():
        print("\n✅ Railway connection ready for sync!")
    else:
        print("\n❌ Fix Railway connection before proceeding")