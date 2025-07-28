#!/usr/bin/env python3
"""
Test Database Connections
Verifies both local PostgreSQL and Railway PostgreSQL work correctly
"""
import os
import sys
from datetime import datetime

# Import database config
from database_config import db_config

def test_connection():
    """Test current database connection"""
    print("🔍 Testing Database Connection")
    print("=" * 60)
    
    # Show current configuration
    print(f"Database Type: {db_config.get_db_type()}")
    print(f"Connection Info: {db_config.get_db_info()}")
    print(f"DATABASE_URL set: {'Yes' if os.environ.get('DATABASE_URL') else 'No'}")
    print()
    
    try:
        # Test basic connection
        conn = db_config.get_connection()
        cursor = conn.cursor()
        
        # Test PostgreSQL version
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"✅ Connected successfully!")
        print(f"PostgreSQL Version: {version.split(',')[0]}")
        print()
        
        # Test data exists
        cursor.execute("SELECT COUNT(*) FROM teams")
        team_count = cursor.fetchone()[0]
        print(f"Teams in database: {team_count}")
        
        cursor.execute("SELECT COUNT(*) FROM competitions")
        comp_count = cursor.fetchone()[0]
        print(f"Competitions in database: {comp_count}")
        
        cursor.execute("SELECT COUNT(*) FROM competition_team_strength")
        strength_count = cursor.fetchone()[0]
        print(f"Team strength records: {strength_count}")
        print()
        
        # Test Arsenal data specifically
        cursor.execute("""
            SELECT team_name, local_league_strength, european_strength,
                   elo_score, squad_value_score
            FROM competition_team_strength
            WHERE team_name = 'Arsenal'
            LIMIT 1
        """)
        
        arsenal = cursor.fetchone()
        if arsenal:
            print("📊 Arsenal Data Check:")
            print(f"  Team: {arsenal[0]}")
            print(f"  Local Strength: {arsenal[1]:.1f}")
            print(f"  European Strength: {arsenal[2]:.1f}")
            print(f"  ELO Score: {arsenal[3]:.1f}")
            print(f"  Squad Value: €{arsenal[4]:.0f}M")
        else:
            print("⚠️  No Arsenal data found")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_agent_compatibility():
    """Test that agents can use the database"""
    print("\n🤖 Testing Agent Compatibility")
    print("=" * 60)
    
    try:
        # Import an agent to test
        from agents.team_strength.competition_elo_agent import get_competition_teams
        
        conn = db_config.get_connection()
        
        # Get Premier League competition ID
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM competitions WHERE name = 'Premier League'")
        result = cursor.fetchone()
        
        if result:
            comp_id = result[0]
            teams = get_competition_teams(comp_id, conn)
            print(f"✅ Agent function works! Found {len(teams)} Premier League teams")
        else:
            print("⚠️  Premier League competition not found")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Agent compatibility test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Football Database Connection Test")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test connection
    connection_ok = test_connection()
    
    # Test agent compatibility
    agent_ok = test_agent_compatibility()
    
    # Summary
    print("\n📋 Test Summary")
    print("=" * 60)
    print(f"Database Connection: {'✅ PASS' if connection_ok else '❌ FAIL'}")
    print(f"Agent Compatibility: {'✅ PASS' if agent_ok else '❌ FAIL'}")
    
    if connection_ok and agent_ok:
        print("\n🎉 All tests passed! Database is ready for use.")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
    
    # Instructions for switching environments
    print("\n💡 To test different environments:")
    print("  Local PostgreSQL: unset DATABASE_URL")
    print("  Railway PostgreSQL: export DATABASE_URL='your-railway-url'")

if __name__ == "__main__":
    main()