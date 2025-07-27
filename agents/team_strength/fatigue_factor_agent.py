#!/usr/bin/env python3
"""
Fatigue Factor Agent - Phase 1 Parameter Implementation
Calculates fatigue factor based on fixture congestion and recent match frequency
"""
import sqlite3
import requests
import json
import uuid
import os
from datetime import datetime, timezone, timedelta
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

def fetch_team_fixtures(team_api_id, league_id, team_name):
    """Fetch team fixtures for fatigue analysis"""
    url = f"{BASE_URL}/fixtures"
    params = {
        "team": team_api_id,
        "league": league_id,
        "season": SEASON,
        "last": 20  # Get recent fixtures
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=15)
        data = response.json()
        
        if response.status_code != 200:
            print(f"   ⚠️ API Error {response.status_code} for {team_name}")
            return None
        
        return data.get("response", [])
        
    except Exception as e:
        print(f"   ❌ Error fetching fixtures for {team_name}: {e}")
        return None

def analyze_fixture_congestion(fixtures, team_name):
    """
    Analyze fixture congestion to calculate fatigue factor
    
    Fatigue factors:
    - Days between matches (rest time)
    - Number of competitions involved
    - Travel distance (domestic vs international)
    - Match importance (league vs cups)
    """
    
    if not fixtures:
        return {
            "fatigue_factor": FALLBACK_SCORE,
            "congestion_level": "Unknown",
            "days_rest": 0,
            "recent_matches": 0,
            "competitions": 0
        }
    
    # Parse fixture dates and calculate rest periods
    recent_fixtures = []
    current_date = datetime.now()
    
    for fixture in fixtures:
        fixture_date_str = fixture.get("fixture", {}).get("date", "")
        if fixture_date_str:
            try:
                fixture_date = datetime.fromisoformat(fixture_date_str.replace('Z', '+00:00'))
                
                # Only consider recent matches (last 30 days)
                days_ago = (current_date - fixture_date.replace(tzinfo=None)).days
                if 0 <= days_ago <= 30:
                    recent_fixtures.append({
                        "date": fixture_date,
                        "days_ago": days_ago,
                        "league": fixture.get("league", {}).get("name", "Unknown"),
                        "status": fixture.get("fixture", {}).get("status", {}).get("short", "")
                    })
            except:
                continue
    
    # Sort by date (most recent first)
    recent_fixtures.sort(key=lambda x: x["date"], reverse=True)
    
    if not recent_fixtures:
        return {
            "fatigue_factor": FALLBACK_SCORE,
            "congestion_level": "No recent data",
            "days_rest": 0,
            "recent_matches": 0,
            "competitions": 0
        }
    
    # Calculate fatigue metrics
    recent_matches = len([f for f in recent_fixtures if f["days_ago"] <= 14])  # Last 2 weeks
    competitions = len(set(f["league"] for f in recent_fixtures))
    
    # Calculate average rest between matches
    rest_periods = []
    for i in range(len(recent_fixtures) - 1):
        days_between = (recent_fixtures[i]["date"] - recent_fixtures[i+1]["date"]).days
        rest_periods.append(days_between)
    
    avg_rest = sum(rest_periods) / len(rest_periods) if rest_periods else 7
    
    # Calculate fatigue factor (lower = more fatigued)
    
    # Base fatigue from match frequency
    if recent_matches >= 6:  # More than 3 matches per week
        frequency_factor = 0.2  # Very high fatigue
    elif recent_matches >= 4:  # 2 matches per week
        frequency_factor = 0.4  # High fatigue
    elif recent_matches >= 3:  # 1.5 matches per week
        frequency_factor = 0.6  # Medium fatigue
    elif recent_matches >= 2:  # 1 match per week
        frequency_factor = 0.8  # Low fatigue
    else:
        frequency_factor = 1.0  # No fatigue
    
    # Rest period adjustment
    if avg_rest >= 7:  # Week between matches
        rest_factor = 1.0  # Well rested
    elif avg_rest >= 4:  # 4-6 days rest
        rest_factor = 0.8  # Adequate rest
    elif avg_rest >= 2:  # 2-3 days rest
        rest_factor = 0.6  # Limited rest
    else:  # Less than 2 days
        rest_factor = 0.3  # Very tired
    
    # Competition load adjustment
    if competitions >= 4:  # Playing in many competitions
        comp_factor = 0.7  # High load
    elif competitions >= 3:  # 3 competitions
        comp_factor = 0.8  # Medium load
    elif competitions >= 2:  # 2 competitions
        comp_factor = 0.9  # Normal load
    else:  # Single competition
        comp_factor = 1.0  # Low load
    
    # Calculate final fatigue factor
    fatigue_factor = (frequency_factor * 0.5) + (rest_factor * 0.3) + (comp_factor * 0.2)
    
    # Determine congestion level
    if fatigue_factor >= 0.8:
        congestion_level = "Low congestion"
    elif fatigue_factor >= 0.6:
        congestion_level = "Medium congestion"
    elif fatigue_factor >= 0.4:
        congestion_level = "High congestion"
    else:
        congestion_level = "Extreme congestion"
    
    return {
        "fatigue_factor": round(fatigue_factor, 3),
        "congestion_level": congestion_level,
        "days_rest": round(avg_rest, 1),
        "recent_matches": recent_matches,
        "competitions": competitions
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

def update_fatigue_factors(competition_name=None):
    """Update fatigue factors for specified competition or all competitions"""
    print("😴 FATIGUE FACTOR ANALYSIS - PHASE 1 PARAMETER")
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
            
        print(f"\n😴 Processing {comp_name}")
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
        
        fatigue_data = {}
        
        # Analyze each team's fixture congestion
        for i, (team_id, team_name) in enumerate(competition_teams, 1):
            print(f"[{i}/{len(competition_teams)}] Processing {team_name}...")
            
            # Get API ID from mapping
            api_team_id = TEAM_API_IDS.get(team_name)
            
            if not api_team_id:
                print(f"   ⚠️ No API ID for {team_name}")
                fatigue_data[team_id] = {
                    "team_name": team_name,
                    "fatigue_factor": FALLBACK_SCORE,
                    "congestion_level": "Unknown"
                }
                continue

            try:
                # Fetch team fixtures
                fixtures = fetch_team_fixtures(api_team_id, league_id, team_name)
                
                # Analyze fixture congestion
                fatigue_analysis = analyze_fixture_congestion(fixtures, team_name)
                
                fatigue_data[team_id] = {
                    "team_name": team_name,
                    "fatigue_factor": fatigue_analysis["fatigue_factor"],
                    "congestion_level": fatigue_analysis["congestion_level"],
                    "days_rest": fatigue_analysis["days_rest"],
                    "recent_matches": fatigue_analysis["recent_matches"],
                    "competitions": fatigue_analysis["competitions"]
                }
                
                print(f"   🏃 Level: {fatigue_analysis['congestion_level']}")
                print(f"   📅 Recent matches: {fatigue_analysis['recent_matches']}, Avg rest: {fatigue_analysis['days_rest']} days")
                print(f"   😴 Fatigue factor: {fatigue_analysis['fatigue_factor']:.3f}")
                
            except Exception as e:
                print(f"   ❌ Failed for {team_name}: {e}")
                fatigue_data[team_id] = {
                    "team_name": team_name,
                    "fatigue_factor": FALLBACK_SCORE,
                    "congestion_level": "Error"
                }
        
        # Normalize scores within this competition
        print(f"\n📊 Normalizing {comp_name} fatigue scores...")
        fatigue_data = normalize_competition_scores(fatigue_data, 'fatigue_factor')
        
        # Update database
        print(f"💾 Updating database for {comp_name}...")
        
        for team_id, data in fatigue_data.items():
            c.execute("""
                UPDATE competition_team_strength 
                SET fatigue_factor = ?, fatigue_normalized = ?,
                    last_updated = ?
                WHERE team_id = ? AND competition_id = ? AND season = ?
            """, (
                data['fatigue_factor'], data['fatigue_factor_normalized'],
                datetime.now(timezone.utc), team_id, comp_id, SEASON
            ))
            
            print(f"   ✅ {data['team_name']}: {data['fatigue_factor']:.3f} → {data['fatigue_factor_normalized']:.3f} ({data['congestion_level']})")
        
        # Show competition summary
        scores = [data['fatigue_factor_normalized'] for data in fatigue_data.values()]
        if scores:
            print(f"\n📈 {comp_name} Summary:")
            print(f"   Fatigue range: {min(scores):.3f} - {max(scores):.3f}")
            print(f"   Teams analyzed: {len(fatigue_data)}")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Fatigue factor analysis complete!")

if __name__ == "__main__":
    # Process all domestic leagues
    update_fatigue_factors()