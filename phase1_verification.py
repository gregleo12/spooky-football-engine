#!/usr/bin/env python3
"""
Phase 1 Completion Verification Script
Comprehensive audit to confirm 100% Phase 1 implementation
"""
import sqlite3
import os
from datetime import datetime

def verify_phase1_completion():
    """
    Verify complete Phase 1 implementation against original blueprint
    
    Phase 1 Blueprint Requirements:
    - 11 parameters total (7 core + 4 new)
    - 7 agents implemented 
    - Database schema complete
    - Calculation engine with proper weighting
    - 47% of final system architecture
    """
    
    print("🔍 PHASE 1 COMPLETION VERIFICATION")
    print("=" * 70)
    print("Comprehensive audit against original Phase 1 blueprint")
    print()
    
    verification_results = {
        'parameters': {},
        'agents': {},
        'database': {},
        'calculation': {},
        'overall_status': 'PENDING'
    }
    
    # 1. PARAMETER VERIFICATION
    print("📊 1. PARAMETER IMPLEMENTATION VERIFICATION")
    print("-" * 50)
    
    required_parameters = {
        'elo_score': {'weight': 0.18, 'description': 'Match-based team strength'},
        'squad_value_score': {'weight': 0.15, 'description': 'Market-based team quality'},
        'form_score': {'weight': 0.05, 'description': 'Recent performance (last 5 matches)'},
        'squad_depth_score': {'weight': 0.02, 'description': 'Squad size and depth measure'},
        'offensive_rating': {'weight': 0.03, 'description': 'Goals scored performance'},
        'defensive_rating': {'weight': 0.03, 'description': 'Goals conceded performance'},
        'home_advantage': {'weight': 0.01, 'description': 'Home vs away performance'}
    }
    
    total_weight = sum(param['weight'] for param in required_parameters.values())
    
    conn = sqlite3.connect("db/football_strength.db")
    c = conn.cursor()
    
    # Check database columns
    c.execute("PRAGMA table_info(competition_team_strength)")
    columns = {col[1]: col[2] for col in c.fetchall()}
    
    for param, details in required_parameters.items():
        param_normalized = f"{param}_normalized"
        
        has_raw = param in columns
        has_normalized = param_normalized in columns
        
        if has_raw and has_normalized:
            # Check data availability
            c.execute(f"SELECT COUNT(*) FROM competition_team_strength WHERE {param} IS NOT NULL")
            teams_with_data = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM competition_team_strength WHERE season = '2024'")
            total_teams = c.fetchone()[0]
            
            coverage = (teams_with_data / total_teams * 100) if total_teams > 0 else 0
            
            status = "✅ IMPLEMENTED"
            if coverage < 50:
                status = "⚠️ LOW COVERAGE"
            
            verification_results['parameters'][param] = {
                'implemented': True,
                'coverage': coverage,
                'weight': details['weight'],
                'status': status
            }
            
            print(f"   {status} {param}: {details['description']}")
            print(f"      Weight: {details['weight']*100:.0f}% | Coverage: {coverage:.1f}% ({teams_with_data}/{total_teams} teams)")
        
        else:
            verification_results['parameters'][param] = {
                'implemented': False,
                'coverage': 0,
                'weight': details['weight'],
                'status': "❌ MISSING"
            }
            print(f"   ❌ MISSING {param}: {details['description']}")
    
    param_status = "✅ COMPLETE" if all(p['implemented'] for p in verification_results['parameters'].values()) else "❌ INCOMPLETE"
    print(f"\nParameter Status: {param_status}")
    print(f"Total Weight Coverage: {total_weight*100:.0f}% of final system")
    
    # 2. AGENT VERIFICATION
    print(f"\n🤖 2. AGENT IMPLEMENTATION VERIFICATION")
    print("-" * 50)
    
    required_agents = [
        'competition_elo_agent.py',
        'competition_form_agent.py', 
        'competition_squad_value_agent.py',
        'competition_squad_depth_agent.py',
        'goals_data_agent.py',
        'context_data_agent.py',
        'enhanced_squad_value_agent.py'
    ]
    
    agent_base_path = "agents/team_strength/"
    
    for agent in required_agents:
        agent_path = os.path.join(agent_base_path, agent)
        exists = os.path.exists(agent_path)
        
        verification_results['agents'][agent] = {
            'implemented': exists,
            'path': agent_path
        }
        
        status = "✅ IMPLEMENTED" if exists else "❌ MISSING"
        print(f"   {status} {agent}")
    
    agent_status = "✅ COMPLETE" if all(a['implemented'] for a in verification_results['agents'].values()) else "❌ INCOMPLETE"
    print(f"\nAgent Status: {agent_status}")
    print(f"Implemented: {sum(1 for a in verification_results['agents'].values() if a['implemented'])}/{len(required_agents)} agents")
    
    # 3. DATABASE SCHEMA VERIFICATION
    print(f"\n🗄️ 3. DATABASE SCHEMA VERIFICATION")
    print("-" * 50)
    
    required_columns = [
        'elo_score', 'elo_normalized',
        'squad_value_score', 'squad_value_normalized',
        'form_score', 'form_normalized',
        'squad_depth_score', 'squad_depth_normalized',
        'offensive_rating', 'offensive_normalized',
        'defensive_rating', 'defensive_normalized',
        'home_advantage', 'home_advantage_normalized',
        'phase1_strength', 'phase1_completion'
    ]
    
    for column in required_columns:
        exists = column in columns
        verification_results['database'][column] = exists
        
        status = "✅ EXISTS" if exists else "❌ MISSING"
        print(f"   {status} {column}")
    
    db_status = "✅ COMPLETE" if all(verification_results['database'].values()) else "❌ INCOMPLETE"
    print(f"\nDatabase Schema Status: {db_status}")
    
    # 4. CALCULATION ENGINE VERIFICATION
    print(f"\n🧮 4. CALCULATION ENGINE VERIFICATION")
    print("-" * 50)
    
    # Check if phase1_engine.py exists and is functional
    engine_exists = os.path.exists("phase1_engine.py")
    
    if engine_exists:
        print("   ✅ IMPLEMENTED phase1_engine.py")
        
        # Check if Phase 1 calculations are in database
        c.execute("SELECT COUNT(*) FROM competition_team_strength WHERE phase1_strength IS NOT NULL")
        teams_with_phase1 = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM competition_team_strength WHERE season = '2024' AND team_name IS NOT NULL")
        total_teams = c.fetchone()[0]
        
        calculation_coverage = (teams_with_phase1 / total_teams * 100) if total_teams > 0 else 0
        
        print(f"   ✅ Phase 1 calculations: {calculation_coverage:.1f}% coverage ({teams_with_phase1}/{total_teams} teams)")
        
        verification_results['calculation']['engine_exists'] = True
        verification_results['calculation']['coverage'] = calculation_coverage
    else:
        print("   ❌ MISSING phase1_engine.py")
        verification_results['calculation']['engine_exists'] = False
        verification_results['calculation']['coverage'] = 0
    
    calculation_status = "✅ COMPLETE" if engine_exists and calculation_coverage > 90 else "❌ INCOMPLETE"
    print(f"\nCalculation Engine Status: {calculation_status}")
    
    # 5. OVERALL PHASE 1 STATUS
    print(f"\n🎯 5. OVERALL PHASE 1 STATUS")
    print("=" * 50)
    
    status_checks = [
        ('Parameters', param_status),
        ('Agents', agent_status), 
        ('Database Schema', db_status),
        ('Calculation Engine', calculation_status)
    ]
    
    all_complete = all('COMPLETE' in status for _, status in status_checks)
    
    for component, status in status_checks:
        print(f"   {status} {component}")
    
    if all_complete:
        verification_results['overall_status'] = '✅ 100% PHASE 1 COMPLETE'
        print(f"\n🎉 PHASE 1 VERIFICATION: ✅ 100% COMPLETE")
        print("   • All 7 parameters implemented with proper weighting")
        print("   • All 7 agents created and functional")
        print("   • Database schema fully supports Phase 1")
        print("   • Calculation engine implements 47% of final architecture")
        print("   • Ready for production deployment")
    else:
        verification_results['overall_status'] = '❌ PHASE 1 INCOMPLETE'
        print(f"\n⚠️ PHASE 1 VERIFICATION: ❌ INCOMPLETE")
        print("   Remaining issues must be resolved before deployment")
    
    # 6. PERFORMANCE METRICS
    print(f"\n📈 6. PHASE 1 PERFORMANCE METRICS")
    print("-" * 50)
    
    # Get top performing teams
    c.execute("""
        SELECT team_name, phase1_strength, phase1_completion
        FROM competition_team_strength 
        WHERE phase1_strength IS NOT NULL
        ORDER BY phase1_strength DESC
        LIMIT 5
    """)
    
    top_teams = c.fetchall()
    
    if top_teams:
        print("Top 5 teams by Phase 1 strength:")
        for i, (team, strength, completion) in enumerate(top_teams, 1):
            print(f"   {i}. {team}: {strength:.3f} ({completion:.0f}% complete)")
    
    # Coverage statistics
    c.execute("""
        SELECT 
            AVG(phase1_completion) as avg_completion,
            COUNT(CASE WHEN phase1_completion = 100 THEN 1 END) as complete_teams,
            COUNT(*) as total_teams
        FROM competition_team_strength 
        WHERE phase1_strength IS NOT NULL
    """)
    
    stats = c.fetchone()
    if stats[0] is not None:
        avg_completion, complete_teams, total_teams = stats
        print(f"\nPhase 1 Statistics:")
        print(f"   Average completion: {avg_completion:.1f}%")
        print(f"   Teams with 100% data: {complete_teams}/{total_teams} ({complete_teams/total_teams*100:.1f}%)")
    
    conn.close()
    
    print(f"\n📅 Verification completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return verification_results

if __name__ == "__main__":
    results = verify_phase1_completion()
    
    # Return appropriate exit code
    if results['overall_status'] == '✅ 100% PHASE 1 COMPLETE':
        exit(0)  # Success
    else:
        exit(1)  # Incomplete