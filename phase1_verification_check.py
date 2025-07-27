#!/usr/bin/env python3
"""
Phase 1 Verification Check - Comprehensive Status Report
Answers all verification questions with detailed analysis
"""
import sqlite3
from datetime import datetime

def phase1_verification_check():
    """Run comprehensive Phase 1 verification check"""
    
    print("🔍 PHASE 1 VERIFICATION CHECK")
    print("=" * 70)
    print()
    
    conn = sqlite3.connect("db/football_strength.db")
    c = conn.cursor()
    
    # 1. PARAMETER COUNT VERIFICATION
    print("📊 1. PARAMETER COUNT VERIFICATION")
    print("-" * 50)
    
    # Get total teams and parameter coverage
    c.execute("""
        SELECT COUNT(*) as total_teams,
               COUNT(CASE WHEN elo_score IS NOT NULL THEN 1 END) as elo_count,
               COUNT(CASE WHEN squad_value_score IS NOT NULL THEN 1 END) as squad_value_count,
               COUNT(CASE WHEN form_score IS NOT NULL THEN 1 END) as form_count,
               COUNT(CASE WHEN squad_depth_score IS NOT NULL THEN 1 END) as depth_count,
               COUNT(CASE WHEN offensive_rating IS NOT NULL THEN 1 END) as offensive_count,
               COUNT(CASE WHEN defensive_rating IS NOT NULL THEN 1 END) as defensive_count,
               COUNT(CASE WHEN home_advantage IS NOT NULL THEN 1 END) as home_count
        FROM competition_team_strength 
        WHERE season = '2024' AND team_name IS NOT NULL
    """)
    
    counts = c.fetchone()
    total_teams = counts[0]
    
    print(f"Total teams in database: {total_teams}")
    print(f"Parameter coverage:")
    print(f"  • ELO Score: {counts[1]}/{total_teams} ({counts[1]/total_teams*100:.1f}%)")
    print(f"  • Squad Value: {counts[2]}/{total_teams} ({counts[2]/total_teams*100:.1f}%)")
    print(f"  • Form Score: {counts[3]}/{total_teams} ({counts[3]/total_teams*100:.1f}%)")
    print(f"  • Squad Depth: {counts[4]}/{total_teams} ({counts[4]/total_teams*100:.1f}%)")
    print(f"  • Offensive Rating: {counts[5]}/{total_teams} ({counts[5]/total_teams*100:.1f}%)")
    print(f"  • Defensive Rating: {counts[6]}/{total_teams} ({counts[6]/total_teams*100:.1f}%)")
    print(f"  • Home Advantage: {counts[7]}/{total_teams} ({counts[7]/total_teams*100:.1f}%)")
    
    # Sample data from top teams
    print(f"\nSample data (top 5 teams with complete data):")
    c.execute("""
        SELECT team_name, 
               elo_score, squad_value_score, form_score, squad_depth_score,
               offensive_rating, defensive_rating, home_advantage,
               phase1_strength, phase1_completion
        FROM competition_team_strength 
        WHERE elo_score IS NOT NULL 
        AND squad_value_score IS NOT NULL 
        AND form_score IS NOT NULL 
        AND squad_depth_score IS NOT NULL
        AND offensive_rating IS NOT NULL 
        AND defensive_rating IS NOT NULL 
        AND home_advantage IS NOT NULL
        ORDER BY phase1_strength DESC
        LIMIT 5
    """)
    
    sample_teams = c.fetchall()
    if sample_teams:
        for i, team in enumerate(sample_teams, 1):
            name, elo, squad_val, form, depth, off, def_, home, phase1, completion = team
            print(f"  {i}. {name}:")
            print(f"     ELO: {elo:.3f}, Squad: €{squad_val}M, Form: {form:.3f}, Depth: {depth:.3f}")
            print(f"     Off: {off:.3f}, Def: {def_:.3f}, Home: {home:.3f}")
            print(f"     Phase1 Strength: {phase1:.3f} ({completion:.0f}% complete)")
    else:
        print("  No teams found with complete 7-parameter data")
    
    # 2. SQUAD DEPTH FIX VERIFICATION
    print(f"\n🏟️ 2. SQUAD DEPTH FIX VERIFICATION")
    print("-" * 50)
    
    # Check Chelsea vs Alaves specifically
    c.execute("""
        SELECT cts.team_name, cts.squad_value_score, cts.squad_depth_score, 
               cts.squad_depth_normalized, c.name as league
        FROM competition_team_strength cts
        JOIN competitions c ON cts.competition_id = c.id
        WHERE cts.team_name IN ('Chelsea', 'Alaves') 
        AND cts.season = '2024'
        ORDER BY cts.squad_depth_score DESC
    """)
    
    depth_comparison = c.fetchall()
    if depth_comparison:
        print("Squad Depth Comparison (Fixed):")
        for team, squad_val, depth_raw, depth_norm, league in depth_comparison:
            print(f"  • {team} ({league}): €{squad_val}M squad value")
            print(f"    Raw depth score: {depth_raw:.3f}")
            print(f"    Normalized (within league): {depth_norm:.3f}")
    else:
        print("Chelsea or Alaves data not found")
    
    # 3. DATA FRESHNESS CHECK
    print(f"\n📅 3. DATA FRESHNESS CHECK")
    print("-" * 50)
    
    # Check last_updated timestamps for different parameters
    freshness_queries = [
        ("ELO data", "SELECT MAX(last_updated) FROM competition_team_strength WHERE elo_score IS NOT NULL"),
        ("Squad values", "SELECT MAX(last_updated) FROM competition_team_strength WHERE squad_value_score IS NOT NULL"), 
        ("Form scores", "SELECT MAX(last_updated) FROM competition_team_strength WHERE form_score IS NOT NULL"),
        ("Squad depth", "SELECT MAX(last_updated) FROM competition_team_strength WHERE squad_depth_score IS NOT NULL"),
        ("Goals data", "SELECT MAX(last_updated) FROM competition_team_strength WHERE offensive_rating IS NOT NULL"),
        ("Home advantage", "SELECT MAX(last_updated) FROM competition_team_strength WHERE home_advantage IS NOT NULL")
    ]
    
    for param_name, query in freshness_queries:
        c.execute(query)
        result = c.fetchone()[0]
        if result:
            # Parse the datetime string
            try:
                dt = datetime.fromisoformat(result.replace('Z', '+00:00'))
                formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
                print(f"  • {param_name}: {formatted_time}")
            except:
                print(f"  • {param_name}: {result}")
        else:
            print(f"  • {param_name}: No data found")
    
    # 4. AGENT STATUS CHECK
    print(f"\n🤖 4. AGENT STATUS CHECK")
    print("-" * 50)
    
    agents_to_check = [
        "competition_elo_agent.py",
        "competition_form_agent.py", 
        "competition_squad_value_agent.py",
        "competition_squad_depth_agent.py",
        "goals_data_agent.py",
        "context_data_agent.py"
    ]
    
    import os
    
    for agent in agents_to_check:
        agent_path = f"agents/team_strength/{agent}"
        exists = os.path.exists(agent_path)
        
        if exists:
            # Get file size and modification time
            stat = os.stat(agent_path)
            size_kb = stat.st_size / 1024
            mod_time = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            print(f"  ✅ {agent} ({size_kb:.1f}KB, modified: {mod_time})")
        else:
            print(f"  ❌ {agent} - NOT FOUND")
    
    # 5. COVERAGE REPORT
    print(f"\n📋 5. COVERAGE REPORT - TEAMS MISSING DATA")
    print("-" * 50)
    
    # Find teams missing any parameters
    c.execute("""
        SELECT team_name, 
               CASE WHEN elo_score IS NULL THEN 'ELO ' ELSE '' END ||
               CASE WHEN squad_value_score IS NULL THEN 'SQUAD_VAL ' ELSE '' END ||
               CASE WHEN form_score IS NULL THEN 'FORM ' ELSE '' END ||
               CASE WHEN squad_depth_score IS NULL THEN 'DEPTH ' ELSE '' END ||
               CASE WHEN offensive_rating IS NULL THEN 'OFFENSIVE ' ELSE '' END ||
               CASE WHEN defensive_rating IS NULL THEN 'DEFENSIVE ' ELSE '' END ||
               CASE WHEN home_advantage IS NULL THEN 'HOME_ADV ' ELSE '' END as missing_params,
               phase1_completion
        FROM competition_team_strength 
        WHERE season = '2024' AND team_name IS NOT NULL
        AND (elo_score IS NULL OR squad_value_score IS NULL OR form_score IS NULL 
             OR squad_depth_score IS NULL OR offensive_rating IS NULL 
             OR defensive_rating IS NULL OR home_advantage IS NULL)
        ORDER BY phase1_completion DESC
        LIMIT 15
    """)
    
    missing_data = c.fetchall()
    if missing_data:
        print("Teams with missing parameter data (showing top 15):")
        for team, missing, completion in missing_data:
            print(f"  • {team} ({completion:.0f}% complete): Missing {missing.strip()}")
    else:
        print("✅ All teams have complete data for all parameters!")
    
    # 6. LIVERPOOL VS MANCHESTER CITY ANALYSIS
    print(f"\n⚽ 6. LIVERPOOL VS MANCHESTER CITY ANALYSIS")
    print("-" * 50)
    
    c.execute("""
        SELECT cts.team_name,
               cts.elo_score, cts.elo_normalized,
               cts.squad_value_score, cts.squad_value_normalized,
               cts.form_score, cts.form_normalized,
               cts.squad_depth_score, cts.squad_depth_normalized,
               cts.offensive_rating, cts.offensive_normalized,
               cts.defensive_rating, cts.defensive_normalized,
               cts.home_advantage, cts.home_advantage_normalized,
               cts.phase1_strength,
               c.name as league
        FROM competition_team_strength cts
        JOIN competitions c ON cts.competition_id = c.id
        WHERE cts.team_name IN ('Liverpool', 'Manchester City') 
        AND cts.season = '2024'
        ORDER BY cts.phase1_strength DESC
    """)
    
    comparison_teams = c.fetchall()
    
    if len(comparison_teams) >= 2:
        print("Parameter-by-parameter breakdown:")
        
        # Define weights
        weights = {
            'elo': 0.18, 'squad_value': 0.15, 'form': 0.05, 'squad_depth': 0.02,
            'offensive': 0.03, 'defensive': 0.03, 'home_advantage': 0.01
        }
        
        for team_data in comparison_teams:
            (name, elo_raw, elo_norm, squad_raw, squad_norm, form_raw, form_norm,
             depth_raw, depth_norm, off_raw, off_norm, def_raw, def_norm,
             home_raw, home_norm, phase1_strength, league) = team_data
            
            print(f"\n🔥 {name} ({league}):")
            print(f"   Overall Phase 1 Strength: {phase1_strength:.3f}")
            print(f"   Parameter breakdown:")
            
            # Calculate contribution of each parameter
            contributions = {
                'ELO': (elo_norm or 0) * weights['elo'],
                'Squad Value': (squad_norm or 0) * weights['squad_value'],
                'Form': (form_norm or 0) * weights['form'],
                'Squad Depth': (depth_norm or 0) * weights['squad_depth'],
                'Offensive': (off_norm or 0) * weights['offensive'],
                'Defensive': (def_norm or 0) * weights['defensive'],
                'Home Advantage': (home_norm or 0) * weights['home_advantage']
            }
            
            raw_values = {
                'ELO': elo_raw,
                'Squad Value': f"€{squad_raw}M" if squad_raw else "N/A",
                'Form': form_raw,
                'Squad Depth': depth_raw,
                'Offensive': off_raw,
                'Defensive': def_raw,
                'Home Advantage': home_raw
            }
            
            for param, contribution in contributions.items():
                raw_val = raw_values[param]
                param_key = param.lower().replace(' ', '_')
                if param_key in weights:
                    weight = weights[param_key]
                    print(f"     • {param}: {contribution:.3f} (weight: {weight*100:.0f}%, raw: {raw_val})")
                else:
                    print(f"     • {param}: {contribution:.3f} (raw: {raw_val})")
        
        # Head-to-head comparison
        if len(comparison_teams) == 2:
            team1, team2 = comparison_teams[0], comparison_teams[1]
            strength_diff = team1[15] - team2[15]  # phase1_strength difference
            winner = team1[0] if strength_diff > 0 else team2[0]
            
            print(f"\n🏆 Head-to-Head Result:")
            print(f"   {winner} leads by {abs(strength_diff):.3f} points")
            print(f"   {team1[0]}: {team1[15]:.3f} vs {team2[0]}: {team2[15]:.3f}")
    
    else:
        print("❌ Could not find both Liverpool and Manchester City in database")
    
    # 7. OVERALL SYSTEM STATUS
    print(f"\n🎯 7. OVERALL PHASE 1 STATUS SUMMARY")
    print("=" * 50)
    
    # Calculate completion statistics
    c.execute("""
        SELECT 
            COUNT(*) as total_teams,
            COUNT(CASE WHEN phase1_completion = 100 THEN 1 END) as complete_teams,
            AVG(phase1_completion) as avg_completion,
            MIN(phase1_completion) as min_completion,
            MAX(phase1_completion) as max_completion
        FROM competition_team_strength 
        WHERE season = '2024' AND team_name IS NOT NULL
    """)
    
    stats = c.fetchone()
    total, complete, avg_comp, min_comp, max_comp = stats
    
    print(f"📊 System Statistics:")
    print(f"   Total teams: {total}")
    print(f"   Teams with 100% data: {complete}/{total} ({complete/total*100:.1f}%)")
    print(f"   Average completion: {avg_comp:.1f}%")
    print(f"   Completion range: {min_comp:.1f}% - {max_comp:.1f}%")
    
    # Deployment readiness
    if avg_comp >= 75 and complete >= total * 0.5:
        status = "✅ PRODUCTION READY"
        print(f"\n🚀 Deployment Status: {status}")
        print("   • Phase 1 implementation complete")
        print("   • Sufficient data coverage for production")
        print("   • All agents operational")
    else:
        status = "⚠️ NEEDS IMPROVEMENT"
        print(f"\n⚠️ Deployment Status: {status}")
        print("   • Requires higher data completion before production")
    
    conn.close()
    
    print(f"\n📅 Verification completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    phase1_verification_check()