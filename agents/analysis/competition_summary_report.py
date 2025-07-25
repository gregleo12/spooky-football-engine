#!/usr/bin/env python3
"""
Generate comprehensive summary report of all competition data
Shows current state and identifies potential issues
"""
import sqlite3

def generate_competition_report():
    print("📊 COMPREHENSIVE COMPETITION DATA REPORT")
    print("="*80)
    
    conn = sqlite3.connect("db/football_strength.db")
    c = conn.cursor()
    
    # 1. Competition overview
    print("\n🏆 COMPETITIONS OVERVIEW")
    print("-" * 50)
    
    c.execute("""
        SELECT 
            c.name,
            c.country,
            c.type,
            COUNT(ct.team_id) as team_count,
            COUNT(cts.team_id) as teams_with_data
        FROM competitions c
        LEFT JOIN competition_teams ct ON c.id = ct.competition_id
        LEFT JOIN competition_team_strength cts ON c.id = cts.competition_id
        GROUP BY c.id, c.name, c.country, c.type
        ORDER BY c.type, c.name
    """)
    
    competitions = c.fetchall()
    
    for name, country, comp_type, team_count, teams_with_data in competitions:
        coverage = f"{teams_with_data}/{team_count}" if team_count > 0 else "0/0"
        print(f"   {name:<20} | {country:<10} | {comp_type:<20} | {coverage} teams")
    
    # 2. Data coverage by metric
    print(f"\n📈 DATA COVERAGE BY METRIC")
    print("-" * 50)
    
    metrics = [
        ("ELO Score", "elo_score", "elo_normalized"),
        ("Squad Value", "squad_value_score", "squad_value_normalized"),
        ("Form Score", "form_score", "form_normalized"), 
        ("Squad Depth", "squad_depth_score", "squad_depth_normalized")
    ]
    
    for comp_id, comp_name, _, _, _ in competitions:
        if comp_name in ["Champions League", "Europa League", "Conference League"]:
            continue  # Skip European competitions for now
            
        print(f"\n🏟️ {comp_name}:")
        
        for metric_name, raw_col, norm_col in metrics:
            c.execute(f"""
                SELECT COUNT(*) 
                FROM competition_team_strength 
                WHERE competition_id = ? 
                AND {raw_col} IS NOT NULL 
                AND {norm_col} IS NOT NULL
            """, (comp_id,))
            
            count = c.fetchone()[0]
            print(f"   {metric_name:<12}: {count} teams")
    
    # 3. Sample data quality check
    print(f"\n🔍 DATA QUALITY SAMPLES")
    print("-" * 50)
    
    # Show top 3 teams by each metric for Premier League
    c.execute("SELECT id FROM competitions WHERE name = 'Premier League'")
    pl_id = c.fetchone()[0]
    
    print(f"\n🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League Top 3 by Metric:")
    
    for metric_name, raw_col, norm_col in metrics:
        c.execute(f"""
            SELECT team_name, {raw_col}, {norm_col}
            FROM competition_team_strength 
            WHERE competition_id = ? 
            AND {raw_col} IS NOT NULL
            ORDER BY {raw_col} DESC 
            LIMIT 3
        """, (pl_id,))
        
        results = c.fetchall()
        print(f"\n   {metric_name}:")
        for team, raw_val, norm_val in results:
            if raw_col == "squad_value_score":
                print(f"      {team:<20}: €{raw_val:.1f}M (norm: {norm_val:.3f})")
            elif raw_col == "elo_score":
                print(f"      {team:<20}: {raw_val:.1f} (norm: {norm_val:.3f})")
            else:
                print(f"      {team:<20}: {raw_val:.3f} (norm: {norm_val:.3f})")
    
    # 4. Potential issues detection
    print(f"\n⚠️ POTENTIAL ISSUES")
    print("-" * 50)
    
    issues_found = []
    
    # Check for suspiciously low squad values
    c.execute("""
        SELECT team_name, squad_value_score 
        FROM competition_team_strength cts
        JOIN competitions c ON cts.competition_id = c.id
        WHERE c.name = 'Premier League' 
        AND squad_value_score < 10 
        AND squad_value_score IS NOT NULL
    """)
    
    low_values = c.fetchall()
    if low_values:
        issues_found.append(f"Premier League teams with suspiciously low squad values:")
        for team, value in low_values:
            issues_found.append(f"   • {team}: €{value:.1f}M")
    
    # Check for missing data
    for comp_id, comp_name, _, team_count, _ in competitions:
        if comp_name in ["Champions League", "Europa League", "Conference League"]:
            continue
            
        for metric_name, raw_col, norm_col in metrics:
            c.execute(f"""
                SELECT COUNT(*) 
                FROM competition_team_strength 
                WHERE competition_id = ? AND {raw_col} IS NULL
            """, (comp_id,))
            
            missing_count = c.fetchone()[0]
            if missing_count > 0:
                issues_found.append(f"{comp_name} missing {metric_name}: {missing_count} teams")
    
    if issues_found:
        for issue in issues_found:
            print(f"   {issue}")
    else:
        print("   ✅ No obvious issues detected")
    
    # 5. Overall summary
    print(f"\n📊 SUMMARY")
    print("-" * 50)
    
    c.execute("SELECT COUNT(*) FROM teams")
    total_teams = c.fetchone()[0]
    
    c.execute("SELECT COUNT(DISTINCT team_id) FROM competition_team_strength")
    teams_with_data = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM competition_team_strength WHERE elo_score IS NOT NULL")
    teams_with_elo = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM competition_team_strength WHERE squad_value_score IS NOT NULL")
    teams_with_values = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM competition_team_strength WHERE form_score IS NOT NULL")
    teams_with_form = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM competition_team_strength WHERE squad_depth_score IS NOT NULL")
    teams_with_depth = c.fetchone()[0]
    
    print(f"   Total teams in database: {total_teams}")
    print(f"   Teams with strength data: {teams_with_data}")
    print(f"   Teams with ELO ratings: {teams_with_elo}")
    print(f"   Teams with squad values: {teams_with_values}")  
    print(f"   Teams with form scores: {teams_with_form}")
    print(f"   Teams with depth scores: {teams_with_depth}")
    
    coverage_pct = (teams_with_data / total_teams) * 100 if total_teams > 0 else 0
    print(f"   Overall coverage: {coverage_pct:.1f}%")
    
    conn.close()

if __name__ == "__main__":
    generate_competition_report()