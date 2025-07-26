#!/usr/bin/env python3
"""
Final Squad Depth Analysis - Corrected Calculation
Tests the actual impact of removing squad depth from strength calculations
"""
import sqlite3
import os
import statistics

def analyze_squad_depth_removal():
    """Test removing squad depth from strength calculation (corrected)"""
    print("🔍 FINAL SQUAD DEPTH IMPACT ANALYSIS")
    print("=" * 60)
    
    # Change to parent directory for database access  
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    conn = sqlite3.connect("db/football_strength.db")
    c = conn.cursor()
    
    # Get teams with all normalized metrics
    c.execute("""
        SELECT 
            cts.team_name,
            c.name as league,
            cts.overall_strength,
            cts.elo_normalized,
            cts.squad_value_normalized,
            cts.form_normalized,
            cts.squad_depth_normalized,
            cts.h2h_normalized,
            cts.scoring_normalized
        FROM competition_team_strength cts
        JOIN competitions c ON cts.competition_id = c.id
        WHERE c.name IN ('Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1')
        AND cts.overall_strength IS NOT NULL
        AND cts.elo_normalized IS NOT NULL
        AND cts.squad_depth_normalized IS NOT NULL
        ORDER BY cts.overall_strength DESC
    """)
    
    teams_data = c.fetchall()
    
    print(f"📊 CURRENT WEIGHTS:")
    print(f"ELO: 18%, Squad Value: 15%, Form: 5%, Squad Depth: 2%, H2H: 4%, Scoring: 3%")
    
    print(f"\n🧪 TESTING SQUAD DEPTH REMOVAL:")
    print(f"Option 1: Remove completely (reduce total from 47% to 45%)")
    print(f"Option 2: Redistribute to proven metrics (keep 47% total)")
    
    print(f"\n{'Team':<20} {'League':<12} {'Current':<8} {'Option1':<7} {'Option2':<7} {'Change':<7}")
    print("-" * 80)
    
    changes_option1 = []
    changes_option2 = []
    ranking_changes_1 = 0
    ranking_changes_2 = 0
    
    current_ranking = []
    option1_teams = []
    option2_teams = []
    
    for i, row in enumerate(teams_data[:20]):  # Top 20 teams
        team, league, current, elo_n, value_n, form_n, depth_n, h2h_n, scoring_n = row
        
        # Current calculation (using normalized values * 100)
        current_calc = (
            (elo_n or 0) * 18 +        # ELO: 18%
            (value_n or 0) * 15 +      # Value: 15%
            (form_n or 0) * 5 +        # Form: 5%
            (depth_n or 0) * 2 +       # Depth: 2%
            (h2h_n or 0) * 4 +         # H2H: 4%
            (scoring_n or 0) * 3       # Scoring: 3%
        )
        
        # Option 1: Remove squad depth completely (45% total)
        option1 = (
            (elo_n or 0) * 18 +        # ELO: 18%
            (value_n or 0) * 15 +      # Value: 15%
            (form_n or 0) * 5 +        # Form: 5%
            (h2h_n or 0) * 4 +         # H2H: 4%
            (scoring_n or 0) * 3       # Scoring: 3%
        )
        
        # Option 2: Redistribute squad depth weight (47% total maintained)
        # ELO: 18% → 19% (+1%), Value: 15% → 16% (+1%)
        option2 = (
            (elo_n or 0) * 19 +        # ELO: 18% → 19%
            (value_n or 0) * 16 +      # Value: 15% → 16%
            (form_n or 0) * 5 +        # Form: 5%
            (h2h_n or 0) * 4 +         # H2H: 4%
            (scoring_n or 0) * 3       # Scoring: 3%
        )
        
        change1 = option1 - current
        change2 = option2 - current
        
        changes_option1.append(abs(change1))
        changes_option2.append(abs(change2))
        
        current_ranking.append((team, current))
        option1_teams.append((team, option1))
        option2_teams.append((team, option2))
        
        print(f"{team:<20} {league:<12} {current:<8.2f} {option1:<7.2f} {option2:<7.2f} {change2:+7.3f}")
    
    # Calculate ranking changes
    option1_teams.sort(key=lambda x: x[1], reverse=True)
    option2_teams.sort(key=lambda x: x[1], reverse=True)
    
    option1_ranking = [team for team, _ in option1_teams]
    option2_ranking = [team for team, _ in option2_teams]
    current_team_order = [team for team, _ in current_ranking]
    
    for i, team in enumerate(current_team_order):
        if team != option1_ranking[i]:
            ranking_changes_1 += 1
        if team != option2_ranking[i]:
            ranking_changes_2 += 1
    
    print(f"\n📈 IMPACT SUMMARY:")
    print(f"                               Option 1    Option 2")
    print(f"Average absolute change:       {statistics.mean(changes_option1):.3f}      {statistics.mean(changes_option2):.3f}")
    print(f"Maximum absolute change:       {max(changes_option1):.3f}      {max(changes_option2):.3f}")
    print(f"Ranking changes (top 20):      {ranking_changes_1}/20       {ranking_changes_2}/20")
    
    # Show new top 10 for Option 2
    print(f"\n🏆 NEW TOP 10 (Option 2 - Redistributed):")
    for i, (team, score) in enumerate(option2_teams[:10]):
        print(f"{i+1:2}. {team:<20} {score:.2f}")
    
    # Final recommendation
    print(f"\n🎯 FINAL RECOMMENDATION:")
    
    if statistics.mean(changes_option2) < 0.1 and ranking_changes_2 <= 2:
        print("✅ REMOVE SQUAD DEPTH - Use Option 2 (redistribute weight)")
        print("   • Minimal impact on strength scores")
        print("   • No significant ranking changes") 
        print("   • 2% weight better used on proven ELO and Squad Value metrics")
        recommendation = "REMOVE"
    elif statistics.mean(changes_option2) < 0.5 and ranking_changes_2 <= 5:
        print("⚠️  CONSIDER REMOVAL - Limited impact but some changes")
        print("   • Small impact on rankings")
        print("   • Squad depth correlation is weak (+0.1047)")
        print("   • Consider improving calculation instead")
        recommendation = "CONSIDER"
    else:
        print("❌ KEEP SQUAD DEPTH - Significant impact detected")
        print("   • Removing would cause major ranking changes")
        print("   • Focus on improving the calculation method")
        recommendation = "KEEP"
    
    # Implementation details
    if recommendation in ["REMOVE", "CONSIDER"]:
        print(f"\n💡 IMPLEMENTATION PLAN:")
        print(f"1. Update competition_team_strength_calculator.py:")
        print(f"   • Change ELO weight: 0.18 → 0.19")
        print(f"   • Change Squad Value weight: 0.15 → 0.16") 
        print(f"   • Remove squad_depth weight (0.02)")
        print(f"2. Update demo_app.py teams ranking endpoint")
        print(f"3. Test on production data")
        print(f"4. Deploy if testing confirms minimal impact")
    
    conn.close()
    return recommendation, statistics.mean(changes_option2), ranking_changes_2

if __name__ == "__main__":
    analyze_squad_depth_removal()