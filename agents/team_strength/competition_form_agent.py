#!/usr/bin/env python3
"""
Competition-aware form agent with per-competition normalization
Calculates recent form (last 5-10 matches) for teams within each league
"""
import sqlite3
import requests
import json
import uuid
from datetime import datetime, timezone, timedelta
import sys
import os

# Add shared utilities to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from competition_normalizer import update_competition_metric, get_competition_teams

API_KEY = "53faec37f076f995841d30d0f7b2dd9d"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}
SEASON = 2024

# Form calculation parameters
FORM_MATCHES = 5  # Last N matches to consider
WIN_POINTS = 3
DRAW_POINTS = 1
LOSS_POINTS = 0

def fetch_team_recent_fixtures(team_api_id, team_name, league_api_id):
    """Fetch recent fixtures for a specific team"""
    url = f"{BASE_URL}/fixtures"
    params = {
        "team": team_api_id,
        "league": league_api_id,
        "season": SEASON,
        "last": FORM_MATCHES * 2  # Get more to ensure we have enough completed matches
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=15)
        data = response.json()
        
        if response.status_code != 200:
            print(f"   ⚠️ API Error {response.status_code} for {team_name}")
            return []
        
        fixtures = data.get("response", [])
        
        # Filter for completed matches only and sort by date (most recent first)
        completed_fixtures = []
        for fixture in fixtures:
            status = fixture.get("fixture", {}).get("status", {}).get("short")
            if status == "FT":
                completed_fixtures.append(fixture)
        
        # Sort by date descending (most recent first)
        completed_fixtures.sort(
            key=lambda x: x.get("fixture", {}).get("date", ""), 
            reverse=True
        )
        
        return completed_fixtures[:FORM_MATCHES]  # Take only the last N matches
        
    except Exception as e:
        print(f"   ❌ Error fetching fixtures for {team_name}: {e}")
        return []

def calculate_team_form(team_api_id, team_name, league_api_id):
    """Calculate form score for a team based on recent results"""
    fixtures = fetch_team_recent_fixtures(team_api_id, team_name, league_api_id)
    
    if not fixtures:
        return 0.0, 0
    
    total_points = 0
    matches_processed = 0
    
    for fixture in fixtures:
        teams = fixture.get("teams", {})
        goals = fixture.get("goals", {})
        
        home_team_id = teams.get("home", {}).get("id")
        away_team_id = teams.get("away", {}).get("id")
        home_goals = goals.get("home")
        away_goals = goals.get("away")
        
        if not all([home_team_id, away_team_id, home_goals is not None, away_goals is not None]):
            continue
        
        # Determine if team was home or away
        is_home = (home_team_id == team_api_id)
        
        if not is_home and away_team_id != team_api_id:
            continue  # Team not in this fixture
        
        # Calculate result from team's perspective
        if is_home:
            team_goals = home_goals
            opponent_goals = away_goals
        else:
            team_goals = away_goals
            opponent_goals = home_goals
        
        # Award points based on result
        if team_goals > opponent_goals:
            total_points += WIN_POINTS
        elif team_goals == opponent_goals:
            total_points += DRAW_POINTS
        else:
            total_points += LOSS_POINTS
        
        matches_processed += 1
    
    # Calculate form as points per game
    if matches_processed > 0:
        form_score = total_points / matches_processed
    else:
        form_score = 0.0
    
    return form_score, matches_processed

def update_competition_form_scores(competition_name=None):
    """Update form scores for specified competition or all competitions"""
    print("📊 COMPETITION-AWARE FORM ANALYSIS")
    print("="*60)
    
    conn = sqlite3.connect("db/football_strength.db")
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON;")
    
    # Get competitions to process
    if competition_name:
        c.execute("SELECT id, name, api_league_id FROM competitions WHERE name = ?", (competition_name,))
    else:
        c.execute("SELECT id, name, api_league_id FROM competitions WHERE type = 'domestic_league'")
    
    competitions = c.fetchall()
    
    for comp_id, comp_name, league_api_id in competitions:
        print(f"\n🏆 Processing {comp_name}")
        print("-" * 40)
        
        # Get teams in this competition
        competition_teams = get_competition_teams(comp_id, conn)
        
        if not competition_teams:
            print(f"   ⚠️ No teams found for {comp_name}")
            continue
        
        team_scores = {}
        
        # Calculate form for each team
        for i, (team_id, team_name, api_team_id) in enumerate(competition_teams, 1):
            print(f"[{i}/{len(competition_teams)}] Processing {team_name}...")
            
            if not api_team_id:
                print(f"   ⚠️ No API ID for {team_name}")
                team_scores[team_id] = 0.0
                continue
            
            try:
                form_score, matches_count = calculate_team_form(api_team_id, team_name, league_api_id)
                team_scores[team_id] = form_score
                
                print(f"   📈 Form: {form_score:.3f} points/game ({matches_count} matches)")
                
            except Exception as e:
                print(f"   ❌ Failed for {team_name}: {e}")
                team_scores[team_id] = 0.0
        
        # Update database with competition-aware normalization
        print(f"\n💾 Updating database for {comp_name}...")
        update_competition_metric(
            comp_id, "form_score", "form_normalized", team_scores, conn
        )
        
        # Show summary
        form_values = list(team_scores.values())
        if form_values:
            print(f"   📊 Form range: {min(form_values):.3f} - {max(form_values):.3f} points/game")
            print(f"   ✅ Updated {len(team_scores)} teams")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Competition-aware form analysis complete!")

if __name__ == "__main__":
    # Process all domestic leagues  
    update_competition_form_scores()