#!/usr/bin/env python3
"""
Sync Local PostgreSQL Data to Railway
Runs all agents against Railway PostgreSQL to ensure data synchronization
"""
import os
import sys
import time
from datetime import datetime
from database_config import db_config

# Import all agents
from agents.team_strength.competition_elo_agent import update_competition_elo_ratings
from agents.team_strength.competition_form_agent import update_competition_form_scores
from agents.team_strength.competition_squad_value_agent import update_competition_squad_values
from agents.team_strength.competition_squad_depth_agent import update_competition_squad_depth

def check_railway_connection():
    """Verify Railway PostgreSQL connection"""
    railway_url = os.environ.get('DATABASE_URL')
    
    if not railway_url:
        print("❌ DATABASE_URL not set!")
        print("\n💡 To sync to Railway:")
        print("   export DATABASE_URL='your-railway-postgresql-url'")
        print("   python3 sync_to_railway.py")
        return False
    
    print(f"✅ DATABASE_URL is set")
    print(f"Database: {db_config.get_db_info()}")
    
    try:
        conn = db_config.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        print("✅ Railway connection successful")
        return True
    except Exception as e:
        print(f"❌ Railway connection failed: {e}")
        return False

def run_agent_with_timing(agent_name, agent_function, *args):
    """Run an agent and time its execution"""
    print(f"\n🤖 Running {agent_name}...")
    print("-" * 40)
    
    start_time = time.time()
    try:
        agent_function(*args)
        elapsed = time.time() - start_time
        print("-" * 40)
        print(f"✅ {agent_name} completed in {elapsed:.1f} seconds")
        return True
    except Exception as e:
        print(f"❌ {agent_name} failed: {e}")
        return False

def sync_all_agents():
    """Run all agents to sync data to Railway"""
    print("\n🔄 Starting Full Agent Sync to Railway")
    print("=" * 60)
    
    agents_run = 0
    agents_failed = 0
    
    # Core agents (most important)
    core_agents = [
        ("ELO Agent", update_competition_elo_ratings),
        ("Form Agent", update_competition_form_scores),
        ("Squad Value Agent", update_competition_squad_values),
        ("Squad Depth Agent", update_competition_squad_depth)
    ]
    
    print("\n📊 Running Core Agents (4 agents):")
    for agent_name, agent_func in core_agents:
        if run_agent_with_timing(agent_name, agent_func):
            agents_run += 1
        else:
            agents_failed += 1
    
    # Additional agents (if available)
    try:
        from agents.team_strength.goals_data_agent import update_goals_data
        from agents.team_strength.context_data_agent import update_home_advantage
        from agents.team_strength.fatigue_factor_agent import update_fatigue_factors
        
        additional_agents = [
            ("Goals Data Agent", update_goals_data),
            ("Home Advantage Agent", update_home_advantage),
            ("Fatigue Factor Agent", update_fatigue_factors)
        ]
        
        print("\n📈 Running Additional Agents:")
        for agent_name, agent_func in additional_agents:
            if run_agent_with_timing(agent_name, agent_func):
                agents_run += 1
            else:
                agents_failed += 1
                
    except ImportError:
        print("\n⚠️  Some additional agents not found (this is OK)")
    
    return agents_run, agents_failed

def verify_sync_results():
    """Quick verification of sync results"""
    print("\n🔍 Verifying Sync Results")
    print("=" * 60)
    
    try:
        conn = db_config.get_connection()
        cursor = conn.cursor()
        
        # Check key metrics
        cursor.execute("SELECT COUNT(*) FROM competition_team_strength")
        total_records = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM competition_team_strength
            WHERE last_updated > CURRENT_TIMESTAMP - INTERVAL '1 hour'
        """)
        recent_updates = cursor.fetchone()[0]
        
        # Sample team check
        cursor.execute("""
            SELECT team_name, local_league_strength, elo_score, last_updated
            FROM competition_team_strength
            WHERE team_name = 'Arsenal'
            ORDER BY last_updated DESC
            LIMIT 1
        """)
        arsenal = cursor.fetchone()
        
        print(f"Total team records: {total_records}")
        print(f"Recently updated: {recent_updates}")
        
        if arsenal:
            print(f"\nArsenal check:")
            print(f"  Strength: {arsenal[1]:.1f}")
            print(f"  ELO: {arsenal[2]:.1f}")
            print(f"  Last updated: {arsenal[3]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def main():
    """Main sync process"""
    print("🚀 Railway PostgreSQL Sync")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check Railway connection
    if not check_railway_connection():
        sys.exit(1)
    
    # Confirm before proceeding
    print("\n⚠️  This will update Railway PostgreSQL with fresh data")
    print("This may take several minutes as agents fetch from APIs")
    response = input("\nProceed with sync? (yes/no): ")
    
    if response.lower() != 'yes':
        print("Sync cancelled.")
        return
    
    # Run all agents
    start_time = time.time()
    agents_run, agents_failed = sync_all_agents()
    total_time = time.time() - start_time
    
    # Verify results
    verify_sync_results()
    
    # Summary
    print("\n📋 Sync Summary")
    print("=" * 60)
    print(f"Agents run successfully: {agents_run}")
    print(f"Agents failed: {agents_failed}")
    print(f"Total time: {total_time/60:.1f} minutes")
    
    if agents_failed == 0:
        print("\n✅ Railway sync completed successfully!")
        print("\nNext steps:")
        print("1. Run compare_environments.py to verify sync")
        print("2. Check web app to see updated data")
    else:
        print("\n⚠️  Some agents failed. Check errors above.")

if __name__ == "__main__":
    main()