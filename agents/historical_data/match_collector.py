#!/usr/bin/env python3
"""
Match Data Collector
Collects and stores historical match data from domestic leagues over the last 5 seasons
"""
import sqlite3
import requests
import json
import os
import sys
from datetime import datetime
import time

# Add shared utilities to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

# API Configuration
API_KEY = "53faec37f076f995841d30d0f7b2dd9d"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

# Seasons to collect (last 5 seasons)
SEASONS = ["2020", "2021", "2022", "2023", "2024"]

# League mappings
LEAGUES = {
    "Premier League": {"api_id": 39, "competition_id": None},
    "La Liga": {"api_id": 140, "competition_id": None}, 
    "Serie A": {"api_id": 135, "competition_id": None},
    "Bundesliga": {"api_id": 78, "competition_id": None},
    "Ligue 1": {"api_id": 61, "competition_id": None}
}

def get_database_connection():
    """Get database connection"""
    return sqlite3.connect("db/football_strength.db")

def get_competition_ids():
    """Get competition IDs from database"""
    conn = get_database_connection()
    c = conn.cursor()
    
    for league_name in LEAGUES.keys():
        c.execute("SELECT id FROM competitions WHERE name = ?", (league_name,))
        result = c.fetchone()
        if result:
            LEAGUES[league_name]["competition_id"] = result[0]
            print(f"   📍 {league_name}: {result[0]}")
        else:
            print(f"   ⚠️ {league_name}: Not found in database")
    
    conn.close()

def get_team_mapping():
    """Get team name to team_id mapping from database"""
    conn = get_database_connection()
    c = conn.cursor()
    
    c.execute("SELECT id, name FROM teams")
    team_mapping = {}
    for team_id, team_name in c.fetchall():
        team_mapping[team_name] = team_id
    
    conn.close()
    return team_mapping

def fetch_league_matches(league_name, api_league_id, season):
    """Fetch all matches for a league in a season"""
    print(f"      🔍 Fetching {league_name} {season} season...")
    
    url = f"{BASE_URL}/fixtures"
    params = {
        "league": api_league_id,
        "season": season
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        data = response.json()
        
        if response.status_code != 200:
            print(f"      ❌ API Error {response.status_code} for {league_name} {season}")
            return []
        
        fixtures = data.get("response", [])
        print(f"      ✅ Found {len(fixtures)} fixtures")
        
        # Add small delay to respect API limits
        time.sleep(0.5)
        
        return fixtures
        
    except Exception as e:
        print(f"      ❌ Error fetching {league_name} {season}: {e}")
        return []

def store_matches(fixtures, league_name, competition_id, season, team_mapping):
    """Store matches in database"""
    conn = get_database_connection()
    c = conn.cursor()
    
    stored_count = 0
    skipped_count = 0
    
    for fixture in fixtures:
        try:
            # Only store finished matches
            if fixture.get("fixture", {}).get("status", {}).get("short") != "FT":
                continue
            
            # Extract match data
            fixture_data = fixture.get("fixture", {})
            teams_data = fixture.get("teams", {})
            goals_data = fixture.get("goals", {})
            
            api_fixture_id = fixture_data.get("id")
            match_date = fixture_data.get("date", "").split("T")[0]  # Extract date part
            
            home_team_name = teams_data.get("home", {}).get("name")
            away_team_name = teams_data.get("away", {}).get("name")
            home_score = goals_data.get("home")
            away_score = goals_data.get("away")
            
            # Skip if essential data is missing
            if not all([api_fixture_id, home_team_name, away_team_name, 
                       home_score is not None, away_score is not None]):
                continue
            
            # Get team IDs from mapping
            home_team_id = team_mapping.get(home_team_name)
            away_team_id = team_mapping.get(away_team_name)
            
            # Skip if teams not found in our database
            if not home_team_id or not away_team_id:
                skipped_count += 1
                continue
            
            # Generate match ID
            match_id = f"{competition_id}_{season}_{api_fixture_id}"
            
            # Insert match
            c.execute("""
                INSERT OR IGNORE INTO matches (
                    id, home_team_id, away_team_id, home_team_name, away_team_name,
                    home_score, away_score, competition_id, competition_name,
                    match_date, season, status, api_fixture_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                match_id, home_team_id, away_team_id, home_team_name, away_team_name,
                home_score, away_score, competition_id, league_name,
                match_date, f"{season}-{str(int(season)+1)[2:]}", "FT", api_fixture_id
            ))
            
            if c.rowcount > 0:
                stored_count += 1
                
        except Exception as e:
            print(f"      ⚠️ Error storing match: {e}")
            continue
    
    conn.commit()
    conn.close()
    
    print(f"      💾 Stored {stored_count} matches, skipped {skipped_count}")
    return stored_count

def collect_all_matches():
    """Collect matches for all leagues and seasons"""
    print("🏟️ MATCH DATA COLLECTION - DOMESTIC LEAGUES")
    print("=" * 70)
    print("📅 Collecting 5 seasons (2020-2024) from 5 major leagues")
    print("🎯 Target: ~19,000 matches")
    print("")
    
    # Get competition IDs from database
    print("🔍 Getting competition mappings...")
    get_competition_ids()
    
    # Get team mappings
    print("👥 Loading team mappings...")
    team_mapping = get_team_mapping()
    print(f"   📊 Found {len(team_mapping)} teams in database")
    
    total_matches = 0
    
    # Process each league and season
    for league_name, league_info in LEAGUES.items():
        api_league_id = league_info["api_id"]
        competition_id = league_info["competition_id"]
        
        if not competition_id:
            print(f"⚠️ Skipping {league_name} - no competition ID found")
            continue
        
        print(f"\n🏆 {league_name.upper()}")
        print("-" * 40)
        
        league_total = 0
        
        for season in SEASONS:
            # Fetch matches from API
            fixtures = fetch_league_matches(league_name, api_league_id, season)
            
            if fixtures:
                # Store matches in database
                match_count = store_matches(fixtures, league_name, competition_id, season, team_mapping)
                league_total += match_count
        
        print(f"   ✅ {league_name}: {league_total} matches stored")
        total_matches += league_total
    
    print(f"\n🎉 COLLECTION COMPLETE!")
    print(f"📊 Total matches stored: {total_matches}")
    print(f"💽 Database size increased by ~{total_matches * 200 / 1024 / 1024:.1f}MB")
    
    # Show database statistics
    conn = get_database_connection()
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM matches")
    total_count = c.fetchone()[0]
    
    c.execute("SELECT competition_name, COUNT(*) FROM matches GROUP BY competition_name")
    by_league = c.fetchall()
    
    print(f"\n📈 DATABASE STATISTICS:")
    print(f"   Total matches: {total_count}")
    for league, count in by_league:
        print(f"   {league}: {count} matches")
    
    conn.close()

if __name__ == "__main__":
    collect_all_matches()