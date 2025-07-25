#!/usr/bin/env python3
"""
Local H2H Performance Analyzer
Uses stored match data for instant, accurate head-to-head analysis
"""
import sqlite3
import sys
import os
from datetime import datetime, timedelta

# Add shared utilities to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from competition_normalizer import update_competition_metric, get_competition_teams

def get_database_connection():
    """Get database connection"""
    return sqlite3.connect("db/football_strength.db")

def analyze_h2h_performance_local(team1_name, team2_name, competition_id, limit=10):
    """Analyze head-to-head performance using local match data"""
    conn = get_database_connection()
    c = conn.cursor()
    
    # Get H2H matches between these teams (both home and away)
    c.execute("""
        SELECT 
            home_team_name, away_team_name, home_score, away_score,
            match_date, season, competition_name
        FROM matches 
        WHERE competition_id = ? 
        AND (
            (home_team_name = ? AND away_team_name = ?) OR
            (home_team_name = ? AND away_team_name = ?)
        )
        AND status = 'FT'
        ORDER BY match_date DESC
        LIMIT ?
    """, (competition_id, team1_name, team2_name, team2_name, team1_name, limit))
    
    matches = c.fetchall()
    conn.close()
    
    if not matches:
        return {
            'h2h_wins': 0,
            'h2h_draws': 0,
            'h2h_losses': 0,
            'goals_scored': 0,
            'goals_conceded': 0,
            'matches_played': 0,
            'home_wins': 0,
            'away_wins': 0,
            'recent_form': [],  # Last 5 results
            'avg_goals_for': 0.0,
            'avg_goals_against': 0.0
        }
    
    # Analyze matches from team1's perspective
    wins = draws = losses = 0
    goals_for = goals_against = 0
    home_wins = away_wins = 0
    recent_form = []
    
    for match in matches:
        home_team, away_team, home_score, away_score, match_date, season, competition = match
        
        # Determine if team1 was home or away
        if home_team == team1_name:
            # Team1 was home
            team1_score = home_score
            team2_score = away_score
            was_home = True
        else:
            # Team1 was away
            team1_score = away_score
            team2_score = home_score
            was_home = False
        
        goals_for += team1_score
        goals_against += team2_score
        
        # Determine result
        if team1_score > team2_score:
            wins += 1
            result = 'W'
            if was_home:
                home_wins += 1
            else:
                away_wins += 1
        elif team1_score < team2_score:
            losses += 1
            result = 'L'
        else:
            draws += 1
            result = 'D'
        
        # Store recent form (last 5 matches)
        if len(recent_form) < 5:
            recent_form.append({
                'result': result,
                'score': f"{team1_score}-{team2_score}",
                'home': was_home,
                'date': match_date,
                'season': season
            })
    
    matches_played = len(matches)
    
    return {
        'h2h_wins': wins,
        'h2h_draws': draws,
        'h2h_losses': losses,
        'goals_scored': goals_for,
        'goals_conceded': goals_against,
        'matches_played': matches_played,
        'home_wins': home_wins,
        'away_wins': away_wins,
        'recent_form': recent_form,
        'avg_goals_for': goals_for / matches_played if matches_played > 0 else 0,
        'avg_goals_against': goals_against / matches_played if matches_played > 0 else 0
    }

def calculate_enhanced_h2h_score(h2h_data):
    """Calculate enhanced H2H strength score with more factors"""
    matches = h2h_data['matches_played']
    
    if matches == 0:
        return 50.0  # Neutral score if no H2H data
    
    wins = h2h_data['h2h_wins']
    draws = h2h_data['h2h_draws']
    losses = h2h_data['h2h_losses']
    goals_for = h2h_data['goals_scored']
    goals_against = h2h_data['goals_conceded']
    
    # Base points system (3 for win, 1 for draw)
    points = (wins * 3) + (draws * 1)
    max_points = matches * 3
    points_ratio = points / max_points if max_points > 0 else 0
    
    # Goal difference factor
    goal_diff = goals_for - goals_against
    goal_diff_per_match = goal_diff / matches if matches > 0 else 0
    
    # Recent form weight (more recent matches count more)
    recent_form_score = 0
    recent_matches = h2h_data['recent_form'][:5]  # Last 5 matches
    for i, match in enumerate(recent_matches):
        weight = 1.0 - (i * 0.15)  # Decreasing weight: 1.0, 0.85, 0.7, 0.55, 0.4
        if match['result'] == 'W':
            recent_form_score += 3 * weight
        elif match['result'] == 'D':
            recent_form_score += 1 * weight
    
    max_recent_score = sum([3 * (1.0 - (i * 0.15)) for i in range(min(5, len(recent_matches)))])
    recent_form_ratio = recent_form_score / max_recent_score if max_recent_score > 0 else 0
    
    # Home/Away balance (bonus for winning both home and away)
    home_away_balance = 0
    if h2h_data['home_wins'] > 0 and h2h_data['away_wins'] > 0:
        home_away_balance = 5  # Bonus for versatility
    
    # Combine factors
    base_score = points_ratio * 60  # 0-60 range
    goal_bonus = max(-10, min(10, goal_diff_per_match * 8))  # -10 to +10
    recent_bonus = recent_form_ratio * 15  # 0-15 range
    balance_bonus = home_away_balance  # 0-5 range
    
    final_score = base_score + goal_bonus + recent_bonus + balance_bonus
    
    # Ensure score is between 0-100
    return max(0, min(100, final_score))

def update_local_h2h_performance(competition_name=None):
    """Update H2H performance using local match data"""
    print("📊 LOCAL H2H PERFORMANCE ANALYSIS")
    print("=" * 60)
    print("🎯 Using stored match data for instant analysis")
    
    conn = get_database_connection()
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON;")
    
    # Get competitions to process
    if competition_name:
        c.execute("SELECT id, name FROM competitions WHERE name = ?", (competition_name,))
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
        
        # Calculate H2H scores for each team against all others in competition
        team_h2h_scores = {}
        
        for i, (team1_id, team1_name, _) in enumerate(competition_teams):
            h2h_results = []
            detailed_stats = {
                'total_matches': 0,
                'total_goals_for': 0,
                'total_goals_against': 0,
                'recent_form_points': 0
            }
            
            for j, (team2_id, team2_name, _) in enumerate(competition_teams):
                if i == j:  # Skip self
                    continue
                
                # Analyze H2H between these teams
                h2h_data = analyze_h2h_performance_local(team1_name, team2_name, comp_id)
                
                if h2h_data['matches_played'] > 0:
                    score = calculate_enhanced_h2h_score(h2h_data)
                    h2h_results.append(score)
                    
                    # Accumulate detailed stats
                    detailed_stats['total_matches'] += h2h_data['matches_played']
                    detailed_stats['total_goals_for'] += h2h_data['goals_scored']
                    detailed_stats['total_goals_against'] += h2h_data['goals_conceded']
                    
                    # Add to recent form points
                    for match in h2h_data['recent_form']:
                        if match['result'] == 'W':
                            detailed_stats['recent_form_points'] += 3
                        elif match['result'] == 'D':
                            detailed_stats['recent_form_points'] += 1
            
            # Calculate average H2H performance across all opponents
            if h2h_results:
                avg_h2h_score = sum(h2h_results) / len(h2h_results)
                team_h2h_scores[team1_id] = avg_h2h_score
                
                # Enhanced reporting
                matches_count = detailed_stats['total_matches']
                gf_avg = detailed_stats['total_goals_for'] / matches_count if matches_count > 0 else 0
                ga_avg = detailed_stats['total_goals_against'] / matches_count if matches_count > 0 else 0
                
                print(f"   📈 {team1_name}: {avg_h2h_score:.1f} ({matches_count} H2H matches, {gf_avg:.1f} GF/match, {ga_avg:.1f} GA/match)")
            else:
                team_h2h_scores[team1_id] = 50.0  # Neutral score
                print(f"   📊 {team1_name}: 50.0 (no H2H data)")
        
        # Update database with H2H scores
        if team_h2h_scores:
            update_competition_metric(
                comp_id, "h2h_performance", "h2h_normalized", team_h2h_scores, conn
            )
            print(f"   ✅ Updated {len(team_h2h_scores)} teams with enhanced H2H scores")
    
    # Show match data statistics
    c.execute("SELECT COUNT(*) FROM matches")
    total_matches = c.fetchone()[0]
    
    c.execute("SELECT competition_name, COUNT(*) FROM matches GROUP BY competition_name ORDER BY COUNT(*) DESC")
    matches_by_league = c.fetchall()
    
    print(f"\n📈 MATCH DATABASE STATISTICS:")
    print(f"   Total stored matches: {total_matches}")
    for league, count in matches_by_league:
        print(f"   {league}: {count} matches")
    
    conn.commit()
    conn.close()
    print(f"\n✅ Local H2H Performance analysis complete!")

if __name__ == "__main__":
    # Process all domestic leagues using local data
    update_local_h2h_performance()