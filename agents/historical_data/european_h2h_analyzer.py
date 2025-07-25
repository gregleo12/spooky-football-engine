#!/usr/bin/env python3
"""
European Competition H2H Analyzer
Analyzes head-to-head performance in European competitions (Champions League, Europa League)
Provides additional context for teams' continental performance
"""
import sqlite3
import sys
import os
from datetime import datetime
from collections import defaultdict

def get_database_connection():
    """Get database connection"""
    return sqlite3.connect("db/football_strength.db")

def analyze_european_h2h_performance(team_name, limit=20):
    """Analyze European competition H2H performance for a team"""
    conn = get_database_connection()
    c = conn.cursor()
    
    # Get European matches for this team
    c.execute("""
        SELECT 
            home_team_name, away_team_name, home_score, away_score,
            match_date, season, competition_name
        FROM matches 
        WHERE competition_name IN ('Champions League', 'Europa League')
        AND (home_team_name = ? OR away_team_name = ?)
        AND status = 'FT'
        ORDER BY match_date DESC
        LIMIT ?
    """, (team_name, team_name, limit))
    
    matches = c.fetchall()
    conn.close()
    
    if not matches:
        return {
            'total_matches': 0,
            'champions_league_matches': 0,
            'europa_league_matches': 0,
            'wins': 0,
            'draws': 0,
            'losses': 0,
            'goals_scored': 0,
            'goals_conceded': 0,
            'clean_sheets': 0,
            'avg_goals_per_match': 0.0,
            'european_experience_score': 0.0
        }
    
    # Analyze European performance
    champions_league_matches = 0
    europa_league_matches = 0
    wins = draws = losses = 0
    goals_scored = goals_conceded = 0
    clean_sheets = 0
    
    competition_weights = {
        'Champions League': 1.0,  # Higher weight for CL
        'Europa League': 0.8     # Lower weight for EL
    }
    
    weighted_points = 0
    total_weight = 0
    
    for match in matches:
        home_team, away_team, home_score, away_score, match_date, season, competition = match
        
        # Count competition participation
        if competition == 'Champions League':
            champions_league_matches += 1
        else:
            europa_league_matches += 1
        
        # Determine if team was home or away
        if home_team == team_name:
            team_goals = home_score
            opponent_goals = away_score
        else:
            team_goals = away_score
            opponent_goals = home_score
        
        goals_scored += team_goals
        goals_conceded += opponent_goals
        
        if opponent_goals == 0:
            clean_sheets += 1
        
        # Determine result and add weighted points
        weight = competition_weights[competition]
        total_weight += weight
        
        if team_goals > opponent_goals:
            wins += 1
            weighted_points += 3 * weight  # 3 points for win
        elif team_goals < opponent_goals:
            losses += 1
            # 0 points for loss
        else:
            draws += 1
            weighted_points += 1 * weight  # 1 point for draw
    
    total_matches = len(matches)
    avg_goals_per_match = goals_scored / total_matches if total_matches > 0 else 0
    
    # Calculate European experience score (0-100)
    # Based on: participation frequency, performance, competition level
    if total_matches == 0:
        european_experience_score = 0.0
    else:
        # Base experience from participation
        participation_score = min(50, total_matches * 2.5)  # Up to 50 points for 20+ matches
        
        # Performance bonus
        if total_weight > 0:
            performance_ratio = weighted_points / (total_weight * 3)  # Normalize to 0-1
            performance_score = performance_ratio * 40  # Up to 40 points
        else:
            performance_score = 0
        
        # Competition level bonus (CL participation is valued higher)
        cl_bonus = min(10, champions_league_matches * 1)  # Up to 10 bonus points
        
        european_experience_score = participation_score + performance_score + cl_bonus
    
    return {
        'total_matches': total_matches,
        'champions_league_matches': champions_league_matches,
        'europa_league_matches': europa_league_matches,
        'wins': wins,
        'draws': draws,
        'losses': losses,
        'goals_scored': goals_scored,
        'goals_conceded': goals_conceded,
        'clean_sheets': clean_sheets,
        'avg_goals_per_match': avg_goals_per_match,
        'european_experience_score': european_experience_score,
        'win_rate': (wins / total_matches * 100) if total_matches > 0 else 0
    }

def generate_european_insights():
    """Generate insights about European performance for database teams"""
    print("🏆 EUROPEAN COMPETITION INSIGHTS")
    print("=" * 70)
    print("📊 Analyzing Champions League & Europa League performance")
    print("🎯 Based on matches involving teams from our 5 domestic leagues")
    print("")
    
    conn = get_database_connection()
    c = conn.cursor()
    
    # Get all teams from domestic leagues
    c.execute("""
        SELECT DISTINCT t.name 
        FROM teams t
        JOIN competition_team_strength cts ON t.id = cts.team_id
        JOIN competitions c ON cts.competition_id = c.id
        WHERE c.type = 'domestic_league'
        ORDER BY t.name
    """)
    
    teams = [row[0] for row in c.fetchall()]
    
    # Analyze European performance for each team
    european_performers = []
    
    for team_name in teams:
        european_data = analyze_european_h2h_performance(team_name)
        
        if european_data['total_matches'] > 0:
            european_performers.append({
                'team': team_name,
                'matches': european_data['total_matches'],
                'cl_matches': european_data['champions_league_matches'],
                'el_matches': european_data['europa_league_matches'],
                'wins': european_data['wins'],
                'draws': european_data['draws'],
                'losses': european_data['losses'],
                'goals_per_match': european_data['avg_goals_per_match'],
                'win_rate': european_data['win_rate'],
                'experience_score': european_data['european_experience_score']
            })
    
    # Sort by experience score
    european_performers.sort(key=lambda x: x['experience_score'], reverse=True)
    
    print(f"🎯 TOP EUROPEAN PERFORMERS FROM DATABASE TEAMS:")
    print("-" * 80)
    print(f"{'Rank':<4} {'Team':<25} {'Matches':<8} {'CL':<4} {'EL':<4} {'W-D-L':<8} {'Goals/M':<8} {'Experience':<10}")
    print("-" * 80)
    
    for i, team in enumerate(european_performers[:15], 1):  # Top 15
        rank_emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i:2d}."
        wdl = f"{team['wins']}-{team['draws']}-{team['losses']}"
        
        print(f"{rank_emoji:<4} {team['team']:<25} {team['matches']:<8} "
              f"{team['cl_matches']:<4} {team['el_matches']:<4} {wdl:<8} "
              f"{team['goals_per_match']:<8.1f} {team['experience_score']:<10.1f}")
    
    # Competition statistics
    c.execute("""
        SELECT competition_name, COUNT(*) as matches,
               COUNT(DISTINCT home_team_name) + COUNT(DISTINCT away_team_name) as unique_teams
        FROM matches 
        WHERE competition_name IN ('Champions League', 'Europa League')
        GROUP BY competition_name
    """)
    
    comp_stats = c.fetchall()
    
    print(f"\n📈 EUROPEAN COMPETITION STATISTICS:")
    print("-" * 50)
    for comp, matches, teams in comp_stats:
        print(f"   {comp}: {matches} matches involving our teams")
    
    # Most active teams in Europe
    print(f"\n🌍 MOST ACTIVE TEAMS IN EUROPEAN COMPETITIONS:")
    print("-" * 60)
    most_active = sorted(european_performers, key=lambda x: x['matches'], reverse=True)[:10]
    
    for i, team in enumerate(most_active, 1):
        print(f"   {i:2d}. {team['team']:<25} {team['matches']} European matches "
              f"(CL: {team['cl_matches']}, EL: {team['el_matches']})")
    
    # Teams with highest win rates (min 5 matches)
    print(f"\n🏅 HIGHEST EUROPEAN WIN RATES (5+ matches):")
    print("-" * 60)
    high_win_rate = [t for t in european_performers if t['matches'] >= 5]
    high_win_rate.sort(key=lambda x: x['win_rate'], reverse=True)
    
    for i, team in enumerate(high_win_rate[:10], 1):
        print(f"   {i:2d}. {team['team']:<25} {team['win_rate']:<5.1f}% "
              f"({team['wins']}W-{team['draws']}D-{team['losses']}L in {team['matches']} matches)")
    
    conn.close()
    
    print(f"\n📊 SUMMARY:")
    print(f"   Teams with European experience: {len(european_performers)}")
    print(f"   Total European matches analyzed: {sum(t['matches'] for t in european_performers)}")
    print(f"   Average European experience score: {sum(t['experience_score'] for t in european_performers) / len(european_performers):.1f}" if european_performers else "   No European data available")

if __name__ == "__main__":
    generate_european_insights()