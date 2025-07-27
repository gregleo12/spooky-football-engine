#!/usr/bin/env python3
"""
Phase 1 Final Verification Report - Complete 11-Parameter System
Comprehensive validation of the complete Phase 1 implementation
"""
import sqlite3
from datetime import datetime

def generate_final_verification_report():
    """Generate comprehensive Phase 1 verification report"""
    
    print("🔍 PHASE 1 FINAL VERIFICATION REPORT")
    print("=" * 80)
    print("Complete 11-Parameter System Validation")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    conn = sqlite3.connect("db/football_strength.db")
    c = conn.cursor()
    
    # 1. EXACT PARAMETER WEIGHTS VERIFICATION
    print("1️⃣ PARAMETER WEIGHTS VERIFICATION")
    print("-" * 50)
    
    weights = {
        'elo_score': 0.20,           # 20% - Match-based team strength
        'squad_value_score': 0.15,   # 15% - Market-based team quality  
        'form_score': 0.20,          # 20% - Recent performance
        'squad_depth_score': 0.10,   # 10% - Squad size and depth
        'offensive_rating': 0.05,    # 5% - Goals scored performance
        'defensive_rating': 0.05,    # 5% - Goals conceded performance
        'home_advantage': 0.08,      # 8% - Home vs away performance
        'motivation_factor': 0.07,   # 7% - League position motivation
        'tactical_matchup': 0.05,    # 5% - Playing style analysis
        'fatigue_factor': 0.03,      # 3% - Fixture congestion
        'key_player_availability': 0.02  # 2% - Injury/suspension impact
    }
    
    for param, weight in weights.items():
        print(f"   {param}: {weight*100:.0f}%")
    
    total_weight = sum(weights.values())
    print(f"\n   Total Weight: {total_weight*100:.1f}%")
    print(f"   Weight Check: {'✅ PASS' if total_weight == 1.0 else '❌ FAIL'}")
    print()
    
    # 2. DATABASE SCHEMA VERIFICATION
    print("2️⃣ DATABASE SCHEMA VERIFICATION")
    print("-" * 50)
    
    required_columns = [
        'elo_score', 'elo_normalized',
        'squad_value_score', 'squad_value_normalized',
        'form_score', 'form_normalized',
        'squad_depth_score', 'squad_depth_normalized',
        'offensive_rating', 'offensive_normalized',
        'defensive_rating', 'defensive_normalized',
        'home_advantage', 'home_advantage_normalized',
        'motivation_factor', 'motivation_normalized',
        'tactical_matchup', 'tactical_normalized',
        'fatigue_factor', 'fatigue_normalized',
        'key_player_availability', 'availability_normalized'
    ]
    
    c.execute("PRAGMA table_info(competition_team_strength)")
    existing_columns = [col[1] for col in c.fetchall()]
    
    missing_columns = []
    for col in required_columns:
        if col in existing_columns:
            print(f"   ✅ {col}")
        else:
            print(f"   ❌ {col} - MISSING")
            missing_columns.append(col)
    
    print(f"\n   Schema Status: {'✅ COMPLETE' if not missing_columns else '❌ INCOMPLETE'}")
    print()
    
    # 3. SAMPLE DATA VERIFICATION
    print("3️⃣ SAMPLE DATA VERIFICATION")
    print("-" * 50)
    
    sample_teams = ['Liverpool', 'Chelsea', 'Bayern München']
    
    for team in sample_teams:
        c.execute("""
            SELECT team_name, 
                   elo_score, squad_value_score, form_score, squad_depth_score,
                   offensive_rating, defensive_rating, home_advantage,
                   motivation_factor, tactical_matchup, fatigue_factor, key_player_availability,
                   phase1_strength
            FROM competition_team_strength 
            WHERE team_name = ? AND season = '2024'
        """, (team,))
        
        result = c.fetchone()
        if result:
            name, elo, squad_val, form, depth, off, def_, home, motiv, tactical, fatigue, avail, strength = result
            print(f"   🔥 {name}:")
            print(f"      Phase 1 Strength: {strength:.3f}")
            print(f"      ELO: {elo:.0f}, Squad: €{squad_val:.0f}M, Form: {form:.2f}")
            print(f"      Depth: {depth:.3f}, Off: {off:.3f}, Def: {def_:.3f}")
            print(f"      Home: {home:.3f}, Motiv: {motiv:.3f}, Tactical: {tactical:.3f}")
            print(f"      Fatigue: {fatigue:.3f}, Availability: {avail:.3f}")
        else:
            print(f"   ❌ {team} - NO DATA")
    print()
    
    # 4. NEW PARAMETER VALIDATION
    print("4️⃣ NEW PARAMETER VALIDATION")
    print("-" * 50)
    
    # Motivation Factor - Check league position correlation
    print("   📊 Motivation Factor Analysis:")
    c.execute("""
        SELECT team_name, motivation_factor, current_position
        FROM competition_team_strength cts
        JOIN competitions c ON cts.competition_id = c.id
        WHERE c.name = 'Premier League' AND current_position IS NOT NULL
        AND cts.season = '2024'
        ORDER BY current_position ASC
        LIMIT 3
    """)
    
    top_teams = c.fetchall()
    print("      Top 3 teams (title race):")
    for team, motiv, pos in top_teams:
        print(f"        {pos}. {team}: {motiv:.3f} motivation")
    
    c.execute("""
        SELECT team_name, motivation_factor, current_position
        FROM competition_team_strength cts
        JOIN competitions c ON cts.competition_id = c.id
        WHERE c.name = 'Premier League' AND current_position IS NOT NULL
        AND cts.season = '2024'
        ORDER BY current_position DESC
        LIMIT 3
    """)
    
    bottom_teams = c.fetchall()
    print("      Bottom 3 teams (relegation battle):")
    for team, motiv, pos in bottom_teams:
        print(f"        {pos}. {team}: {motiv:.3f} motivation")
    
    # Tactical Matchup Analysis
    print("\n   ⚔️ Tactical Matchup Analysis:")
    c.execute("""
        SELECT team_name, tactical_matchup
        FROM competition_team_strength cts
        JOIN competitions c ON cts.competition_id = c.id
        WHERE c.name IN ('La Liga', 'Premier League')
        AND tactical_matchup IS NOT NULL
        AND cts.season = '2024'
        ORDER BY tactical_matchup DESC
        LIMIT 5
    """)
    
    tactical_teams = c.fetchall()
    print("      Highest tactical scores:")
    for team, tactical in tactical_teams:
        print(f"        {team}: {tactical:.3f}")
    
    # Key Player Availability Analysis
    print("\n   🏥 Key Player Availability Analysis:")
    c.execute("""
        SELECT team_name, key_player_availability
        FROM competition_team_strength cts
        JOIN competitions c ON cts.competition_id = c.id
        WHERE c.name = 'Premier League'
        AND key_player_availability IS NOT NULL
        AND cts.season = '2024'
        ORDER BY key_player_availability ASC
        LIMIT 5
    """)
    
    injured_teams = c.fetchall()
    print("      Teams with key player injuries:")
    for team, avail in injured_teams:
        impact = "Severe" if avail <= 0.3 else "Moderate" if avail <= 0.6 else "Minor"
        print(f"        {team}: {avail:.3f} ({impact} impact)")
    print()
    
    # 5. CALCULATION VERIFICATION
    print("5️⃣ CALCULATION VERIFICATION")
    print("-" * 50)
    
    # Verify Liverpool calculation manually
    c.execute("""
        SELECT team_name, 
               elo_normalized, squad_value_normalized, form_normalized, squad_depth_normalized,
               offensive_normalized, defensive_normalized, home_advantage_normalized,
               motivation_normalized, tactical_normalized, fatigue_normalized, availability_normalized,
               phase1_strength
        FROM competition_team_strength 
        WHERE team_name = 'Liverpool' AND season = '2024'
    """)
    
    liverpool_data = c.fetchone()
    if liverpool_data:
        name, elo_n, squad_n, form_n, depth_n, off_n, def_n, home_n, motiv_n, tactical_n, fatigue_n, avail_n, db_strength = liverpool_data
        
        # Manual calculation
        manual_strength = (
            (elo_n or 0) * weights['elo_score'] +
            (squad_n or 0) * weights['squad_value_score'] +
            (form_n or 0) * weights['form_score'] +
            (depth_n or 0) * weights['squad_depth_score'] +
            (off_n or 0) * weights['offensive_rating'] +
            (def_n or 0) * weights['defensive_rating'] +
            (home_n or 0) * weights['home_advantage'] +
            (motiv_n or 0) * weights['motivation_factor'] +
            (tactical_n or 0) * weights['tactical_matchup'] +
            (fatigue_n or 0) * weights['fatigue_factor'] +
            (avail_n or 0) * weights['key_player_availability']
        )
        
        print(f"   Liverpool Calculation Verification:")
        print(f"      Manual calculation: {manual_strength:.3f}")
        print(f"      Database value: {db_strength:.3f}")
        print(f"      Match: {'✅ PASS' if abs(manual_strength - db_strength) < 0.001 else '❌ FAIL'}")
    print()
    
    # 6. GLOBAL RANKINGS VERIFICATION
    print("6️⃣ GLOBAL RANKINGS VERIFICATION")
    print("-" * 50)
    
    c.execute("""
        SELECT cts.team_name, c.name as league, cts.phase1_strength,
               cts.elo_score, cts.squad_value_score
        FROM competition_team_strength cts
        JOIN competitions c ON cts.competition_id = c.id
        WHERE c.name IN ('Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1')
        AND cts.phase1_strength IS NOT NULL
        AND cts.season = '2024'
        ORDER BY cts.phase1_strength DESC
        LIMIT 10
    """)
    
    top_global = c.fetchall()
    print("   Global Top 10:")
    for i, (team, league, strength, elo, squad_val) in enumerate(top_global, 1):
        print(f"   {i:2d}. {team} ({league}): {strength:.3f}")
    print()
    
    # 7. SYSTEM STATUS SUMMARY
    print("7️⃣ SYSTEM STATUS SUMMARY")
    print("-" * 50)
    
    c.execute("""
        SELECT COUNT(*) as total_teams,
               COUNT(CASE WHEN phase1_strength IS NOT NULL THEN 1 END) as teams_with_strength,
               AVG(CASE WHEN phase1_strength IS NOT NULL THEN phase1_strength END) as avg_strength
        FROM competition_team_strength 
        WHERE season = '2024' AND team_name IS NOT NULL
    """)
    
    stats = c.fetchone()
    total_teams, teams_with_strength, avg_strength = stats
    
    print(f"   Total teams in system: {total_teams}")
    print(f"   Teams with Phase 1 calculations: {teams_with_strength}")
    print(f"   Coverage: {teams_with_strength/total_teams*100:.1f}%")
    print(f"   Average Phase 1 strength: {avg_strength:.3f}")
    print()
    
    # FINAL VERDICT
    print("🎯 FINAL VERIFICATION VERDICT")
    print("=" * 50)
    
    # Check all critical success factors
    checks = [
        (total_weight == 1.0, "Parameter weights sum to 100%"),
        (not missing_columns, "All database columns exist"),
        (teams_with_strength > 90, "Sufficient teams have calculations"),
        (avg_strength > 0.5, "Reasonable strength values"),
        (len(top_global) >= 5, "Cross-league rankings work")
    ]
    
    passed_checks = sum(1 for check, _ in checks if check)
    
    for check, description in checks:
        status = "✅ PASS" if check else "❌ FAIL"
        print(f"   {status} {description}")
    
    print(f"\n   Overall Status: {passed_checks}/{len(checks)} checks passed")
    
    if passed_checks == len(checks):
        print("   🎉 PHASE 1 VERIFICATION: ✅ COMPLETE SUCCESS")
        print("   The 11-parameter system is fully implemented and operational!")
    else:
        print("   ⚠️ PHASE 1 VERIFICATION: ❌ ISSUES DETECTED")
        print("   Some components need attention before full deployment.")
    
    conn.close()
    
    print(f"\n📅 Report completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    generate_final_verification_report()