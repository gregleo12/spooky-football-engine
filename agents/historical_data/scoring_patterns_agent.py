#!/usr/bin/env python3
"""
Scoring Patterns Analysis Agent
Analyzes team scoring patterns, goal trends, and offensive/defensive characteristics
Third historical data metric - adds 3% weight to overall strength calculation
"""
import sqlite3
import sys
import os
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

# Add shared utilities to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from competition_normalizer import update_competition_metric, get_competition_teams

def get_database_connection():
    """Get database connection"""
    return sqlite3.connect("db/football_strength.db")

def analyze_team_scoring_patterns(team_name, competition_id, limit=50):
    """Analyze comprehensive scoring patterns for a team"""
    conn = get_database_connection()
    c = conn.cursor()
    
    # Get recent matches for this team in this competition
    c.execute("""
        SELECT 
            home_team_name, away_team_name, home_score, away_score,
            match_date, season, competition_name
        FROM matches 
        WHERE competition_id = ? 
        AND (home_team_name = ? OR away_team_name = ?)
        AND status = 'FT'
        ORDER BY match_date DESC
        LIMIT ?
    """, (competition_id, team_name, team_name, limit))
    
    matches = c.fetchall()
    conn.close()
    
    if not matches:
        return {
            'total_matches': 0,
            'goals_scored': 0,
            'goals_conceded': 0,
            'avg_goals_scored': 0.0,
            'avg_goals_conceded': 0.0,
            'clean_sheets': 0,
            'failed_to_score': 0,
            'high_scoring_games': 0,
            'low_scoring_games': 0,
            'goal_difference_per_match': 0.0,
            'scoring_consistency': 0.0,
            'defensive_consistency': 0.0,
            'home_goals_avg': 0.0,
            'away_goals_avg': 0.0,
            'recent_form_goals': 0.0
        }
    
    # Initialize analysis variables
    total_goals_scored = 0
    total_goals_conceded = 0
    clean_sheets = 0
    failed_to_score = 0
    high_scoring_games = 0  # 3+ goals
    low_scoring_games = 0   # 0-1 goals
    
    home_goals = []
    away_goals = []
    home_conceded = []
    away_conceded = []
    
    goals_per_match = []
    conceded_per_match = []
    recent_form_goals = []  # Last 10 matches for form
    
    for i, match in enumerate(matches):
        home_team, away_team, home_score, away_score, match_date, season, competition = match
        
        # Determine if team was home or away
        if home_team == team_name:
            # Team was home
            team_goals = home_score
            opponent_goals = away_score
            was_home = True
            home_goals.append(team_goals)
            home_conceded.append(opponent_goals)
        else:
            # Team was away
            team_goals = away_score
            opponent_goals = home_score
            was_home = False
            away_goals.append(team_goals)
            away_conceded.append(opponent_goals)
        
        # Accumulate statistics
        total_goals_scored += team_goals
        total_goals_conceded += opponent_goals
        goals_per_match.append(team_goals)
        conceded_per_match.append(opponent_goals)
        
        # Recent form (last 10 matches)
        if i < 10:
            recent_form_goals.append(team_goals)
        
        # Pattern analysis
        if opponent_goals == 0:
            clean_sheets += 1
        if team_goals == 0:
            failed_to_score += 1
        if team_goals >= 3:
            high_scoring_games += 1
        if team_goals <= 1:
            low_scoring_games += 1
    
    total_matches = len(matches)
    
    # Calculate advanced metrics
    avg_goals_scored = total_goals_scored / total_matches
    avg_goals_conceded = total_goals_conceded / total_matches
    goal_difference_per_match = (total_goals_scored - total_goals_conceded) / total_matches
    
    # Scoring consistency (lower standard deviation = more consistent)
    scoring_consistency = 100 - (statistics.stdev(goals_per_match) * 20) if len(goals_per_match) > 1 else 50
    scoring_consistency = max(0, min(100, scoring_consistency))
    
    # Defensive consistency (lower goals conceded deviation = more consistent)
    defensive_consistency = 100 - (statistics.stdev(conceded_per_match) * 20) if len(conceded_per_match) > 1 else 50
    defensive_consistency = max(0, min(100, defensive_consistency))
    
    # Home vs Away goal averages
    home_goals_avg = sum(home_goals) / len(home_goals) if home_goals else 0
    away_goals_avg = sum(away_goals) / len(away_goals) if away_goals else 0
    
    # Recent form average (last 10 matches)
    recent_form_goals_avg = sum(recent_form_goals) / len(recent_form_goals) if recent_form_goals else 0
    
    return {
        'total_matches': total_matches,
        'goals_scored': total_goals_scored,
        'goals_conceded': total_goals_conceded,
        'avg_goals_scored': avg_goals_scored,
        'avg_goals_conceded': avg_goals_conceded,
        'clean_sheets': clean_sheets,
        'failed_to_score': failed_to_score,
        'high_scoring_games': high_scoring_games,
        'low_scoring_games': low_scoring_games,
        'goal_difference_per_match': goal_difference_per_match,
        'scoring_consistency': scoring_consistency,
        'defensive_consistency': defensive_consistency,
        'home_goals_avg': home_goals_avg,
        'away_goals_avg': away_goals_avg,
        'recent_form_goals': recent_form_goals_avg,
        'clean_sheet_rate': (clean_sheets / total_matches) * 100,
        'fail_to_score_rate': (failed_to_score / total_matches) * 100
    }

def calculate_scoring_patterns_score(patterns_data):
    """Calculate comprehensive scoring patterns strength score"""
    if patterns_data['total_matches'] == 0:
        return 50.0  # Neutral score if no data
    
    # Key scoring metrics (0-100 scale)
    
    # 1. Goal scoring ability (35% weight)
    goals_per_match = patterns_data['avg_goals_scored']
    scoring_ability = min(100, (goals_per_match / 3.0) * 100)  # 3 goals/match = 100
    
    # 2. Defensive solidity (30% weight)  
    goals_conceded_per_match = patterns_data['avg_goals_conceded']
    defensive_solidity = max(0, 100 - (goals_conceded_per_match / 3.0) * 100)  # 0 conceded = 100
    
    # 3. Goal difference efficiency (20% weight)
    goal_diff = patterns_data['goal_difference_per_match']
    goal_diff_score = 50 + (goal_diff * 25)  # -2 to +2 range mapped to 0-100
    goal_diff_score = max(0, min(100, goal_diff_score))
    
    # 4. Scoring consistency (10% weight)
    consistency_score = patterns_data['scoring_consistency']
    
    # 5. Recent form bonus (5% weight)
    recent_form = patterns_data['recent_form_goals']
    recent_form_score = min(100, (recent_form / 2.5) * 100)  # 2.5 goals/match = 100
    
    # Combine all factors
    final_score = (
        scoring_ability * 0.35 +
        defensive_solidity * 0.30 +
        goal_diff_score * 0.20 +
        consistency_score * 0.10 +
        recent_form_score * 0.05
    )
    
    # Bonus factors
    clean_sheet_bonus = min(5, patterns_data['clean_sheet_rate'] / 10)  # Up to 5 points
    high_scoring_bonus = min(3, patterns_data['high_scoring_games'] / patterns_data['total_matches'] * 30)
    
    final_score += clean_sheet_bonus + high_scoring_bonus
    
    return max(0, min(100, final_score))

def update_scoring_patterns_analysis(competition_name=None):
    """Update scoring patterns analysis for all teams"""
    print("⚽ SCORING PATTERNS ANALYSIS")
    print("=" * 60)
    print("🎯 Analyzing goal-scoring trends and patterns")
    print("📊 Metrics: Goals/match, consistency, clean sheets, recent form")
    
    conn = get_database_connection()
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON;")
    
    # Get competitions to process
    if competition_name:
        c.execute("SELECT id, name FROM competitions WHERE name = ? AND type = 'domestic_league'", (competition_name,))
    else:
        c.execute("SELECT id, name FROM competitions WHERE type = 'domestic_league'")
    
    competitions = c.fetchall()
    
    for comp_id, comp_name in competitions:
        print(f"\n🏆 Processing {comp_name}")
        print("-" * 40)
        
        # Get teams in this competition
        competition_teams = get_competition_teams(comp_id, conn)
        
        if not competition_teams:
            print(f"   ⚠️ No teams found for {comp_name}")
            continue
        
        # Calculate scoring patterns for each team
        team_scoring_scores = {}
        
        for team_id, team_name, _ in competition_teams:
            # Analyze scoring patterns
            patterns_data = analyze_team_scoring_patterns(team_name, comp_id)
            
            if patterns_data['total_matches'] > 0:
                score = calculate_scoring_patterns_score(patterns_data)
                team_scoring_scores[team_id] = score
                
                # Enhanced reporting with key metrics
                matches = patterns_data['total_matches']
                avg_scored = patterns_data['avg_goals_scored']
                avg_conceded = patterns_data['avg_goals_conceded']
                clean_sheets = patterns_data['clean_sheets']
                consistency = patterns_data['scoring_consistency']
                
                print(f"   ⚽ {team_name}: {score:.1f} "
                      f"({matches}M, {avg_scored:.1f}GF/M, {avg_conceded:.1f}GA/M, "
                      f"{clean_sheets}CS, {consistency:.0f}% consistent)")
            else:
                team_scoring_scores[team_id] = 50.0  # Neutral score
                print(f"   📊 {team_name}: 50.0 (no scoring data)")
        
        # Update database with scoring patterns scores
        if team_scoring_scores:
            update_competition_metric(
                comp_id, "scoring_patterns", "scoring_normalized", team_scoring_scores, conn
            )
            print(f"   ✅ Updated {len(team_scoring_scores)} teams with scoring patterns scores")
    
    # Show match data statistics for scoring analysis
    c.execute("SELECT COUNT(*) FROM matches WHERE home_score IS NOT NULL AND away_score IS NOT NULL")
    total_matches = c.fetchone()[0]
    
    c.execute("""
        SELECT competition_name, COUNT(*) 
        FROM matches 
        WHERE home_score IS NOT NULL AND away_score IS NOT NULL
        GROUP BY competition_name 
        ORDER BY COUNT(*) DESC
    """)
    matches_by_league = c.fetchall()
    
    print(f"\n📈 SCORING ANALYSIS STATISTICS:")
    print(f"   Total matches analyzed: {total_matches}")
    for league, count in matches_by_league:
        print(f"   {league}: {count} matches")
    
    conn.commit()
    conn.close()
    print(f"\n✅ Scoring Patterns analysis complete!")

def generate_scoring_insights():
    """Generate insights about scoring patterns across competitions"""
    print("\n📊 SCORING PATTERNS INSIGHTS")
    print("=" * 50)
    
    conn = get_database_connection()
    c = conn.cursor()
    
    # Top scoring teams across all competitions
    c.execute("""
        SELECT 
            cts.team_name,
            c.name as competition,
            cts.scoring_normalized as scoring_score
        FROM competition_team_strength cts
        JOIN competitions c ON cts.competition_id = c.id
        WHERE cts.scoring_normalized IS NOT NULL
        AND c.type = 'domestic_league'
        ORDER BY cts.scoring_normalized DESC
        LIMIT 15
    """)
    
    top_scorers = c.fetchall()
    
    if top_scorers:
        print("\n🎯 TOP 15 TEAMS BY SCORING PATTERNS:")
        print("-" * 50)
        print(f"{'Rank':<4} {'Team':<25} {'League':<15} {'Score':<6}")
        print("-" * 50)
        
        for i, (team, competition, score) in enumerate(top_scorers, 1):
            rank_emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i:2d}."
            print(f"{rank_emoji:<4} {team:<25} {competition:<15} {score:5.1f}")
    
    # League averages
    c.execute("""
        SELECT 
            c.name as competition,
            COUNT(cts.scoring_normalized) as teams,
            AVG(cts.scoring_normalized) as avg_score,
            MAX(cts.scoring_normalized) as max_score,
            MIN(cts.scoring_normalized) as min_score
        FROM competition_team_strength cts
        JOIN competitions c ON cts.competition_id = c.id
        WHERE cts.scoring_normalized IS NOT NULL
        AND c.type = 'domestic_league'
        GROUP BY c.name
        ORDER BY avg_score DESC
    """)
    
    league_stats = c.fetchall()
    
    if league_stats:
        print(f"\n📈 LEAGUE SCORING PATTERN AVERAGES:")
        print("-" * 60)
        print(f"{'League':<15} {'Teams':<6} {'Avg':<6} {'Max':<6} {'Min':<6} {'Range':<6}")
        print("-" * 60)
        
        for comp, teams, avg_score, max_score, min_score in league_stats:
            range_score = max_score - min_score
            print(f"{comp:<15} {teams:<6.0f} {avg_score:<6.1f} {max_score:<6.1f} {min_score:<6.1f} {range_score:<6.1f}")
    
    conn.close()

if __name__ == "__main__":
    # Process all domestic leagues for scoring patterns
    update_scoring_patterns_analysis()
    
    # Generate insights
    generate_scoring_insights()