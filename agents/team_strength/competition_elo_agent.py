#!/usr/bin/env python3
"""
Competition-aware ELO agent with per-competition normalization
Calculates ELO ratings for teams within each league competition
"""
import requests
import json
import uuid
from datetime import datetime, timezone
import sys
import os

# Add project root to path for database config
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from database_config import db_config

# Add shared utilities to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from competition_normalizer import update_competition_metric, get_competition_teams

API_KEY = '53faec37f076f995841d30d0f7b2dd9d'
BASE_URL = 'https://v3.football.api-sports.io'
HEADERS = {"x-apisports-key": API_KEY}
SEASON = 2024

# ELO rating parameters
INITIAL_ELO = 1500
K_FACTOR = 20

def fetch_league_fixtures(league_api_id, league_name):
    """Fetch all fixtures from current season for ELO calculation"""
    print(f"   🔍 Fetching fixtures from {league_name}...")
    
    url = f"{BASE_URL}/fixtures"
    params = {
        "league": league_api_id,
        "season": SEASON
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        data = response.json()
        
        if response.status_code != 200:
            print(f"   ❌ API Error {response.status_code} for {league_name}")
            return []
        
        fixtures = data.get("response", [])
        print(f"   ✅ Found {len(fixtures)} fixtures in {league_name}")
        
        return fixtures
        
    except Exception as e:
        print(f"   ❌ Error fetching {league_name} fixtures: {e}")
        return []

def calculate_elo_ratings(fixtures, team_api_mapping):
    """Calculate ELO ratings from fixture results"""
    team_elos = {}
    
    # Initialize all teams with starting ELO
    for team_name in team_api_mapping.keys():
        team_elos[team_name] = INITIAL_ELO
    
    processed_fixtures = 0
    
    for fixture in fixtures:
        # Only process finished matches
        if fixture.get("fixture", {}).get("status", {}).get("short") != 'FT':
            continue
            
        teams = fixture.get("teams", {})
        goals = fixture.get("goals", {})
        
        home_team_id = teams.get("home", {}).get("id")
        away_team_id = teams.get("away", {}).get("id")
        home_goals = goals.get("home")
        away_goals = goals.get("away")
        
        if not all([home_team_id, away_team_id, home_goals is not None, away_goals is not None]):
            continue
        
        # Find team names from API IDs
        home_team_name = None
        away_team_name = None
        
        for team_name, api_id in team_api_mapping.items():
            if api_id == home_team_id:
                home_team_name = team_name
            elif api_id == away_team_id:
                away_team_name = team_name
        
        if not home_team_name or not away_team_name:
            continue
        
        # Calculate result
        if home_goals > away_goals:
            home_result = 1.0  # Win
            away_result = 0.0  # Loss
        elif home_goals < away_goals:
            home_result = 0.0  # Loss
            away_result = 1.0  # Win
        else:
            home_result = 0.5  # Draw
            away_result = 0.5  # Draw
        
        # Get current ELO ratings
        home_elo = team_elos[home_team_name]
        away_elo = team_elos[away_team_name]
        
        # Calculate expected scores
        home_expected = 1 / (1 + 10**((away_elo - home_elo) / 400))
        away_expected = 1 / (1 + 10**((home_elo - away_elo) / 400))
        
        # Update ELO ratings
        team_elos[home_team_name] = home_elo + K_FACTOR * (home_result - home_expected)
        team_elos[away_team_name] = away_elo + K_FACTOR * (away_result - away_expected)
        
        processed_fixtures += 1
    
    print(f"   📊 Processed {processed_fixtures} completed fixtures")
    return team_elos

def update_competition_elo_ratings(competition_name=None):
    """Update ELO ratings for specified competition or all competitions"""
    print("📈 COMPETITION-AWARE ELO ANALYSIS")
    print("="*60)
    
    conn = db_config.get_connection()
    c = conn.cursor()
    
    # Get competitions to process
    if competition_name:
        c.execute("SELECT id, name, api_league_id FROM competitions WHERE name = %s", (competition_name,))
    else:
        c.execute("SELECT id, name, api_league_id FROM competitions WHERE type = %s", ('domestic_league',))
    
    competitions = c.fetchall()
    
    for comp_id, comp_name, league_api_id in competitions:
        print(f"\n🏆 Processing {comp_name}")
        print("-" * 40)
        
        # Get teams in this competition
        competition_teams = get_competition_teams(comp_id, conn)
        
        if not competition_teams:
            print(f"   ⚠️ No teams found for {comp_name}")
            continue
        
        # Create team API mapping
        team_api_mapping = {}
        for team_id, team_name, api_team_id in competition_teams:
            if api_team_id:
                team_api_mapping[team_name] = api_team_id
        
        if not team_api_mapping:
            print(f"   ⚠️ No team API IDs found for {comp_name}")
            continue
        
        try:
            # Fetch league fixtures
            fixtures = fetch_league_fixtures(league_api_id, comp_name)
            if not fixtures:
                continue
            
            # Calculate ELO ratings
            print(f"   🧮 Calculating ELO ratings...")
            team_elos = calculate_elo_ratings(fixtures, team_api_mapping)
            
            # Show ELO range
            elo_values = list(team_elos.values())
            if elo_values:
                print(f"   📊 ELO range: {min(elo_values):.1f} - {max(elo_values):.1f}")
            
            # Convert to team_id mapping for database update
            team_scores = {}
            for team_id, team_name, api_team_id in competition_teams:
                if team_name in team_elos:
                    team_scores[team_id] = team_elos[team_name]
            
            # Update database with competition-aware normalization
            update_competition_metric(
                comp_id, "elo_score", "elo_normalized", team_scores, conn
            )
            
            print(f"   ✅ Updated {len(team_scores)} teams with ELO ratings")
            
        except Exception as e:
            print(f"   ❌ Failed for {comp_name}: {e}")
            continue
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Competition-aware ELO analysis complete!")

if __name__ == '__main__':
    # Process all domestic leagues
    update_competition_elo_ratings()