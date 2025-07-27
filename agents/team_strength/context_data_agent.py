#!/usr/bin/env python3
"""
Context Data Agent - Phase 1 Parameter Implementation
Calculates home advantage based on home vs away performance analysis
"""
import sqlite3
import requests
import json
import uuid
import os
from datetime import datetime, timezone
from collections import defaultdict

API_KEY = "53faec37f076f995841d30d0f7b2dd9d"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}
SEASON = 2024
FALLBACK_SCORE = 0.5

# Load team API ID mapping
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEAM_API_IDS_PATH = os.path.join(SCRIPT_DIR, "..", "shared", "team_api_ids.json")

try:
    with open(TEAM_API_IDS_PATH, 'r', encoding='utf-8') as f:
        TEAM_API_IDS = json.load(f)
except FileNotFoundError:
    print(f"⚠️ Warning: team_api_ids.json not found at {TEAM_API_IDS_PATH}")
    TEAM_API_IDS = {}

def fetch_team_statistics(team_api_id, league_id, team_name):
    """Fetch team statistics including home/away performance"""
    url = f"{BASE_URL}/teams/statistics"
    params = {
        "team": team_api_id,
        "league": league_id,
        "season": SEASON
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=15)
        data = response.json()
        
        if response.status_code != 200:
            print(f"   ⚠️ API Error {response.status_code} for {team_name}")
            return None
        
        return data.get("response", {})
        
    except Exception as e:
        print(f"   ❌ Error fetching statistics for {team_name}: {e}")
        return None

def calculate_home_advantage(home_stats, away_stats):
    """Calculate home advantage based on home vs away performance"""
    
    # Extract home performance
    home_matches = home_stats.get('played', 0)
    home_wins = home_stats.get('wins', 0)
    home_draws = home_stats.get('draws', 0)
    home_goals_for = home_stats.get('goals', {}).get('for', 0)
    home_goals_against = home_stats.get('goals', {}).get('against', 0)
    
    # Extract away performance
    away_matches = away_stats.get('played', 0)
    away_wins = away_stats.get('wins', 0)
    away_draws = away_stats.get('draws', 0)
    away_goals_for = away_stats.get('goals', {}).get('for', 0)
    away_goals_against = away_stats.get('goals', {}).get('against', 0)
    
    if home_matches == 0 or away_matches == 0:
        return FALLBACK_SCORE
    
    # Calculate points per game (3 for win, 1 for draw)
    home_points = (home_wins * 3) + (home_draws * 1)
    away_points = (away_wins * 3) + (away_draws * 1)
    
    home_ppg = home_points / home_matches
    away_ppg = away_points / away_matches
    
    # Calculate goals per game ratios
    home_goals_ratio = (home_goals_for / home_matches) - (home_goals_against / home_matches)
    away_goals_ratio = (away_goals_for / away_matches) - (away_goals_against / away_matches)
    
    # Home advantage calculation
    # 60% based on points per game difference
    # 40% based on goal difference improvement
    
    ppg_advantage = home_ppg - away_ppg  # Range typically -3 to +3
    goals_advantage = home_goals_ratio - away_goals_ratio  # Range typically -2 to +2
    
    # Normalize to 0-2 scale (1.0 = no advantage, >1.0 = positive advantage, <1.0 = negative)
    # PPG component: scale -3 to +3 range to -0.5 to +0.5, then add 1.0
    ppg_component = max(-0.5, min(0.5, ppg_advantage / 6)) + 1.0
    
    # Goals component: scale -2 to +2 range to -0.25 to +0.25, then add to base
    goals_component = max(-0.25, min(0.25, goals_advantage / 8))
    
    home_advantage = (ppg_component * 0.6) + ((1.0 + goals_component) * 0.4)
    
    # Clamp to 0-2 range
    home_advantage = max(0.0, min(2.0, home_advantage))
    
    return round(home_advantage, 3)

def normalize_competition_scores(competition_data, metric_key):
    """Normalize scores within competition (0-1 scale)"""
    if not competition_data:
        return competition_data
    
    scores = [data[metric_key] for data in competition_data.values() if data[metric_key] is not None]
    
    if not scores or len(set(scores)) == 1:
        # All teams have same score, assign 0.5 to all
        for team_data in competition_data.values():
            team_data[f'{metric_key}_normalized'] = 0.5
        return competition_data
    
    min_score = min(scores)
    max_score = max(scores)
    score_range = max_score - min_score
    
    # Normalize each team's score within competition
    for team_data in competition_data.values():
        if team_data[metric_key] is not None and score_range > 0:
            normalized = (team_data[metric_key] - min_score) / score_range
        else:
            normalized = 0.5
        team_data[f'{metric_key}_normalized'] = round(normalized, 3)
    
    return competition_data

def update_context_data(competition_name=None):
    """Update home advantage for specified competition or all competitions"""
    print("🏠 CONTEXT DATA ANALYSIS - PHASE 1 PARAMETERS")
    print("=" * 60)
    
    conn = sqlite3.connect("db/football_strength.db")
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON;")
    
    # League ID mapping for API calls
    league_ids = {
        'Premier League': 39,
        'La Liga': 140,
        'Serie A': 135,
        'Bundesliga': 78,
        'Ligue 1': 61
    }
    
    # Get competitions to process
    if competition_name:
        c.execute("SELECT id, name FROM competitions WHERE name = ?", (competition_name,))
    else:
        c.execute("SELECT id, name FROM competitions WHERE type = 'domestic_league'")
    
    competitions = c.fetchall()
    
    for comp_id, comp_name in competitions:
        if comp_name not in league_ids:
            print(f"⚠️ Skipping {comp_name} - no league ID mapping")
            continue
            
        print(f"\n🏠 Processing {comp_name}")
        print("-" * 40)
        
        league_id = league_ids[comp_name]
        
        # Get teams in this competition
        c.execute("""
            SELECT cts.team_id, cts.team_name
            FROM competition_team_strength cts
            WHERE cts.competition_id = ? AND cts.season = ?
            AND cts.team_name IS NOT NULL
        """, (comp_id, SEASON))
        
        competition_teams = c.fetchall()
        
        if not competition_teams:
            print(f"   ⚠️ No teams found for {comp_name}")
            continue
        
        context_data = {}
        
        # Analyze each team's home advantage
        for i, (team_id, team_name) in enumerate(competition_teams, 1):
            print(f"[{i}/{len(competition_teams)}] Processing {team_name}...")
            
            # Get API ID from mapping
            api_team_id = TEAM_API_IDS.get(team_name)
            
            if not api_team_id:
                print(f"   ⚠️ No API ID for {team_name}")
                context_data[team_id] = {
                    "team_name": team_name,
                    "home_advantage": FALLBACK_SCORE,
                    "home_ppg": 0,
                    "away_ppg": 0
                }
                continue

            try:
                # Fetch team statistics
                stats = fetch_team_statistics(api_team_id, league_id, team_name)
                
                if not stats:
                    context_data[team_id] = {
                        "team_name": team_name,
                        "home_advantage": FALLBACK_SCORE,
                        "home_ppg": 0,
                        "away_ppg": 0
                    }
                    continue
                
                # Extract home/away data
                fixtures = stats.get('fixtures', {})
                home_stats = fixtures.get('played', {}).get('home', 0)
                away_stats = fixtures.get('played', {}).get('away', 0)
                
                wins = stats.get('fixtures', {}).get('wins', {})
                draws = stats.get('fixtures', {}).get('draws', {})
                goals = stats.get('goals', {})
                
                # Build home/away performance data
                home_performance = {
                    'played': home_stats,
                    'wins': wins.get('home', 0),
                    'draws': draws.get('home', 0),
                    'goals': {
                        'for': goals.get('for', {}).get('total', {}).get('home', 0),
                        'against': goals.get('against', {}).get('total', {}).get('home', 0)
                    }
                }
                
                away_performance = {
                    'played': away_stats,
                    'wins': wins.get('away', 0),
                    'draws': draws.get('away', 0),
                    'goals': {
                        'for': goals.get('for', {}).get('total', {}).get('away', 0),
                        'against': goals.get('against', {}).get('total', {}).get('away', 0)
                    }
                }
                
                # Calculate home advantage
                home_advantage = calculate_home_advantage(home_performance, away_performance)
                
                # Calculate PPG for display
                home_ppg = 0
                away_ppg = 0
                if home_performance['played'] > 0:
                    home_points = (home_performance['wins'] * 3) + (home_performance['draws'] * 1)
                    home_ppg = home_points / home_performance['played']
                if away_performance['played'] > 0:
                    away_points = (away_performance['wins'] * 3) + (away_performance['draws'] * 1)
                    away_ppg = away_points / away_performance['played']
                
                context_data[team_id] = {
                    "team_name": team_name,
                    "home_advantage": home_advantage,
                    "home_ppg": round(home_ppg, 2),
                    "away_ppg": round(away_ppg, 2)
                }
                
                print(f"   🏠 Home PPG: {home_ppg:.2f}, Away PPG: {away_ppg:.2f}")
                print(f"   📈 Home advantage: {home_advantage}")
                
            except Exception as e:
                print(f"   ❌ Failed for {team_name}: {e}")
                context_data[team_id] = {
                    "team_name": team_name,
                    "home_advantage": FALLBACK_SCORE,
                    "home_ppg": 0,
                    "away_ppg": 0
                }
        
        # Normalize scores within this competition
        print(f"\n📊 Normalizing {comp_name} scores...")
        context_data = normalize_competition_scores(context_data, 'home_advantage')
        
        # Update database
        print(f"💾 Updating database for {comp_name}...")
        
        for team_id, data in context_data.items():
            c.execute("""
                UPDATE competition_team_strength 
                SET home_advantage = ?, home_advantage_normalized = ?,
                    overall_home_advantage = ?,
                    last_updated = ?
                WHERE team_id = ? AND competition_id = ? AND season = ?
            """, (
                data['home_advantage'], data['home_advantage_normalized'],
                data['home_advantage'],
                datetime.now(timezone.utc), team_id, comp_id, SEASON
            ))
            
            print(f"   ✅ {data['team_name']}: {data['home_advantage']} → {data['home_advantage_normalized']} (PPG: {data['home_ppg']:.2f}H/{data['away_ppg']:.2f}A)")
        
        # Show competition summary
        scores = [data['home_advantage_normalized'] for data in context_data.values()]
        if scores:
            print(f"\n📈 {comp_name} Summary:")
            print(f"   Home advantage range: {min(scores):.3f} - {max(scores):.3f}")
            print(f"   Teams analyzed: {len(context_data)}")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Context data analysis complete!")

if __name__ == "__main__":
    # Process all domestic leagues
    update_context_data()