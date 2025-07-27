#!/usr/bin/env python3
"""
Motivation Factor Agent - Phase 1 Parameter Implementation
Calculates motivation factor based on league position and situational context
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

def fetch_league_standings(league_id, team_name):
    """Fetch current league standings to determine team position"""
    url = f"{BASE_URL}/standings"
    params = {
        "league": league_id,
        "season": SEASON
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=15)
        data = response.json()
        
        if response.status_code != 200:
            print(f"   ⚠️ API Error {response.status_code} for standings")
            return None
        
        standings = data.get("response", [])
        if standings and len(standings) > 0:
            return standings[0].get("league", {}).get("standings", [[]])[0]
        
        return None
        
    except Exception as e:
        print(f"   ❌ Error fetching standings: {e}")
        return None

def calculate_motivation_factor(team_position, total_teams, points, points_above_relegation, points_behind_leader):
    """
    Calculate motivation factor based on league position and context
    
    Motivation scenarios:
    - Title race (top 4): High motivation (0.8-1.0)
    - European spots (5-7): Medium-high motivation (0.6-0.8)
    - Mid-table (8-12): Low motivation (0.3-0.6) 
    - Relegation battle (bottom 3): Very high motivation (0.9-1.0)
    - Safe mid-table: Lowest motivation (0.2-0.4)
    """
    
    if not team_position or not total_teams:
        return FALLBACK_SCORE
    
    # Position-based motivation
    position_ratio = team_position / total_teams
    
    # Title race motivation (top 25%)
    if position_ratio <= 0.25:
        base_motivation = 0.85
        # Closer to top = higher motivation
        title_proximity = (0.25 - position_ratio) / 0.25
        motivation = base_motivation + (title_proximity * 0.15)
    
    # European competition spots (positions 25-35%)
    elif position_ratio <= 0.35:
        base_motivation = 0.7
        european_factor = (0.35 - position_ratio) / 0.1
        motivation = base_motivation + (european_factor * 0.1)
    
    # Relegation battle (bottom 15%)
    elif position_ratio >= 0.85:
        base_motivation = 0.9
        # Closer to relegation = higher motivation
        relegation_proximity = (position_ratio - 0.85) / 0.15
        motivation = base_motivation + (relegation_proximity * 0.1)
    
    # Safe mid-table (lowest motivation)
    else:
        # Mid-table teams have lowest motivation
        mid_table_factor = abs(position_ratio - 0.5) / 0.5  # Distance from middle
        motivation = 0.25 + (mid_table_factor * 0.35)
    
    # Points-based adjustments
    if points_behind_leader is not None and points_behind_leader <= 5:
        motivation += 0.1  # In title race
    
    if points_above_relegation is not None and points_above_relegation <= 5:
        motivation += 0.15  # Fighting relegation
    
    # Ensure within bounds
    motivation = max(0.0, min(1.0, motivation))
    
    return round(motivation, 3)

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

def update_motivation_factors(competition_name=None):
    """Update motivation factors for specified competition or all competitions"""
    print("🔥 MOTIVATION FACTOR ANALYSIS - PHASE 1 PARAMETER")
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
            
        print(f"\n🔥 Processing {comp_name}")
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
        
        # Fetch league standings
        standings = fetch_league_standings(league_id, comp_name)
        
        if not standings:
            print(f"   ⚠️ Could not fetch standings for {comp_name}")
            # Use fallback motivation based on historical data
            motivation_data = {}
            for team_id, team_name in competition_teams:
                motivation_data[team_id] = {
                    "team_name": team_name,
                    "motivation_factor": FALLBACK_SCORE,
                    "position": None,
                    "points": None,
                    "context": "No standings data"
                }
        else:
            # Create position lookup
            position_lookup = {}
            total_teams = len(standings)
            
            for standing in standings:
                team_info = standing.get("team", {})
                team_name_api = team_info.get("name", "")
                position = standing.get("rank", 0)
                points = standing.get("points", 0)
                
                position_lookup[team_name_api] = {
                    "position": position,
                    "points": points,
                    "total_teams": total_teams
                }
            
            motivation_data = {}
            
            # Calculate motivation for each team
            for team_id, team_name in competition_teams:
                print(f"   Processing {team_name}...")
                
                # Try to find team in standings
                team_standing = None
                for api_name, standing_data in position_lookup.items():
                    if team_name.lower() in api_name.lower() or api_name.lower() in team_name.lower():
                        team_standing = standing_data
                        break
                
                if team_standing:
                    position = team_standing["position"]
                    points = team_standing["points"]
                    total_teams = team_standing["total_teams"]
                    
                    # Calculate points context
                    all_points = [s["points"] for s in position_lookup.values()]
                    leader_points = max(all_points)
                    relegation_points = sorted(all_points)[2] if len(all_points) > 3 else min(all_points)
                    
                    points_behind_leader = leader_points - points
                    points_above_relegation = points - relegation_points
                    
                    motivation = calculate_motivation_factor(
                        position, total_teams, points, 
                        points_above_relegation, points_behind_leader
                    )
                    
                    # Determine context
                    if position <= total_teams * 0.25:
                        context = "Title race"
                    elif position <= total_teams * 0.35:
                        context = "European spots"
                    elif position >= total_teams * 0.85:
                        context = "Relegation battle"
                    else:
                        context = "Mid-table"
                    
                    motivation_data[team_id] = {
                        "team_name": team_name,
                        "motivation_factor": motivation,
                        "position": position,
                        "points": points,
                        "context": context
                    }
                    
                    print(f"      Position: {position}/{total_teams} ({context})")
                    print(f"      Points: {points} (behind leader: {points_behind_leader})")
                    print(f"      Motivation: {motivation:.3f}")
                
                else:
                    motivation_data[team_id] = {
                        "team_name": team_name,
                        "motivation_factor": FALLBACK_SCORE,
                        "position": None,
                        "points": None,
                        "context": "Not found in standings"
                    }
                    print(f"      ⚠️ Not found in standings, using fallback: {FALLBACK_SCORE}")
        
        # Normalize scores within this competition
        print(f"\n📊 Normalizing {comp_name} motivation scores...")
        motivation_data = normalize_competition_scores(motivation_data, 'motivation_factor')
        
        # Update database
        print(f"💾 Updating database for {comp_name}...")
        
        for team_id, data in motivation_data.items():
            c.execute("""
                UPDATE competition_team_strength 
                SET motivation_factor = ?, motivation_normalized = ?,
                    current_position = ?,
                    last_updated = ?
                WHERE team_id = ? AND competition_id = ? AND season = ?
            """, (
                data['motivation_factor'], data['motivation_factor_normalized'],
                data['position'],
                datetime.now(timezone.utc), team_id, comp_id, SEASON
            ))
            
            print(f"   ✅ {data['team_name']}: {data['motivation_factor']:.3f} → {data['motivation_factor_normalized']:.3f} ({data['context']})")
        
        # Show competition summary
        scores = [data['motivation_factor_normalized'] for data in motivation_data.values()]
        if scores:
            print(f"\n📈 {comp_name} Summary:")
            print(f"   Motivation range: {min(scores):.3f} - {max(scores):.3f}")
            print(f"   Teams analyzed: {len(motivation_data)}")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Motivation factor analysis complete!")

if __name__ == "__main__":
    # Process all domestic leagues
    update_motivation_factors()