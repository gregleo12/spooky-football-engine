#!/usr/bin/env python3
"""
Enhanced Match Data Collector
Handles team name variations and provides better mapping between API and database
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

# League mappings
LEAGUES = {
    "Premier League": {"api_id": 39, "competition_id": None},
    "La Liga": {"api_id": 140, "competition_id": None}, 
    "Serie A": {"api_id": 135, "competition_id": None},
    "Bundesliga": {"api_id": 78, "competition_id": None},
    "Ligue 1": {"api_id": 61, "competition_id": None}
}

# Team name mappings for common variations
TEAM_NAME_MAPPINGS = {
    # Premier League variations
    "Brighton & Hove Albion": ["Brighton & Hove Albion", "Brighton"],
    "Manchester United": ["Manchester United", "Man United"],
    "Manchester City": ["Manchester City", "Man City"],
    "Newcastle United": ["Newcastle United", "Newcastle"],
    "Tottenham Hotspur": ["Tottenham Hotspur", "Tottenham"],
    "West Ham United": ["West Ham United", "West Ham"],
    "Wolverhampton Wanderers": ["Wolverhampton Wanderers", "Wolves"],
    "Leicester City": ["Leicester City", "Leicester"],
    "Sheffield United": ["Sheffield United", "Sheffield Utd"],
    "Leeds United": ["Leeds United", "Leeds"],
    "Norwich City": ["Norwich City", "Norwich"],
    "Watford FC": ["Watford FC", "Watford"],
    "Luton Town": ["Luton Town", "Luton"],
    "Ipswich Town": ["Ipswich Town", "Ipswich"],
    
    # La Liga variations
    "Athletic Club": ["Athletic Club", "Athletic Bilbao"],
    "Real Betis": ["Real Betis", "Betis"],
    "Celta Vigo": ["Celta Vigo", "Celta de Vigo"],
    "Real Sociedad": ["Real Sociedad", "Sociedad"],
    "Deportivo Alavés": ["Deportivo Alavés", "Alaves"],
    "Rayo Vallecano": ["Rayo Vallecano", "Rayo"],
    "Real Valladolid": ["Real Valladolid", "Valladolid"],
    "Granada CF": ["Granada CF", "Granada"],
    "Cadiz CF": ["Cadiz CF", "Cadiz"],
    "SD Huesca": ["SD Huesca", "Huesca"],
    "Elche CF": ["Elche CF", "Elche"],
    "UD Almeria": ["UD Almeria", "Almeria"],
    
    # Serie A variations  
    "AC Milan": ["AC Milan", "Milan"],
    "Inter Milan": ["Inter Milan", "Inter"],
    "AS Roma": ["AS Roma", "Roma"],
    "SS Lazio": ["SS Lazio", "Lazio"],
    "Hellas Verona": ["Hellas Verona", "Verona"],
    "Atalanta BC": ["Atalanta BC", "Atalanta"],
    "US Sassuolo": ["US Sassuolo", "Sassuolo"],
    "UC Sampdoria": ["UC Sampdoria", "Sampdoria"],
    "FC Crotone": ["FC Crotone", "Crotone"],
    "Benevento Calcio": ["Benevento Calcio", "Benevento"],
    "Spezia Calcio": ["Spezia Calcio", "Spezia"],
    "US Salernitana": ["US Salernitana", "Salernitana"],
    "US Cremonese": ["US Cremonese", "Cremonese"],
    "Frosinone Calcio": ["Frosinone Calcio", "Frosinone"],
    
    # Bundesliga variations
    "Bayern München": ["Bayern München", "Bayern Munich", "FC Bayern Munich"],
    "Borussia Dortmund": ["Borussia Dortmund", "Dortmund"],
    "Borussia Mönchengladbach": ["Borussia Mönchengladbach", "Gladbach"],
    "Eintracht Frankfurt": ["Eintracht Frankfurt", "Frankfurt"],
    "SC Freiburg": ["SC Freiburg", "Freiburg"],
    "TSG Hoffenheim": ["TSG Hoffenheim", "Hoffenheim", "1899 Hoffenheim"],
    "1. FC Köln": ["1. FC Köln", "FC Köln", "Cologne"],
    "FSV Mainz 05": ["FSV Mainz 05", "Mainz"],
    "Union Berlin": ["Union Berlin", "FC Union Berlin"],
    "VfB Stuttgart": ["VfB Stuttgart", "Stuttgart"],
    "Bayer Leverkusen": ["Bayer Leverkusen", "Leverkusen"],
    "RB Leipzig": ["RB Leipzig", "Leipzig"],
    "VfL Wolfsburg": ["VfL Wolfsburg", "Wolfsburg"],
    "FC Augsburg": ["FC Augsburg", "Augsburg"],
    "Hertha Berlin": ["Hertha Berlin", "Hertha BSC"],
    "FC Schalke 04": ["FC Schalke 04", "Schalke"],
    "Arminia Bielefeld": ["Arminia Bielefeld", "Bielefeld"],
    "Hamburger SV": ["Hamburger SV", "Hamburg"],
    "SpVgg Greuther Fürth": ["SpVgg Greuther Fürth", "Greuther Fürth"],
    "Fortuna Düsseldorf": ["Fortuna Düsseldorf", "Düsseldorf"],
    "SV Darmstadt 98": ["SV Darmstadt 98", "Darmstadt"],
    "Holstein Kiel": ["Holstein Kiel", "Kiel"],
    "FC St. Pauli": ["FC St. Pauli", "St. Pauli"],
    "1. FC Heidenheim": ["1. FC Heidenheim", "Heidenheim"],
    "VfL Bochum": ["VfL Bochum", "Bochum"],
    
    # Ligue 1 variations
    "Paris Saint Germain": ["Paris Saint Germain", "Paris SG", "PSG"],
    "Olympique Marseille": ["Olympique Marseille", "Marseille"],
    "Olympique Lyon": ["Olympique Lyon", "Lyon"],
    "AS Saint-Étienne": ["AS Saint-Étienne", "Saint Etienne"],
    "Stade Rennais": ["Stade Rennais", "Rennes"],
    "Montpellier HSC": ["Montpellier HSC", "Montpellier"],
    "FC Girondins Bordeaux": ["FC Girondins Bordeaux", "Bordeaux"],
    "Dijon FCO": ["Dijon FCO", "Dijon"],
    "FC Nîmes": ["FC Nîmes", "Nimes"],
    "FC Lorient": ["FC Lorient", "Lorient"],
    "Clermont Foot": ["Clermont Foot", "Clermont"],
    "ESTAC Troyes": ["ESTAC Troyes", "Troyes"],
    "AC Ajaccio": ["AC Ajaccio", "Ajaccio"],
    "Stade Brestois 29": ["Stade Brestois 29", "Brest"],
    "Le Havre AC": ["Le Havre AC", "Le Havre"]
}

def create_reverse_mapping(team_mappings):
    """Create reverse mapping from API names to database names"""
    reverse_map = {}
    for db_name, api_variants in team_mappings.items():
        for api_name in api_variants:
            reverse_map[api_name] = db_name
    return reverse_map

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

def get_enhanced_team_mapping():
    """Get enhanced team name to team_id mapping"""
    conn = get_database_connection()
    c = conn.cursor()
    
    c.execute("SELECT id, name FROM teams")
    team_mapping = {}
    reverse_name_mapping = create_reverse_mapping(TEAM_NAME_MAPPINGS)
    
    for team_id, team_name in c.fetchall():
        # Add direct mapping
        team_mapping[team_name] = team_id
        
        # Add reverse mappings for variations
        if team_name in TEAM_NAME_MAPPINGS:
            for variant in TEAM_NAME_MAPPINGS[team_name]:
                team_mapping[variant] = team_id
    
    conn.close()
    print(f"   📊 Enhanced mapping covers {len(team_mapping)} name variations")
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

def store_matches_enhanced(fixtures, league_name, competition_id, season, team_mapping):
    """Store matches with enhanced team name matching"""
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
            
            # Track unmapped teams for debugging
            if not home_team_id:
                unmapped_teams.add(home_team_name)
            if not away_team_id:
                unmapped_teams.add(away_team_name)
            
            # Skip if teams not found in our mapping
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
    if unmapped_teams:
        print(f"      ⚠️ Unmapped teams: {', '.join(sorted(unmapped_teams))}")
    
    return stored_count

def collect_all_matches_enhanced():
    """Enhanced match collection with better team name mapping"""
    print("🏟️ ENHANCED MATCH DATA COLLECTION")
    print("=" * 70)
    print("📅 Collecting 5 seasons (2020-2024) from 5 major leagues")
    print("🎯 Enhanced team name matching for complete coverage")
    print("")
    
    # Get competition IDs from database
    print("🔍 Getting competition mappings...")
    get_competition_ids()
    
    # Get enhanced team mappings
    print("👥 Loading enhanced team mappings...")
    team_mapping = get_enhanced_team_mapping()
    
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
                # Store matches with enhanced mapping
                match_count = store_matches_enhanced(
                    fixtures, league_name, competition_id, season, team_mapping
                )
                league_total += match_count
        
        print(f"   ✅ {league_name}: {league_total} matches stored")
        total_matches += league_total
    
    print(f"\n🎉 ENHANCED COLLECTION COMPLETE!")
    print(f"📊 Total matches stored: {total_matches}")
    
    # Show final database statistics
    conn = get_database_connection()
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM matches")
    total_count = c.fetchone()[0]
    
    c.execute("SELECT competition_name, COUNT(*) FROM matches GROUP BY competition_name ORDER BY COUNT(*) DESC")
    by_league = c.fetchall()
    
    print(f"\n📈 FINAL DATABASE STATISTICS:")
    print(f"   Total matches in database: {total_count}")
    for league, count in by_league:
        print(f"   {league}: {count} matches")
    
    # Check coverage by season
    c.execute("""
        SELECT competition_name, season, COUNT(*) as matches,
               COUNT(DISTINCT home_team_name) + COUNT(DISTINCT away_team_name) as unique_teams
        FROM matches 
        GROUP BY competition_name, season 
        ORDER BY competition_name, season
    """)
    
    print(f"\n📊 COVERAGE BY SEASON:")
    current_league = ""
    for league, season, matches, teams in c.fetchall():
        if league != current_league:
            print(f"\n   {league}:")
            current_league = league
        expected_matches = {
            "Premier League": 380,
            "La Liga": 380, 
            "Serie A": 380,
            "Bundesliga": 306,
            "Ligue 1": 380
        }.get(league, 380)
        coverage = (matches / expected_matches) * 100
        print(f"     {season}: {matches} matches ({coverage:.1f}% coverage)")
    
    conn.close()

if __name__ == "__main__":
    collect_all_matches_enhanced()