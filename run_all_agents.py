#!/usr/bin/env python3
"""
Run All Agents for Fresh Data Population
Systematically runs all agents to populate PostgreSQL with fresh API data
"""
import sys
import time
from datetime import datetime
from database_config import db_config

def run_agent_safely(agent_name, agent_function, *args):
    """Run an agent with error handling and timing"""
    print(f"\n🤖 Running {agent_name}...")
    print("-" * 50)
    
    start_time = time.time()
    try:
        result = agent_function(*args)
        elapsed = time.time() - start_time
        print("-" * 50)
        print(f"✅ {agent_name} completed in {elapsed:.1f} seconds")
        return True
    except Exception as e:
        elapsed = time.time() - start_time
        print("-" * 50)
        print(f"❌ {agent_name} failed after {elapsed:.1f} seconds: {e}")
        return False

def populate_teams_first():
    """Populate basic team data before running strength agents"""
    print("👥 Populating Basic Team Data")
    print("=" * 60)
    
    try:
        from agents.data_collection.add_top5_league_teams import populate_all_leagues
        return run_agent_safely("Team Population Agent", populate_all_leagues)
    except ImportError:
        print("⚠️  Team population agent not found - agents will create teams as needed")
        return True

def run_core_agents():
    """Run the 4 core strength agents"""
    print("\n💪 Running Core Strength Agents (4/11)")
    print("=" * 60)
    
    agents_run = 0
    agents_failed = 0
    
    # Core agents
    core_agents = [
        ("ELO Agent", "agents.team_strength.competition_elo_agent", "update_competition_elo_ratings"),
        ("Squad Value Agent", "agents.team_strength.competition_squad_value_agent", "update_competition_squad_values"),
        ("Form Agent", "agents.team_strength.competition_form_agent", "update_competition_form_scores"),
        ("Squad Depth Agent", "agents.team_strength.competition_squad_depth_agent", "update_competition_squad_depth")
    ]
    
    for agent_name, module_name, function_name in core_agents:
        try:
            # Dynamic import
            module = __import__(module_name, fromlist=[function_name])
            agent_function = getattr(module, function_name)
            
            if run_agent_safely(agent_name, agent_function):
                agents_run += 1
            else:
                agents_failed += 1
                
        except ImportError as e:
            print(f"❌ Could not import {agent_name}: {e}")
            agents_failed += 1
    
    return agents_run, agents_failed

def run_advanced_agents():
    """Run the advanced parameter agents"""
    print("\n📈 Running Advanced Parameter Agents (7/11)")
    print("=" * 60)
    
    agents_run = 0
    agents_failed = 0
    
    # Advanced agents
    advanced_agents = [
        ("Goals Data Agent", "agents.team_strength.goals_data_agent", "update_goals_data"),
        ("Home Advantage Agent", "agents.team_strength.context_data_agent", "update_home_advantage"),
        ("Fatigue Factor Agent", "agents.team_strength.fatigue_factor_agent", "update_fatigue_factors"),
        ("Key Player Agent", "agents.team_strength.key_player_availability_agent", "update_key_player_availability"),
        ("Motivation Agent", "agents.team_strength.motivation_factor_agent", "update_motivation_factors"),
        ("Tactical Agent", "agents.team_strength.tactical_matchup_agent", "update_tactical_matchups"),
        ("Enhanced Squad Value", "agents.team_strength.enhanced_squad_value_agent", "update_enhanced_squad_values")
    ]
    
    for agent_name, module_name, function_name in advanced_agents:
        try:
            # Dynamic import
            module = __import__(module_name, fromlist=[function_name])
            agent_function = getattr(module, function_name)
            
            if run_agent_safely(agent_name, agent_function):
                agents_run += 1
            else:
                agents_failed += 1
                
        except (ImportError, AttributeError) as e:
            print(f"⚠️  {agent_name} not available: {e}")
            # Don't count as failed - some agents might not exist yet
    
    return agents_run, agents_failed

def verify_population():
    """Quick verification of data population"""
    print("\n🔍 Verifying Data Population")
    print("=" * 60)
    
    try:
        conn = db_config.get_connection()
        cursor = conn.cursor()
        
        # Basic counts
        cursor.execute("SELECT COUNT(*) FROM teams")
        team_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM competition_team_strength")
        strength_count = cursor.fetchone()[0]
        
        # Parameter completeness
        cursor.execute("""
            SELECT COUNT(*) FROM competition_team_strength 
            WHERE elo_score IS NOT NULL
        """)
        elo_count = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM competition_team_strength 
            WHERE squad_value_score IS NOT NULL
        """)
        value_count = cursor.fetchone()[0]
        
        # Sample team check
        cursor.execute("""
            SELECT team_name, local_league_strength, elo_score, last_updated
            FROM competition_team_strength
            WHERE local_league_strength IS NOT NULL
            ORDER BY local_league_strength DESC
            LIMIT 3
        """)
        top_teams = cursor.fetchall()
        
        print(f"Teams populated: {team_count}")
        print(f"Strength records: {strength_count}")
        print(f"ELO data: {elo_count}/{strength_count}")
        print(f"Squad value data: {value_count}/{strength_count}")
        
        if top_teams:
            print(f"\nTop teams by strength:")
            for team, strength, elo, updated in top_teams:
                print(f"  {team}: {strength:.1f} (ELO: {elo:.1f}) - {updated}")
        
        cursor.close()
        conn.close()
        
        return strength_count > 0
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def main():
    """Main agent execution process"""
    print("🚀 Fresh Data Population with All Agents")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Database: {db_config.get_db_info()}")
    print()
    
    start_time = time.time()
    
    # Step 1: Populate teams
    if not populate_teams_first():
        print("⚠️  Team population had issues, but continuing...")
    
    # Step 2: Run core agents
    core_success, core_failed = run_core_agents()
    
    # Step 3: Run advanced agents  
    advanced_success, advanced_failed = run_advanced_agents()
    
    # Step 4: Verify population
    population_success = verify_population()
    
    # Summary
    total_time = time.time() - start_time
    total_success = core_success + advanced_success
    total_failed = core_failed + advanced_failed
    
    print(f"\n📋 Agent Execution Summary")
    print("=" * 60)
    print(f"Core agents successful: {core_success}/4")
    print(f"Advanced agents successful: {advanced_success}")
    print(f"Total agents failed: {total_failed}")
    print(f"Execution time: {total_time/60:.1f} minutes")
    print(f"Data population: {'✅ Success' if population_success else '❌ Failed'}")
    
    if core_success >= 3 and population_success:
        print(f"\n🎉 Fresh data population successful!")
        print(f"Ready for Railway sync!")
    else:
        print(f"\n⚠️  Some issues occurred. Check logs above.")
        if total_failed > 0:
            print(f"Consider running failed agents individually.")

if __name__ == "__main__":
    main()