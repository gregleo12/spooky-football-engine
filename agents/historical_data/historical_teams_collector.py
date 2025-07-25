#!/usr/bin/env python3
"""
Historical Teams Collector
Adds all teams that participated in the top 5 leagues over the past 5 seasons
This ensures complete match data collection for comprehensive H2H analysis
"""
import sqlite3
import requests
import json
import os
import sys
import uuid
from datetime import datetime
import time

# API Configuration
API_KEY = "53faec37f076f995841d30d0f7b2dd9d"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

# Seasons to collect teams from
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

def get_existing_teams():
    """Get existing team names from database"""
    conn = get_database_connection()
    c = conn.cursor()
    
    c.execute("SELECT name FROM teams")
    existing_teams = set(row[0] for row in c.fetchall())
    
    conn.close()
    return existing_teams

def fetch_league_teams(league_name, api_league_id, season):
    """Fetch all teams that participated in a league during a season"""
    print(f"      🔍 Fetching {league_name} {season} teams...")
    
    url = f"{BASE_URL}/teams"
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
        
        teams = data.get("response", [])
        print(f"      ✅ Found {len(teams)} teams")
        
        # Add small delay to respect API limits
        time.sleep(0.5)
        
        return teams
        
    except Exception as e:
        print(f"      ❌ Error fetching {league_name} {season} teams: {e}")
        return []

def add_teams_to_database(teams_data, league_name, competition_id, season, existing_teams):
    """Add new teams to database"""
    conn = get_database_connection()
    c = conn.cursor()
    
    added_count = 0
    skipped_count = 0
    
    for team_data in teams_data:
        try:
            team_info = team_data.get("team", {})
            venue_info = team_data.get("venue", {})
            
            team_name = team_info.get("name")
            team_id = str(uuid.uuid4())
            
            # Skip if team already exists
            if team_name in existing_teams:
                skipped_count += 1
                continue
            
            # Extract team details
            country = team_info.get("country")
            founded = team_info.get("founded")
            venue_name = venue_info.get("name")
            venue_city = venue_info.get("city")
            venue_capacity = venue_info.get("capacity")
            logo_url = team_info.get("logo")
            team_code = team_info.get("code")
            
            # Insert team
            c.execute("""
                INSERT INTO teams (
                    id, name, country, founded, venue_name, venue_city, 
                    venue_capacity, logo_url, team_code
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                team_id, team_name, country, founded, venue_name, 
                venue_city, venue_capacity, logo_url, team_code
            ))
            
            # Also add to competition_team_strength table for this season
            c.execute("""
                INSERT OR IGNORE INTO competition_team_strength (
                    id, competition_id, team_id, team_name, season, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()), competition_id, team_id, team_name, 
                f"{season}-{str(int(season)+1)[2:]}", datetime.now()
            ))
            
            existing_teams.add(team_name)  # Add to set to avoid duplicates
            added_count += 1
            
            print(f"         ➕ Added: {team_name} ({country})")
                
        except Exception as e:
            print(f"      ⚠️ Error adding team {team_name}: {e}")
            continue
    
    conn.commit()
    conn.close()
    
    print(f"      💾 Added {added_count} new teams, skipped {skipped_count} existing")
    return added_count

def collect_all_historical_teams():
    """Collect all teams from past 5 seasons across all leagues"""
    print("👥 HISTORICAL TEAMS COLLECTION")
    print("=" * 70)
    print("📅 Collecting teams from 5 seasons (2020-2024) across 5 major leagues")
    print("🎯 Goal: Complete team database for comprehensive H2H analysis")
    print("")
    
    # Get competition IDs from database
    print("🔍 Getting competition mappings...")
    get_competition_ids()
    
    # Get existing teams
    print("📊 Loading existing teams...")
    existing_teams = get_existing_teams()
    print(f"   Found {len(existing_teams)} existing teams in database")
    
    total_teams_added = 0
    all_unique_teams = set()
    
    # Process each league and season
    for league_name, league_info in LEAGUES.items():
        api_league_id = league_info["api_id"]
        competition_id = league_info["competition_id"]
        
        if not competition_id:
            print(f"⚠️ Skipping {league_name} - no competition ID found")
            continue
        
        print(f"\n🏆 {league_name.upper()}")
        print("-" * 40)
        
        league_teams_added = 0
        league_unique_teams = set()
        
        for season in SEASONS:
            # Fetch teams from API
            teams_data = fetch_league_teams(league_name, api_league_id, season)
            
            if teams_data:
                # Count unique teams for this season
                season_teams = set(team["team"]["name"] for team in teams_data)
                league_unique_teams.update(season_teams)
                
                # Add new teams to database
                teams_added = add_teams_to_database(
                    teams_data, league_name, competition_id, season, existing_teams
                )
                league_teams_added += teams_added
        
        print(f"   ✅ {league_name}: {league_teams_added} new teams added")
        print(f"   📊 Total unique teams seen: {len(league_unique_teams)}")
        total_teams_added += league_teams_added
        all_unique_teams.update(league_unique_teams)
    
    print(f"\n🎉 COLLECTION COMPLETE!")
    print(f"👥 Total new teams added: {total_teams_added}")
    print(f"🌍 Total unique teams across all leagues/seasons: {len(all_unique_teams)}")
    
    # Show final database statistics
    conn = get_database_connection()
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM teams")
    total_teams = c.fetchone()[0]
    
    c.execute("""
        SELECT c.name, COUNT(DISTINCT cts.team_name) 
        FROM competition_team_strength cts
        JOIN competitions c ON cts.competition_id = c.id
        GROUP BY c.name
    """)
    teams_by_league = c.fetchall()
    
    print(f"\n📈 FINAL DATABASE STATISTICS:")
    print(f"   Total teams in database: {total_teams}")
    for league, count in teams_by_league:
        print(f"   {league}: {count} teams")
    
    conn.close()
    
    print(f"\n✅ Ready for complete match data collection!")

if __name__ == "__main__":
    collect_all_historical_teams()