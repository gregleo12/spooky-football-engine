#!/usr/bin/env python3
"""
Tactical Matchup Agent - Phase 1 Parameter Implementation
Calculates tactical style advantages based on team playing styles
"""
import requests
import json
import uuid
import os
import sys
from datetime import datetime, timezone
from collections import defaultdict

# Add project root to path for database config
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from database_config import db_config

API_KEY = '53faec37f076f995841d30d0f7b2dd9d'
BASE_URL = 'https://v3.football.api-sports.io'
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

def fetch_team_statistics(team_api_id, league_id, team_name):
    """Fetch detailed team statistics for tactical analysis"""
    url = f"{BASE_URL}/teams/statistics"
    params = {
        "team": team_api_id,
        "league": league_id,
        "season": SEASON
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=15)
        data = response.json()
        
        if response.status_code != 200:
            print(f"   ⚠️ API Error {response.status_code} for {team_name}")
            return None
        
        return data.get("response", {})
        
    except Exception as e:
        print(f"   ❌ Error fetching statistics for {team_name}: {e}")
        return None

def analyze_playing_style(stats, team_name):
    """
    Analyze team's playing style based on statistics
    
    Style dimensions:
    - Offensive vs Defensive focus
    - Possession vs Counter-attacking
    - Direct vs Build-up play
    - High vs Low defensive line
    """
    
    if not stats:
        return {
            "style_profile": "Unknown",
            "offensive_rating": 0.5,
            "defensive_rating": 0.5,
            "possession_style": 0.5,
            "directness": 0.5,
            "tactical_score": FALLBACK_SCORE
        }
    
    # Extract key statistics
    fixtures = stats.get('fixtures', {})
    goals = stats.get('goals', {})
    
    matches_played = fixtures.get('played', {}).get('total', 0)
    if matches_played == 0:
        return {
            "style_profile": "Insufficient data",
            "offensive_rating": 0.5,
            "defensive_rating": 0.5, 
            "possession_style": 0.5,
            "directness": 0.5,
            "tactical_score": FALLBACK_SCORE
        }
    
    goals_for = goals.get('for', {}).get('total', {}).get('total', 0)
    goals_against = goals.get('against', {}).get('total', {}).get('total', 0)
    
    # Calculate style metrics
    
    # 1. Offensive rating (goals per game normalized)
    goals_per_game = goals_for / matches_played
    offensive_rating = min(1.0, goals_per_game / 3.0)  # 3 goals/game = 1.0
    
    # 2. Defensive rating (inverted goals conceded)
    goals_conceded_per_game = goals_against / matches_played
    defensive_rating = max(0.0, 1.0 - (goals_conceded_per_game / 3.0))
    
    # 3. Style analysis based on goal patterns
    total_goals = goals_for + goals_against
    if total_goals > 0:
        attacking_tendency = goals_for / total_goals
    else:
        attacking_tendency = 0.5
    
    # 4. Estimate possession style (based on goals and defensive record)
    # Teams that score more and concede less often play possession football
    if defensive_rating > 0.7 and offensive_rating > 0.6:
        possession_style = 0.8  # High possession
    elif defensive_rating < 0.4:
        possession_style = 0.2  # Counter-attacking
    else:
        possession_style = 0.5  # Balanced
    
    # 5. Directness (estimated from goal/game ratio)
    # High-scoring teams with average defense = direct
    # Low-scoring teams with good defense = possession-based
    if offensive_rating > 0.7 and defensive_rating < 0.6:
        directness = 0.8  # Very direct
    elif offensive_rating < 0.5 and defensive_rating > 0.7:
        directness = 0.2  # Build-up play
    else:
        directness = 0.5  # Balanced
    
    # Calculate overall tactical score
    # Balanced teams get higher scores (easier to predict and analyze)
    balance_score = 1.0 - abs(offensive_rating - defensive_rating)
    consistency_score = (offensive_rating + defensive_rating) / 2
    tactical_score = (balance_score * 0.3) + (consistency_score * 0.7)
    
    # Determine style profile
    if offensive_rating > 0.7 and possession_style > 0.6:
        style_profile = 'Possession-based attacking'
    elif offensive_rating > 0.7 and directness > 0.6:
        style_profile = 'Direct attacking'
    elif defensive_rating > 0.7 and possession_style > 0.6:
        style_profile = 'Possession-based defensive'
    elif defensive_rating > 0.7:
        style_profile = 'Counter-attacking'
    elif balance_score > 0.7:
        style_profile = 'Balanced'
    else:
        style_profile = 'Inconsistent'
    
    return {
        "style_profile": style_profile,
        "offensive_rating": round(offensive_rating, 3),
        "defensive_rating": round(defensive_rating, 3),
        "possession_style": round(possession_style, 3),
        "directness": round(directness, 3),
        "tactical_score": round(tactical_score, 3)
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

def update_tactical_matchups(competition_name=None):
    """Update tactical matchup scores for specified competition or all competitions"""
    print("⚔️ TACTICAL MATCHUP ANALYSIS - PHASE 1 PARAMETER")
    print("=" * 60)
    
    conn = db_config.get_connection()
    c = conn.cursor()
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
        c.execute("SELECT id, name FROM competitions WHERE name = %s", (competition_name,))
    else:
        c.execute("SELECT id, name FROM competitions WHERE type = 'domestic_league'")
    
    competitions = c.fetchall()
    
    for comp_id, comp_name in competitions:
        if comp_name not in league_ids:
            print(f"⚠️ Skipping {comp_name} - no league ID mapping")
            continue
            
        print(f"\n⚔️ Processing {comp_name}")
        print("-" * 40)
        
        league_id = league_ids[comp_name]
        
        # Get teams in this competition
        c.execute("""
            SELECT cts.team_id, cts.team_name
            FROM competition_team_strength cts
            WHERE cts.competition_id = %s AND cts.season = %s
            AND cts.team_name IS NOT NULL
        """, (comp_id, str(SEASON)))
        
        competition_teams = c.fetchall()
        
        if not competition_teams:
            print(f"   ⚠️ No teams found for {comp_name}")
            continue
        
        tactical_data = {}
        
        # Analyze each team's tactical style
        for i, (team_id, team_name) in enumerate(competition_teams, 1):
            print(f"[{i}/{len(competition_teams)}] Processing {team_name}...")
            
            # Get API ID from mapping
            api_team_id = TEAM_API_IDS.get(team_name)
            
            if not api_team_id:
                print(f"   ⚠️ No API ID for {team_name}")
                tactical_data[team_id] = {
                    "team_name": team_name,
                    "tactical_matchup": FALLBACK_SCORE,
                    "style_profile": "Unknown"
                }
                continue

            try:
                # Fetch team statistics
                stats = fetch_team_statistics(api_team_id, league_id, team_name)
                
                # Analyze playing style
                style_analysis = analyze_playing_style(stats, team_name)
                
                tactical_data[team_id] = {
                    "team_name": team_name,
                    "tactical_matchup": style_analysis["tactical_score"],
                    "style_profile": style_analysis["style_profile"],
                    "offensive_rating": style_analysis["offensive_rating"],
                    "defensive_rating": style_analysis["defensive_rating"],
                    "possession_style": style_analysis["possession_style"],
                    "directness": style_analysis["directness"]
                }
                
                print(f"   📊 Style: {style_analysis['style_profile']}")
                print(f"   ⚔️ Off: {style_analysis['offensive_rating']:.3f}, Def: {style_analysis['defensive_rating']:.3f}")
                print(f"   📈 Tactical score: {style_analysis['tactical_score']:.3f}")
                
            except Exception as e:
                print(f"   ❌ Failed for {team_name}: {e}")
                tactical_data[team_id] = {
                    "team_name": team_name,
                    "tactical_matchup": FALLBACK_SCORE,
                    "style_profile": "Error"
                }
        
        # Normalize scores within this competition
        print(f"\n📊 Normalizing {comp_name} tactical scores...")
        tactical_data = normalize_competition_scores(tactical_data, 'tactical_matchup')
        
        # Update database
        print(f"💾 Updating database for {comp_name}...")
        
        for team_id, data in tactical_data.items():
            c.execute("""
                UPDATE competition_team_strength 
                SET tactical_matchup_score = %s, tactical_matchup_normalized = %s,
                    last_updated = %s
                WHERE team_id = %s AND competition_id = %s AND season = %s
            """, (
                data['tactical_matchup'], data['tactical_matchup_normalized'],
                datetime.now(timezone.utc), team_id, comp_id, str(SEASON)
            ))
            
            print(f"   ✅ {data['team_name']}: {data['tactical_matchup']:.3f} → {data['tactical_matchup_normalized']:.3f} ({data['style_profile']})")
        
        # Show competition summary
        scores = [data['tactical_matchup_normalized'] for data in tactical_data.values()]
        if scores:
            print(f"\n📈 {comp_name} Summary:")
            print(f"   Tactical range: {min(scores):.3f} - {max(scores):.3f}")
            print(f"   Teams analyzed: {len(tactical_data)}")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Tactical matchup analysis complete!")

if __name__ == '__main__':
    # Process all domestic leagues
    update_tactical_matchups()