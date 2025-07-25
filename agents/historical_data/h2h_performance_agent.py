#!/usr/bin/env python3
"""
Head-to-Head Performance Agent
Analyzes historical match data between teams to calculate H2H performance scores
"""
import sqlite3
import requests
import json
import os
import sys
from datetime import datetime, timedelta

# Add shared utilities to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from competition_normalizer import update_competition_metric, get_competition_teams

# API Configuration
API_KEY = "53faec37f076f995841d30d0f7b2dd9d"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

# Load team API IDs
def load_team_api_ids():
    team_ids_path = os.path.join(os.path.dirname(__file__), '..', 'shared', 'team_api_ids.json')
    try:
        with open(team_ids_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load team API IDs: {e}")
        return {}

def analyze_h2h_performance(team1_name, team1_id, team2_name, team2_id):
    """Analyze head-to-head performance between two teams"""
    
    # Fetch H2H data from API
    url = f"{BASE_URL}/fixtures/headtohead"
    params = {
        "h2h": f"{team1_id}-{team2_id}",
        "last": 10  # Last 10 H2H matches
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        data = response.json()
        
        if response.status_code != 200 or not data.get('response'):
            return {
                'h2h_wins': 0,
                'h2h_draws': 0,
                'h2h_losses': 0,
                'goals_scored': 0,
                'goals_conceded': 0,
                'matches_played': 0
            }
        
        wins = draws = losses = 0
        goals_for = goals_against = 0
        matches = 0
        
        for fixture in data['response']:
            # Only count finished matches
            if fixture.get('fixture', {}).get('status', {}).get('short') != 'FT':
                continue
                
            home_team_id = fixture['teams']['home']['id']
            away_team_id = fixture['teams']['away']['id']
            home_goals = fixture['goals']['home']
            away_goals = fixture['goals']['away']
            
            if home_goals is None or away_goals is None:
                continue
                
            matches += 1
            
            # Determine if team1 was home or away
            if home_team_id == team1_id:
                # Team1 was home
                goals_for += home_goals
                goals_against += away_goals
                
                if home_goals > away_goals:
                    wins += 1
                elif home_goals < away_goals:
                    losses += 1
                else:
                    draws += 1
            else:
                # Team1 was away
                goals_for += away_goals
                goals_against += home_goals
                
                if away_goals > home_goals:
                    wins += 1
                elif away_goals < home_goals:
                    losses += 1
                else:
                    draws += 1
        
        return {
            'h2h_wins': wins,
            'h2h_draws': draws,
            'h2h_losses': losses,
            'goals_scored': goals_for,
            'goals_conceded': goals_against,
            'matches_played': matches
        }
        
    except Exception as e:
        print(f"Error analyzing H2H for {team1_name} vs {team2_name}: {e}")
        return {
            'h2h_wins': 0,
            'h2h_draws': 0,
            'h2h_losses': 0,
            'goals_scored': 0,
            'goals_conceded': 0,
            'matches_played': 0
        }

def calculate_h2h_strength_score(h2h_data):
    """Calculate strength score based on H2H performance"""
    matches = h2h_data['matches_played']
    
    if matches == 0:
        return 50.0  # Neutral score if no H2H data
    
    wins = h2h_data['h2h_wins']
    draws = h2h_data['h2h_draws']
    losses = h2h_data['h2h_losses']
    goals_for = h2h_data['goals_scored']
    goals_against = h2h_data['goals_conceded']
    
    # Points-based scoring (3 for win, 1 for draw)
    points = (wins * 3) + (draws * 1)
    max_points = matches * 3
    points_ratio = points / max_points if max_points > 0 else 0
    
    # Goal difference factor
    goal_diff = goals_for - goals_against
    goal_diff_per_match = goal_diff / matches if matches > 0 else 0
    
    # Base score from points (0-70 range)
    base_score = points_ratio * 70
    
    # Goal difference bonus/penalty (-15 to +15 range)
    goal_bonus = max(-15, min(15, goal_diff_per_match * 10))
    
    # Recent form bonus (more recent matches weighted higher)
    # This could be enhanced to weight recent matches more
    recent_form_bonus = 0
    
    # Combine all factors
    final_score = base_score + goal_bonus + recent_form_bonus
    
    # Ensure score is between 0-100
    return max(0, min(100, final_score))

def update_h2h_performance_scores(competition_name=None):
    """Update H2H performance scores for all teams in a competition"""
    print("📊 H2H PERFORMANCE ANALYSIS")
    print("=" * 60)
    
    conn = sqlite3.connect("db/football_strength.db")
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON;")
    
    # Get competitions to process
    if competition_name:
        c.execute("SELECT id, name FROM competitions WHERE name = ?", (competition_name,))
    else:
        c.execute("SELECT id, name FROM competitions WHERE type = 'domestic_league'")
    
    competitions = c.fetchall()
    team_api_ids = load_team_api_ids()
    
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
        
        for i, (team1_id, team1_name, team1_api_id) in enumerate(competition_teams):
            if team1_name not in team_api_ids:
                print(f"   ⚠️ No API ID for {team1_name}")
                continue
                
            h2h_results = []
            team1_api = team_api_ids[team1_name]
            
            for j, (team2_id, team2_name, team2_api_id) in enumerate(competition_teams):
                if i == j or team2_name not in team_api_ids:
                    continue
                
                team2_api = team_api_ids[team2_name]
                
                # Analyze H2H between these teams
                h2h_data = analyze_h2h_performance(team1_name, team1_api, team2_name, team2_api)
                
                if h2h_data['matches_played'] > 0:
                    score = calculate_h2h_strength_score(h2h_data)
                    h2h_results.append(score)
            
            # Average H2H performance across all opponents
            if h2h_results:
                avg_h2h_score = sum(h2h_results) / len(h2h_results)
                team_h2h_scores[team1_id] = avg_h2h_score
                print(f"   📈 {team1_name}: {avg_h2h_score:.1f} (from {len(h2h_results)} H2H records)")
            else:
                team_h2h_scores[team1_id] = 50.0  # Neutral score
                print(f"   📊 {team1_name}: 50.0 (no H2H data)")
        
        # Update database with H2H scores
        if team_h2h_scores:
            update_competition_metric(
                comp_id, "h2h_performance", "h2h_normalized", team_h2h_scores, conn
            )
            print(f"   ✅ Updated {len(team_h2h_scores)} teams with H2H performance scores")
    
    conn.commit()
    conn.close()
    print(f"\n✅ H2H Performance analysis complete!")

if __name__ == "__main__":
    # Process all domestic leagues
    leagues = ["Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1"]
    
    for league in leagues:
        try:
            update_h2h_performance_scores(league)
        except Exception as e:
            print(f"❌ Error processing {league}: {e}")
            continue