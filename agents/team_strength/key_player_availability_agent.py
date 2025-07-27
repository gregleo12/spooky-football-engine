#!/usr/bin/env python3
"""
Key Player Availability Agent - Phase 1 Parameter Implementation
Calculates key player availability impact based on injuries and suspensions
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
FALLBACK_SCORE = 0.8  # Assume most players available by default

# Load team API ID mapping
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEAM_API_IDS_PATH = os.path.join(SCRIPT_DIR, "..", "shared", "team_api_ids.json")

try:
    with open(TEAM_API_IDS_PATH, 'r', encoding='utf-8') as f:
        TEAM_API_IDS = json.load(f)
except FileNotFoundError:
    print(f"⚠️ Warning: team_api_ids.json not found at {TEAM_API_IDS_PATH}")
    TEAM_API_IDS = {}

def fetch_team_injuries(team_api_id, team_name):
    """Fetch current team injuries and suspensions"""
    url = f"{BASE_URL}/injuries"
    params = {
        "team": team_api_id,
        "season": SEASON
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=15)
        data = response.json()
        
        if response.status_code != 200:
            print(f"   ⚠️ API Error {response.status_code} for {team_name}")
            return None
        
        return data.get("response", [])
        
    except Exception as e:
        print(f"   ❌ Error fetching injuries for {team_name}: {e}")
        return None

def fetch_team_players(team_api_id, team_name):
    """Fetch team player statistics to identify key players"""
    url = f"{BASE_URL}/players"
    params = {
        "team": team_api_id,
        "season": SEASON
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=15)
        data = response.json()
        
        if response.status_code != 200:
            print(f"   ⚠️ API Error {response.status_code} for players of {team_name}")
            return None
        
        return data.get("response", [])
        
    except Exception as e:
        print(f"   ❌ Error fetching players for {team_name}: {e}")
        return None

def identify_key_players(players_data, team_name):
    """
    Identify key players based on playing time and performance
    
    Key player criteria:
    - High minutes played
    - Goals/assists contribution
    - Regular starter status
    """
    
    if not players_data:
        return []
    
    key_players = []
    
    for player_info in players_data:
        player = player_info.get("player", {})
        statistics = player_info.get("statistics", [])
        
        if not statistics:
            continue
        
        # Get main league statistics (first entry usually)
        main_stats = statistics[0]
        games = main_stats.get("games", {})
        goals = main_stats.get("goals", {})
        passes = main_stats.get("passes", {})
        
        minutes = games.get("minutes", 0) or 0
        appearances = games.get("appearences", 0) or 0
        goals_scored = goals.get("total", 0) or 0
        assists = passes.get("assists", 0) or 0
        
        # Calculate importance score
        # High minutes + appearances = regular player
        # Goals + assists = attacking contribution
        if appearances > 0:
            minutes_per_game = minutes / appearances
            attacking_contribution = goals_scored + assists
            
            # Key player thresholds
            is_regular = appearances >= 10 and minutes_per_game >= 45
            is_contributor = attacking_contribution >= 3 or minutes_per_game >= 70
            
            if is_regular and is_contributor:
                importance_score = (
                    (minutes_per_game / 90) * 0.4 +  # Playing time weight
                    (appearances / 30) * 0.3 +        # Consistency weight  
                    (attacking_contribution / 10) * 0.3  # Contribution weight
                )
                
                key_players.append({
                    "name": player.get("name", "Unknown"),
                    "position": main_stats.get("games", {}).get("position", "Unknown"),
                    "minutes": minutes,
                    "appearances": appearances,
                    "goals": goals_scored,
                    "assists": assists,
                    "importance_score": min(1.0, importance_score)
                })
    
    # Sort by importance and return top players
    key_players.sort(key=lambda x: x["importance_score"], reverse=True)
    return key_players[:8]  # Top 8 key players

def analyze_player_availability(injuries_data, key_players, team_name):
    """
    Analyze impact of injuries/suspensions on key players
    
    Availability impact:
    - Number of key players unavailable
    - Importance of unavailable players
    - Duration of unavailability
    """
    
    if not key_players:
        return {
            "availability_factor": FALLBACK_SCORE,
            "unavailable_players": 0,
            "key_players_count": 0,
            "impact_level": "Unknown",
            "missing_key_players": []
        }
    
    # Create mapping of player names for injury matching
    key_player_names = {player["name"].lower(): player for player in key_players}
    
    unavailable_key_players = []
    total_importance_lost = 0.0
    
    if injuries_data:
        for injury_info in injuries_data:
            player = injury_info.get("player", {})
            injury = injury_info.get("injury", {})
            
            player_name = player.get("name", "").lower()
            injury_type = injury.get("type", "Unknown")
            injury_reason = injury.get("reason", "Unknown")
            
            # Check if injured player is a key player
            if player_name in key_player_names:
                key_player = key_player_names[player_name]
                unavailable_key_players.append({
                    "name": player.get("name", "Unknown"),
                    "injury_type": injury_type,
                    "reason": injury_reason,
                    "importance": key_player["importance_score"]
                })
                total_importance_lost += key_player["importance_score"]
    
    # Calculate availability factor
    total_key_importance = sum(p["importance_score"] for p in key_players)
    
    if total_key_importance > 0:
        availability_factor = 1.0 - (total_importance_lost / total_key_importance)
    else:
        availability_factor = FALLBACK_SCORE
    
    # Ensure reasonable bounds
    availability_factor = max(0.2, min(1.0, availability_factor))
    
    # Determine impact level
    unavailable_count = len(unavailable_key_players)
    key_count = len(key_players)
    
    if unavailable_count == 0:
        impact_level = "No key players missing"
    elif unavailable_count >= key_count * 0.5:
        impact_level = "Severe impact"
    elif unavailable_count >= key_count * 0.25:
        impact_level = "Moderate impact"
    else:
        impact_level = "Minor impact"
    
    return {
        "availability_factor": round(availability_factor, 3),
        "unavailable_players": unavailable_count,
        "key_players_count": key_count,
        "impact_level": impact_level,
        "missing_key_players": unavailable_key_players
    }

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

def update_key_player_availability(competition_name=None):
    """Update key player availability for specified competition or all competitions"""
    print("🏥 KEY PLAYER AVAILABILITY ANALYSIS - PHASE 1 PARAMETER")
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
            
        print(f"\n🏥 Processing {comp_name}")
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
        
        availability_data = {}
        
        # Analyze each team's key player availability
        for i, (team_id, team_name) in enumerate(competition_teams, 1):
            print(f"[{i}/{len(competition_teams)}] Processing {team_name}...")
            
            # Get API ID from mapping
            api_team_id = TEAM_API_IDS.get(team_name)
            
            if not api_team_id:
                print(f"   ⚠️ No API ID for {team_name}")
                availability_data[team_id] = {
                    "team_name": team_name,
                    "key_player_availability": FALLBACK_SCORE,
                    "impact_level": "Unknown"
                }
                continue

            try:
                # Fetch team players and injuries
                players_data = fetch_team_players(api_team_id, team_name)
                injuries_data = fetch_team_injuries(api_team_id, team_name)
                
                # Identify key players
                key_players = identify_key_players(players_data, team_name)
                
                # Analyze availability impact
                availability_analysis = analyze_player_availability(injuries_data, key_players, team_name)
                
                availability_data[team_id] = {
                    "team_name": team_name,
                    "key_player_availability": availability_analysis["availability_factor"],
                    "impact_level": availability_analysis["impact_level"],
                    "key_players_count": availability_analysis["key_players_count"],
                    "unavailable_players": availability_analysis["unavailable_players"],
                    "missing_key_players": availability_analysis["missing_key_players"]
                }
                
                print(f"   👥 Key players: {availability_analysis['key_players_count']}")
                print(f"   🏥 Unavailable: {availability_analysis['unavailable_players']} ({availability_analysis['impact_level']})")
                print(f"   ✅ Availability factor: {availability_analysis['availability_factor']:.3f}")
                
                if availability_analysis['missing_key_players']:
                    missing_names = [p['name'] for p in availability_analysis['missing_key_players'][:3]]
                    print(f"      Missing: {', '.join(missing_names)}")
                
            except Exception as e:
                print(f"   ❌ Failed for {team_name}: {e}")
                availability_data[team_id] = {
                    "team_name": team_name,
                    "key_player_availability": FALLBACK_SCORE,
                    "impact_level": "Error"
                }
        
        # Normalize scores within this competition
        print(f"\n📊 Normalizing {comp_name} availability scores...")
        availability_data = normalize_competition_scores(availability_data, 'key_player_availability')
        
        # Update database
        print(f"💾 Updating database for {comp_name}...")
        
        for team_id, data in availability_data.items():
            c.execute("""
                UPDATE competition_team_strength 
                SET key_player_availability = ?, availability_normalized = ?,
                    last_updated = ?
                WHERE team_id = ? AND competition_id = ? AND season = ?
            """, (
                data['key_player_availability'], data['key_player_availability_normalized'],
                datetime.now(timezone.utc), team_id, comp_id, SEASON
            ))
            
            print(f"   ✅ {data['team_name']}: {data['key_player_availability']:.3f} → {data['key_player_availability_normalized']:.3f} ({data['impact_level']})")
        
        # Show competition summary
        scores = [data['key_player_availability_normalized'] for data in availability_data.values()]
        if scores:
            print(f"\n📈 {comp_name} Summary:")
            print(f"   Availability range: {min(scores):.3f} - {max(scores):.3f}")
            print(f"   Teams analyzed: {len(availability_data)}")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Key player availability analysis complete!")

if __name__ == "__main__":
    # Process all domestic leagues
    update_key_player_availability()