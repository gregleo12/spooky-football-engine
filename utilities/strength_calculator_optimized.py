#!/usr/bin/env python3
"""
Optimized Strength Calculator - Without Squad Depth
Redistributes squad depth weight (2%) to proven metrics
"""
import sqlite3
import os

def calculate_optimized_strength():
    """Calculate team strengths without squad depth component"""
    print("⚡ OPTIMIZED STRENGTH CALCULATION (No Squad Depth)")
    print("=" * 60)
    
    # Change to parent directory for database access  
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    conn = sqlite3.connect("db/football_strength.db")
    c = conn.cursor()
    
    # Get current data
    c.execute("""
        SELECT 
            cts.team_name,
            c.name as league,
            cts.overall_strength as current_strength,
            cts.elo_score,
            cts.squad_value_score,
            cts.form_score,
            cts.squad_depth_score,
            cts.h2h_performance,
            cts.scoring_patterns
        FROM competition_team_strength cts
        JOIN competitions c ON cts.competition_id = c.id
        WHERE c.name IN ('Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1')
        AND cts.overall_strength IS NOT NULL
        ORDER BY cts.overall_strength DESC
    """)
    
    teams_data = c.fetchall()
    
    print(f"📊 WEIGHT REDISTRIBUTION:")
    print(f"OLD: ELO(18%) + Value(15%) + Form(5%) + Depth(2%) + H2H(4%) + Scoring(3%) = 47%")
    print(f"NEW: ELO(19%) + Value(16%) + Form(5%) + H2H(4%) + Scoring(3%) = 47%")
    print(f"")
    print(f"Changes: ELO +1%, Squad Value +1%, Squad Depth removed")
    
    print(f"\n🔝 TOP 20 TEAMS - STRENGTH COMPARISON:")
    print(f"{'Team':<20} {'League':<12} {'Current':<8} {'Optimized':<10} {'Change':<7}")
    print("-" * 75)
    
    optimized_teams = []
    
    for row in teams_data[:20]:
        team, league, current, elo, value, form, depth, h2h, scoring = row
        
        # New optimized calculation (without squad depth, redistributed weights)
        optimized = (
            (elo or 0) * 0.19 +           # ELO: 18% → 19% (+1%)
            (value or 0) * 0.16 +         # Value: 15% → 16% (+1%) 
            (form or 0) * 0.05 +          # Form: 5% (unchanged)
            (h2h or 0) * 0.04 +           # H2H: 4% (unchanged)
            (scoring or 0) * 0.03         # Scoring: 3% (unchanged)
        )
        
        change = optimized - current
        optimized_teams.append((team, league, optimized, change))
        
        print(f"{team:<20} {league:<12} {current:<8.2f} {optimized:<10.2f} {change:+7.3f}")
    
    # Sort by optimized strength
    optimized_teams.sort(key=lambda x: x[2], reverse=True)
    
    print(f"\n🏆 NEW RANKING (Top 15):")
    print(f"{'Rank':<4} {'Team':<20} {'League':<12} {'Strength':<8}")
    print("-" * 50)
    
    for i, (team, league, strength, _) in enumerate(optimized_teams[:15]):
        print(f"{i+1:<4} {team:<20} {league:<12} {strength:<8.2f}")
    
    # Calculate impact statistics
    changes = [abs(data[3]) for data in optimized_teams]
    avg_change = sum(changes) / len(changes)
    max_change = max(changes)
    
    print(f"\n📈 IMPACT ANALYSIS:")
    print(f"Average absolute change: {avg_change:.3f} points")
    print(f"Maximum absolute change: {max_change:.3f} points") 
    print(f"Teams with >0.5 point change: {sum(1 for c in changes if c > 0.5)}/{len(changes)}")
    print(f"Teams with >1.0 point change: {sum(1 for c in changes if c > 1.0)}/{len(changes)}")
    
    # Check for ranking changes
    current_ranking = [row[0] for row in teams_data[:20]]
    new_ranking = [team for team, _, _, _ in optimized_teams[:20]]
    
    ranking_changes = 0
    for i, team in enumerate(current_ranking):
        if team != new_ranking[i]:
            ranking_changes += 1
    
    print(f"\n🔄 RANKING CHANGES:")
    print(f"Teams that changed position in top 20: {ranking_changes}/20")
    
    if ranking_changes == 0:
        print("✅ No ranking changes - confirms squad depth had minimal impact")
    elif ranking_changes <= 3:
        print("⚠️  Minor ranking changes - squad depth had small impact")
    else:
        print("❌ Significant ranking changes - squad depth had meaningful impact")
    
    conn.close()
    
    print(f"\n🎯 CONCLUSION:")
    if avg_change < 0.1 and ranking_changes <= 2:
        print("✅ CONFIRMED: Squad depth can be safely removed")
        print("   • Minimal impact on strength scores")
        print("   • No significant ranking changes")
        print("   • Weight better used on proven metrics")
    else:
        print("⚠️  CAUTION: Squad depth removal has measurable impact")
        print("   • Consider improved implementation instead")
    
    return optimized_teams

if __name__ == "__main__":
    calculate_optimized_strength()