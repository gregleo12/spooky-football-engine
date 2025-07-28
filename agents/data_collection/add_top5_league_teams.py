#!/usr/bin/env python3
"""
Add teams from Top 5 European leagues to database
Fetches team data from API-Football and populates teams and competition_teams tables
"""
import requests
import json
import uuid
import sys
import os
from datetime import datetime, timezone

# Add project root to path for database config
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from database_config import db_config

API_KEY = "53faec37f076f995841d30d0f7b2dd9d"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}
SEASON = 2024

# Competition mappings
LEAGUE_CONFIGS = {
    "La Liga": {"api_id": 140, "country": "Spain"},
    "Serie A": {"api_id": 135, "country": "Italy"}, 
    "Bundesliga": {"api_id": 78, "country": "Germany"},
    "Ligue 1": {"api_id": 61, "country": "France"}
    # Premier League already exists
}

def fetch_league_teams(league_api_id, league_name):
    """Fetch all teams from a specific league"""
    print(f"   🔍 Fetching teams from {league_name} (API ID: {league_api_id})...")
    
    url = f"{BASE_URL}/teams"
    params = {
        "league": league_api_id,
        "season": SEASON
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=15)
        data = response.json()
        
        if response.status_code != 200:
            print(f"   ❌ API Error {response.status_code} for {league_name}")
            return []
        
        teams = data.get("response", [])
        print(f"   ✅ Found {len(teams)} teams in {league_name}")
        
        return teams
        
    except Exception as e:
        print(f"   ❌ Error fetching {league_name} teams: {e}")
        return []

def add_teams_to_database(conn):
    """Add teams from all Top 5 leagues to database"""
    print("🏟️ ADDING TOP 5 LEAGUE TEAMS")
    print("="*60)
    
    c = conn.cursor()
    # PostgreSQL doesn't need PRAGMA statements
    
    all_team_api_ids = {}
    
    # Load existing team API IDs
    try:
        with open("agents/shared/team_api_ids.json") as f:
            all_team_api_ids = json.load(f)
        print(f"📋 Loaded {len(all_team_api_ids)} existing team API IDs")
    except FileNotFoundError:
        print("📋 Creating new team API IDs file")
    
    for league_name, config in LEAGUE_CONFIGS.items():
        print(f"\n🏆 Processing {league_name}")
        print("-" * 40)
        
        # Get competition ID
        c.execute("SELECT id FROM competitions WHERE name = %s", (league_name,))
        comp_result = c.fetchone()
        if not comp_result:
            print(f"   ⚠️ Competition {league_name} not found in database")
            continue
        
        competition_id = comp_result[0]
        
        # Fetch teams from API
        teams_data = fetch_league_teams(config["api_id"], league_name)
        if not teams_data:
            continue
        
        teams_added = 0
        teams_mapped = 0
        
        for team_data in teams_data:
            team_info = team_data.get("team", {})
            venue_info = team_data.get("venue", {})
            
            team_name = team_info.get("name", "").strip()
            api_team_id = team_info.get("id")
            team_logo = team_info.get("logo", "")
            team_code = team_info.get("code", "")
            country = team_info.get("country", config["country"])
            founded = team_info.get("founded")
            
            venue_name = venue_info.get("name", "")
            venue_city = venue_info.get("city", "")
            venue_capacity = venue_info.get("capacity")
            
            if not team_name or not api_team_id:
                print(f"   ⚠️ Skipping invalid team data")
                continue
            
            try:
                # Check if team already exists
                c.execute("SELECT id FROM teams WHERE name = %s", (team_name,))
                existing_team = c.fetchone()
                
                if existing_team:
                    team_id = existing_team[0]
                    print(f"   🔄 Team exists: {team_name}")
                else:
                    # Add new team
                    team_id = str(uuid.uuid4())
                    c.execute("""
                        INSERT INTO teams 
                        (id, name, country, api_team_id, created_at)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (team_id, team_name, country, api_team_id, datetime.now(timezone.utc)))
                    
                    teams_added += 1
                    print(f"   ➕ Added: {team_name}")
                
                # Add to competition_team_strength mapping (check if exists first)
                c.execute("""
                    SELECT id FROM competition_team_strength 
                    WHERE competition_id = %s AND team_id = %s AND season = %s
                """, (competition_id, team_id, str(SEASON)))
                
                if not c.fetchone():
                    c.execute("""
                        INSERT INTO competition_team_strength 
                        (id, competition_id, team_id, team_name, season)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (str(uuid.uuid4()), competition_id, team_id, team_name, str(SEASON)))
                
                # Update API IDs mapping
                all_team_api_ids[team_name] = api_team_id
                teams_mapped += 1
                
            except Exception as e:
                print(f"   ❌ Error processing {team_name}: {e}")
                continue
        
        print(f"   📊 Summary: {teams_added} new teams, {teams_mapped} mapped to competition")
    
    # Save updated team API IDs
    with open("agents/shared/team_api_ids.json", "w") as f:
        json.dump(all_team_api_ids, f, indent=2, sort_keys=True)
    
    print(f"\n💾 Updated team_api_ids.json with {len(all_team_api_ids)} teams")
    
    # Show final statistics
    c.execute("SELECT COUNT(*) FROM teams")
    total_teams = c.fetchone()[0]
    
    c.execute("""
        SELECT c.name, COUNT(ct.team_id) as team_count
        FROM competitions c
        LEFT JOIN competition_teams ct ON c.id = ct.competition_id
        WHERE c.type = 'domestic_league'
        GROUP BY c.name
        ORDER BY c.name
    """)
    
    league_stats = c.fetchall()
    
    print(f"\n📊 FINAL STATISTICS")
    print("="*40)
    print(f"   Total teams in database: {total_teams}")
    print(f"   Teams per league:")
    
    for league, count in league_stats:
        print(f"      {league:<20}: {count} teams")
    
    conn.commit()

def main():
    conn = db_config.get_connection()
    
    try:
        add_teams_to_database(conn)
        print(f"\n✅ Successfully added Top 5 league teams!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        conn.rollback()
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()