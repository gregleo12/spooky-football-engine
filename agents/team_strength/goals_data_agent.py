#!/usr/bin/env python3
"""
Goals Data Agent - Phase 1 Parameter Implementation
Calculates offensive and defensive ratings based on goals scored/conceded data
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
    """Fetch team statistics including goals scored/conceded"""
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

def calculate_offensive_rating(goals_for, matches_played, league_average_goals=2.5):
    """Calculate offensive rating based on goals scored"""
    if matches_played == 0:
        return FALLBACK_SCORE
    
    goals_per_game = goals_for / matches_played
    
    # Compare to league average (2.5 goals per game is typical)
    offensive_ratio = goals_per_game / league_average_goals
    
    # Scale to 0-2 range (2.0 = exceptional, 1.0 = average, 0.5 = poor)
    offensive_rating = min(2.0, max(0.0, offensive_ratio))
    
    return round(offensive_rating, 3)

def calculate_defensive_rating(goals_against, matches_played, league_average_goals=2.5):
    """Calculate defensive rating based on goals conceded (inverted - lower conceded = higher rating)"""
    if matches_played == 0:
        return FALLBACK_SCORE
    
    goals_per_game = goals_against / matches_played
    
    # Invert for defensive rating (lower goals conceded = better defense)
    # If team concedes league average, they get 1.0 rating
    # If they concede half the average, they get 2.0 rating
    # If they concede double the average, they get 0.5 rating
    defensive_ratio = league_average_goals / goals_per_game if goals_per_game > 0 else 2.0
    
    # Scale to 0-2 range
    defensive_rating = min(2.0, max(0.0, defensive_ratio))
    
    return round(defensive_rating, 3)

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

def update_goals_data(competition_name=None):
    """Update offensive and defensive ratings for specified competition or all competitions"""
    print("⚽ GOALS DATA ANALYSIS - PHASE 1 PARAMETERS")
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
            
        print(f"\n⚽ Processing {comp_name}")
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
        
        goals_data = {}
        
        # Analyze each team's goals data
        for i, (team_id, team_name) in enumerate(competition_teams, 1):
            print(f"[{i}/{len(competition_teams)}] Processing {team_name}...")
            
            # Get API ID from mapping
            api_team_id = TEAM_API_IDS.get(team_name)
            
            if not api_team_id:
                print(f"   ⚠️ No API ID for {team_name}")
                goals_data[team_id] = {
                    "team_name": team_name,
                    "offensive_rating": FALLBACK_SCORE,
                    "defensive_rating": FALLBACK_SCORE,
                    "goals_for": 0,
                    "goals_against": 0,
                    "matches_played": 0
                }
                continue

            try:
                # Fetch team statistics
                stats = fetch_team_statistics(api_team_id, league_id, team_name)
                
                if not stats:
                    goals_data[team_id] = {
                        "team_name": team_name,
                        "offensive_rating": FALLBACK_SCORE,
                        "defensive_rating": FALLBACK_SCORE,
                        "goals_for": 0,
                        "goals_against": 0,
                        "matches_played": 0
                    }
                    continue
                
                # Extract goals data
                fixtures = stats.get('fixtures', {})
                goals = stats.get('goals', {})
                
                matches_played = fixtures.get('played', {}).get('total', 0)
                goals_for = goals.get('for', {}).get('total', {}).get('total', 0)
                goals_against = goals.get('against', {}).get('total', {}).get('total', 0)
                
                # Calculate ratings
                offensive_rating = calculate_offensive_rating(goals_for, matches_played)
                defensive_rating = calculate_defensive_rating(goals_against, matches_played)
                
                goals_data[team_id] = {
                    "team_name": team_name,
                    "offensive_rating": offensive_rating,
                    "defensive_rating": defensive_rating,
                    "goals_for": goals_for,
                    "goals_against": goals_against,
                    "matches_played": matches_played
                }
                
                print(f"   📊 Matches: {matches_played}, Goals: {goals_for}-{goals_against}")
                print(f"   ⚔️ Offensive rating: {offensive_rating}")
                print(f"   🛡️ Defensive rating: {defensive_rating}")
                
            except Exception as e:
                print(f"   ❌ Failed for {team_name}: {e}")
                goals_data[team_id] = {
                    "team_name": team_name,
                    "offensive_rating": FALLBACK_SCORE,
                    "defensive_rating": FALLBACK_SCORE,
                    "goals_for": 0,
                    "goals_against": 0,
                    "matches_played": 0
                }
        
        # Normalize scores within this competition
        print(f"\n📊 Normalizing {comp_name} scores...")
        goals_data = normalize_competition_scores(goals_data, 'offensive_rating')
        goals_data = normalize_competition_scores(goals_data, 'defensive_rating')
        
        # Update database
        print(f"💾 Updating database for {comp_name}...")
        
        for team_id, data in goals_data.items():
            c.execute("""
                UPDATE competition_team_strength 
                SET offensive_rating = ?, offensive_normalized = ?,
                    defensive_rating = ?, defensive_normalized = ?,
                    goals_per_game = ?, goals_conceded_per_game = ?,
                    last_updated = ?
                WHERE team_id = ? AND competition_id = ? AND season = ?
            """, (
                data['offensive_rating'], data['offensive_rating_normalized'],
                data['defensive_rating'], data['defensive_rating_normalized'],
                data['goals_for'] / max(1, data['matches_played']),
                data['goals_against'] / max(1, data['matches_played']),
                datetime.now(timezone.utc), team_id, comp_id, SEASON
            ))
            
            print(f"   ✅ {data['team_name']}: OFF {data['offensive_rating']} → {data['offensive_rating_normalized']}, DEF {data['defensive_rating']} → {data['defensive_rating_normalized']}")
        
        # Show competition summary
        off_scores = [data['offensive_rating_normalized'] for data in goals_data.values()]
        def_scores = [data['defensive_rating_normalized'] for data in goals_data.values()]
        if off_scores and def_scores:
            print(f"\n📈 {comp_name} Summary:")
            print(f"   Offensive range: {min(off_scores):.3f} - {max(off_scores):.3f}")
            print(f"   Defensive range: {min(def_scores):.3f} - {max(def_scores):.3f}")
            print(f"   Teams analyzed: {len(goals_data)}")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Goals data analysis complete!")

if __name__ == "__main__":
    # Process all domestic leagues
    update_goals_data()