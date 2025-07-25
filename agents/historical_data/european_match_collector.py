#!/usr/bin/env python3
"""
European Match Data Collector
Collects and stores historical match data from European competitions (Champions League, Europa League)
"""
import sqlite3
import requests
import json
import os
import sys
from datetime import datetime
import time

# API Configuration
API_KEY = "53faec37f076f995841d30d0f7b2dd9d"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

# Seasons to collect (last 5 seasons)
SEASONS = ["2020", "2021", "2022", "2023", "2024"]

# European competition mappings
EUROPEAN_COMPETITIONS = {
    "Champions League": {"api_id": 2, "competition_id": None},
    "Europa League": {"api_id": 3, "competition_id": None}
}

def get_database_connection():
    """Get database connection"""
    return sqlite3.connect("db/football_strength.db")

def get_competition_ids():
    """Get competition IDs from database"""
    conn = get_database_connection()
    c = conn.cursor()
    
    for comp_name in EUROPEAN_COMPETITIONS.keys():
        c.execute("SELECT id FROM competitions WHERE name = ?", (comp_name,))
        result = c.fetchone()
        if result:
            EUROPEAN_COMPETITIONS[comp_name]["competition_id"] = result[0]
            print(f"   📍 {comp_name}: {result[0]}")
        else:
            print(f"   ⚠️ {comp_name}: Not found in database")
    
    conn.close()

def create_enhanced_team_mapping():
    """Create enhanced team name mapping for European competitions"""
    conn = get_database_connection()
    c = conn.cursor()
    
    c.execute("SELECT id, name FROM teams")
    team_mapping = {}
    
    # Common European team name variations
    EUROPEAN_NAME_MAPPINGS = {
        # Premier League teams in Europe
        "Brighton & Hove Albion": ["Brighton & Hove Albion", "Brighton"],
        "Manchester United": ["Manchester United", "Man United", "Manchester Utd"],
        "Manchester City": ["Manchester City", "Man City", "Manchester City FC"],
        "Newcastle United": ["Newcastle United", "Newcastle"],
        "Tottenham Hotspur": ["Tottenham Hotspur", "Tottenham"],
        "West Ham United": ["West Ham United", "West Ham"],
        "Wolverhampton Wanderers": ["Wolverhampton Wanderers", "Wolves"],
        
        # La Liga teams in Europe
        "Athletic Club": ["Athletic Club", "Athletic Bilbao", "Ath Bilbao"],
        "Real Betis": ["Real Betis", "Betis"],
        "Atletico Madrid": ["Atletico Madrid", "Atlético Madrid", "Atletico"],
        "Real Sociedad": ["Real Sociedad", "Sociedad"],
        "Deportivo Alavés": ["Deportivo Alavés", "Alaves"],
        
        # Serie A teams in Europe
        "AC Milan": ["AC Milan", "Milan", "AC Milan"],
        "Inter Milan": ["Inter Milan", "Inter", "Internazionale"],
        "AS Roma": ["AS Roma", "Roma"],
        "SS Lazio": ["SS Lazio", "Lazio"],
        "Atalanta BC": ["Atalanta BC", "Atalanta"],
        
        # Bundesliga teams in Europe
        "Bayern München": ["Bayern München", "Bayern Munich", "FC Bayern Munich", "Bayern"],
        "Borussia Dortmund": ["Borussia Dortmund", "Dortmund", "BVB"],
        "Borussia Mönchengladbach": ["Borussia Mönchengladbach", "Gladbach", "B. Monchengladbach"],
        "Eintracht Frankfurt": ["Eintracht Frankfurt", "Frankfurt"],
        "Bayer Leverkusen": ["Bayer Leverkusen", "Leverkusen"],
        "RB Leipzig": ["RB Leipzig", "Leipzig"],
        "VfL Wolfsburg": ["VfL Wolfsburg", "Wolfsburg"],
        
        # Ligue 1 teams in Europe
        "Paris Saint Germain": ["Paris Saint Germain", "Paris SG", "PSG"],
        "Olympique Marseille": ["Olympique Marseille", "Marseille", "OM"],
        "Olympique Lyon": ["Olympique Lyon", "Lyon", "OL"],
        "Stade Rennais": ["Stade Rennais", "Rennes"],
        "Montpellier HSC": ["Montpellier HSC", "Montpellier"],
        
        # Other European teams (opponents)
        "Ajax": ["Ajax", "AFC Ajax"],
        "PSV Eindhoven": ["PSV Eindhoven", "PSV"],
        "FC Porto": ["FC Porto", "Porto"],
        "Benfica": ["Benfica", "SL Benfica"],
        "Sporting CP": ["Sporting CP", "Sporting"],
        "Celtic": ["Celtic", "Celtic FC"],
        "Rangers": ["Rangers", "Rangers FC"],
        "Dynamo Kiev": ["Dynamo Kiev", "Dynamo Kyiv"],
        "Shakhtar Donetsk": ["Shakhtar Donetsk", "Shakhtar"],
        "Red Bull Salzburg": ["Red Bull Salzburg", "Salzburg"],
        "FC Basel": ["FC Basel", "Basel"],
        "Young Boys": ["Young Boys", "BSC Young Boys"],
        "Club Brugge": ["Club Brugge", "Club Bruges"],
        "Galatasaray": ["Galatasaray", "Galatasaray SK"],
        "Fenerbahce": ["Fenerbahce", "Fenerbahçe"]
    }
    
    for team_id, team_name in c.fetchall():
        # Add direct mapping
        team_mapping[team_name] = team_id
        
        # Add variations for European names
        if team_name in EUROPEAN_NAME_MAPPINGS:
            for variant in EUROPEAN_NAME_MAPPINGS[team_name]:
                team_mapping[variant] = team_id
    
    conn.close()
    print(f"   📊 Enhanced European mapping covers {len(team_mapping)} name variations")
    return team_mapping

def fetch_european_matches(competition_name, api_competition_id, season):
    """Fetch all matches for a European competition in a season"""
    print(f"      🔍 Fetching {competition_name} {season} season...")
    
    url = f"{BASE_URL}/fixtures"
    params = {
        "league": api_competition_id,
        "season": season
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        data = response.json()
        
        if response.status_code != 200:
            print(f"      ❌ API Error {response.status_code} for {competition_name} {season}")
            return []
        
        fixtures = data.get("response", [])
        print(f"      ✅ Found {len(fixtures)} fixtures")
        
        # Add delay to respect API limits
        time.sleep(0.5)
        
        return fixtures
        
    except Exception as e:
        print(f"      ❌ Error fetching {competition_name} {season}: {e}")
        return []

def store_european_matches(fixtures, competition_name, competition_id, season, team_mapping):
    """Store European matches with enhanced team matching"""
    conn = get_database_connection()
    c = conn.cursor()
    
    stored_count = 0
    skipped_count = 0
    unmapped_teams = set()
    
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
            match_date = fixture_data.get("date", "").split("T")[0]
            
            home_team_name = teams_data.get("home", {}).get("name")
            away_team_name = teams_data.get("away", {}).get("name")
            home_score = goals_data.get("home")
            away_score = goals_data.get("away")
            
            # Skip if essential data is missing
            if not all([api_fixture_id, home_team_name, away_team_name, 
                       home_score is not None, away_score is not None]):
                continue
            
            # Get team IDs using enhanced mapping
            home_team_id = team_mapping.get(home_team_name)
            away_team_id = team_mapping.get(away_team_name)
            
            # Track unmapped teams (likely non-database teams)
            if not home_team_id:
                unmapped_teams.add(home_team_name)
            if not away_team_id:
                unmapped_teams.add(away_team_name)
            
            # Skip if either team not in our database (expected for European competitions)
            if not home_team_id or not away_team_id:
                skipped_count += 1
                continue
            
            # Generate match ID
            match_id = f"{competition_id}_{season}_{api_fixture_id}"
            
            # Get database team names
            home_db_name = next((name for name, tid in team_mapping.items() if tid == home_team_id), home_team_name)
            away_db_name = next((name for name, tid in team_mapping.items() if tid == away_team_id), away_team_name)
            
            # Insert match
            c.execute("""
                INSERT OR IGNORE INTO matches (
                    id, home_team_id, away_team_id, home_team_name, away_team_name,
                    home_score, away_score, competition_id, competition_name,
                    match_date, season, status, api_fixture_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                match_id, home_team_id, away_team_id, home_db_name, away_db_name,
                home_score, away_score, competition_id, competition_name,
                match_date, f"{season}-{str(int(season)+1)[2:]}", "FT", api_fixture_id
            ))
            
            if c.rowcount > 0:
                stored_count += 1
                
        except Exception as e:
            print(f"      ⚠️ Error storing match: {e}")
            continue
    
    conn.commit()
    conn.close()
    
    print(f"      💾 Stored {stored_count} matches involving database teams")
    print(f"      ⏭️ Skipped {skipped_count} matches (teams not in database)")
    if len(unmapped_teams) > 20:  # Show sample of unmapped teams
        sample_teams = sorted(list(unmapped_teams))[:10]
        print(f"      📋 Sample unmapped teams: {', '.join(sample_teams)}... (+{len(unmapped_teams)-10} more)")
    elif unmapped_teams:
        print(f"      📋 Unmapped teams: {', '.join(sorted(unmapped_teams))}")
    
    return stored_count

def collect_european_matches():
    """Collect European competition matches"""
    print("🏆 EUROPEAN COMPETITION MATCH COLLECTION")
    print("=" * 70)
    print("📅 Collecting 5 seasons (2020-2024) from Champions League & Europa League")
    print("🎯 Focus: Matches involving teams from our 5 domestic leagues")
    print("")
    
    # Get competition IDs from database
    print("🔍 Getting European competition mappings...")
    get_competition_ids()
    
    # Get enhanced team mappings for European competitions
    print("👥 Loading enhanced European team mappings...")
    team_mapping = create_enhanced_team_mapping()
    
    total_matches = 0
    
    # Process each European competition and season
    for comp_name, comp_info in EUROPEAN_COMPETITIONS.items():
        api_comp_id = comp_info["api_id"]
        competition_id = comp_info["competition_id"]
        
        if not competition_id:
            print(f"⚠️ Skipping {comp_name} - no competition ID found")
            continue
        
        print(f"\n🏆 {comp_name.upper()}")
        print("-" * 40)
        
        comp_total = 0
        
        for season in SEASONS:
            # Fetch matches from API
            fixtures = fetch_european_matches(comp_name, api_comp_id, season)
            
            if fixtures:
                # Store matches with European mapping
                match_count = store_european_matches(
                    fixtures, comp_name, competition_id, season, team_mapping
                )
                comp_total += match_count
        
        print(f"   ✅ {comp_name}: {comp_total} matches stored")
        total_matches += comp_total
    
    print(f"\n🎉 EUROPEAN COLLECTION COMPLETE!")
    print(f"📊 Total European matches stored: {total_matches}")
    
    # Show final database statistics
    conn = get_database_connection()
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM matches WHERE competition_name IN ('Champions League', 'Europa League')")
    european_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM matches")
    total_count = c.fetchone()[0]
    
    c.execute("""
        SELECT competition_name, COUNT(*) 
        FROM matches 
        WHERE competition_name IN ('Champions League', 'Europa League')
        GROUP BY competition_name ORDER BY COUNT(*) DESC
    """)
    by_competition = c.fetchall()
    
    print(f"\n📈 EUROPEAN DATABASE STATISTICS:")
    print(f"   European matches in database: {european_count}")
    print(f"   Total matches in database: {total_count}")
    for comp, count in by_competition:
        print(f"   {comp}: {count} matches")
    
    conn.close()

if __name__ == "__main__":
    collect_european_matches()