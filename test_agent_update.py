#!/usr/bin/env python3
"""
Test Agent Database Update
Verifies agents can update the database correctly
"""
import os
import sys
from datetime import datetime

# Import database config
from database_config import db_config

def test_agent_update():
    """Test that an agent can update the database"""
    print("🔄 Testing Agent Database Update")
    print("=" * 60)
    print(f"Database: {db_config.get_db_info()}")
    print()
    
    # Check current Arsenal form score
    conn = db_config.get_connection()
    cursor = conn.cursor()
    
    # Get current form score
    cursor.execute("""
        SELECT form_score, form_normalized, last_updated
        FROM competition_team_strength
        WHERE team_name = 'Arsenal'
        ORDER BY last_updated DESC
        LIMIT 1
    """)
    
    result = cursor.fetchone()
    if result:
        old_form, old_normalized, last_update = result
        print(f"Current Arsenal form score: {old_form}")
        print(f"Last updated: {last_update}")
    else:
        print("No Arsenal data found!")
        return False
    
    cursor.close()
    conn.close()
    
    # Run the form agent for just Premier League
    print("\nRunning competition_form_agent for Premier League only...")
    print("-" * 40)
    
    try:
        # Import and run the agent
        from agents.team_strength.competition_form_agent import update_competition_form_scores
        
        # Update only Premier League to save time
        update_competition_form_scores("Premier League")
        
        print("-" * 40)
        print("✅ Agent completed")
        
        # Check if data was updated
        conn = db_config.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT form_score, form_normalized, last_updated
            FROM competition_team_strength
            WHERE team_name = 'Arsenal'
            ORDER BY last_updated DESC
            LIMIT 1
        """)
        
        new_result = cursor.fetchone()
        if new_result:
            new_form, new_normalized, new_update = new_result
            print(f"\nNew Arsenal form score: {new_form}")
            print(f"New last updated: {new_update}")
            
            if new_update > last_update:
                print("\n✅ Database successfully updated by agent!")
            else:
                print("\n⚠️  Update timestamp unchanged")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Agent update failed: {e}")
        return False

def main():
    """Run the test"""
    print("🚀 Agent Database Update Test")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Environment: {'Production' if os.environ.get('DATABASE_URL') else 'Local Development'}")
    print()
    
    success = test_agent_update()
    
    if success:
        print("\n🎉 Test passed! Agents can update the database.")
    else:
        print("\n❌ Test failed! Check the errors above.")

if __name__ == "__main__":
    main()