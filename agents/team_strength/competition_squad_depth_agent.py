#!/usr/bin/env python3
"""
Competition-aware squad depth agent with per-competition normalization
Supports multiple leagues and European competitions
"""
import sqlite3
import requests
import json
import uuid
from datetime import datetime, timezone
from collections import defaultdict

API_KEY = "53faec37f076f995841d30d0f7b2dd9d"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}
SEASON = 2024
FALLBACK_SCORE = 0.5

def fetch_full_squad_with_pagination(team_api_id, team_name):
    """Fetch complete squad handling API pagination"""
    all_players = []
    page = 1
    max_pages = 5  # Safety limit
    
    while page <= max_pages:
        url = f"{BASE_URL}/players"
        params = {
            "team": team_api_id,
            "season": SEASON,
            "page": page
        }
        
        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=15)
            data = response.json()
            
            if response.status_code != 200:
                print(f"   ⚠️ API Error {response.status_code} for {team_name}")
                break
            
            players = data.get("response", [])
            
            if not players:  # No more players
                break
                
            all_players.extend(players)
            
            # Check if there are more pages
            paging = data.get("paging", {})
            total_pages = paging.get("total", 1)
            
            if page >= total_pages:
                break
                
            page += 1
            
        except Exception as e:
            print(f"   ❌ Error fetching page {page} for {team_name}: {e}")
            break
    
    return all_players

def analyze_squad_composition(players, team_name):
    """Analyze squad composition for depth scoring"""
    if not players:
        return {
            "total_players": 0,
            "goalkeepers": 0,
            "defenders": 0, 
            "midfielders": 0,
            "forwards": 0,
            "avg_age": 0,
            "raw_depth_score": FALLBACK_SCORE
        }
    
    positions = defaultdict(int)
    ages = []
    
    for player_data in players:
        player = player_data.get('player', {})
        stats = player_data.get('statistics', [{}])
        
        # Get position
        if stats and len(stats) > 0:
            position = stats[0].get('games', {}).get('position', 'Unknown')
        else:
            position = 'Unknown'
        
        # Categorize positions
        if position in ['Goalkeeper', 'G']:
            positions['goalkeepers'] += 1
        elif position in ['Defender', 'D']:
            positions['defenders'] += 1
        elif position in ['Midfielder', 'M']:
            positions['midfielders'] += 1
        elif position in ['Attacker', 'F']:
            positions['forwards'] += 1
        else:
            positions['other'] += 1
        
        # Get age
        age = player.get('age')
        if age and isinstance(age, int) and 16 <= age <= 45:
            ages.append(age)
    
    total_players = len(players)
    avg_age = sum(ages) / len(ages) if ages else 25
    
    # Calculate raw depth score (absolute, not normalized)
    raw_depth_score = calculate_raw_depth_score(
        total_players,
        positions['goalkeepers'],
        positions['defenders'], 
        positions['midfielders'],
        positions['forwards'],
        avg_age
    )
    
    return {
        "total_players": total_players,
        "goalkeepers": positions['goalkeepers'],
        "defenders": positions['defenders'],
        "midfielders": positions['midfielders'], 
        "forwards": positions['forwards'],
        "avg_age": round(avg_age, 1),
        "raw_depth_score": raw_depth_score
    }

def calculate_raw_depth_score(total, gk, def_, mid, fwd, avg_age):
    """Calculate raw squad depth score (absolute scale, not competition-relative)"""
    
    # Base score from total squad size
    size_score = min(1.0, max(0.0, (total - 18) / 12))  # 18-30 range
    
    # Position balance score
    position_scores = []
    
    # Goalkeeper depth (need 2-3)
    gk_score = min(1.0, max(0.0, (gk - 1) / 2))
    position_scores.append(gk_score)
    
    # Defender depth (need 6-10) 
    def_score = min(1.0, max(0.0, (def_ - 4) / 6))
    position_scores.append(def_score)
    
    # Midfielder depth (need 6-10)
    mid_score = min(1.0, max(0.0, (mid - 4) / 6))
    position_scores.append(mid_score)
    
    # Forward depth (need 3-6)
    fwd_score = min(1.0, max(0.0, (fwd - 2) / 4))
    position_scores.append(fwd_score)
    
    position_balance = sum(position_scores) / len(position_scores)
    
    # Age balance score (ideal: 22-28 average)
    age_score = 1.0 - abs(avg_age - 25) / 10  # Peak around 25
    age_score = max(0.0, min(1.0, age_score))
    
    # Combined score (weighted)
    final_score = (
        size_score * 0.4 +           # 40% squad size
        position_balance * 0.5 +      # 50% position balance  
        age_score * 0.1               # 10% age balance
    )
    
    return round(final_score, 3)

def normalize_competition_scores(competition_data):
    """Normalize squad depth scores within competition (0-1 scale)"""
    if not competition_data:
        return competition_data
    
    raw_scores = [data['raw_depth_score'] for data in competition_data.values()]
    
    if not raw_scores or len(set(raw_scores)) == 1:
        # All teams have same score, assign 0.5 to all
        for team_data in competition_data.values():
            team_data['depth_normalized'] = 0.5
        return competition_data
    
    min_score = min(raw_scores)
    max_score = max(raw_scores)
    score_range = max_score - min_score
    
    # Normalize each team's score within competition
    for team_data in competition_data.values():
        if score_range > 0:
            normalized = (team_data['raw_depth_score'] - min_score) / score_range
        else:
            normalized = 0.5
        team_data['depth_normalized'] = round(normalized, 3)
    
    return competition_data

def update_competition_squad_depth(competition_name=None):
    """Update squad depth scores for specified competition or all competitions"""
    print("👥 COMPETITION-AWARE SQUAD DEPTH ANALYSIS")
    print("="*60)
    
    conn = sqlite3.connect("db/football_strength.db")
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON;")
    
    # Get competitions to process
    if competition_name:
        c.execute("SELECT id, name FROM competitions WHERE name = ?", (competition_name,))
    else:
        c.execute("SELECT id, name FROM competitions WHERE type = 'domestic_league'")
    
    competitions = c.fetchall()
    
    for comp_id, comp_name in competitions:
        print(f"\n🏆 Processing {comp_name}")
        print("-" * 40)
        
        # Get teams in this competition
        c.execute("""
            SELECT ct.team_id, ct.team_name, ct.api_team_id 
            FROM competition_teams ct 
            WHERE ct.competition_id = ? AND ct.season = ?
        """, (comp_id, SEASON))
        
        competition_teams = c.fetchall()
        
        if not competition_teams:
            print(f"   ⚠️ No teams found for {comp_name}")
            continue
        
        squad_data = {}
        
        # Analyze each team's squad depth
        for i, (team_id, team_name, api_team_id) in enumerate(competition_teams, 1):
            print(f"[{i}/{len(competition_teams)}] Processing {team_name}...")
            
            if not api_team_id:
                print(f"   ⚠️ No API ID for {team_name}")
                squad_data[team_id] = {
                    "team_name": team_name,
                    "total_players": 0,
                    "raw_depth_score": FALLBACK_SCORE
                }
                continue

            try:
                # Fetch complete squad
                players = fetch_full_squad_with_pagination(api_team_id, team_name)
                print(f"   📊 Found {len(players)} total players")
                
                # Analyze squad composition
                analysis = analyze_squad_composition(players, team_name)
                analysis["team_name"] = team_name
                squad_data[team_id] = analysis
                
                print(f"   🏟️ Composition: {analysis['goalkeepers']}GK, {analysis['defenders']}DEF, {analysis['midfielders']}MID, {analysis['forwards']}FWD")
                print(f"   📈 Average age: {analysis['avg_age']} years")
                print(f"   ⚽ Raw depth score: {analysis['raw_depth_score']}")
                
            except Exception as e:
                print(f"   ❌ Failed for {team_name}: {e}")
                squad_data[team_id] = {
                    "team_name": team_name,
                    "total_players": 0,
                    "raw_depth_score": FALLBACK_SCORE
                }
        
        # Normalize scores within this competition
        print(f"\n📊 Normalizing {comp_name} scores...")
        squad_data = normalize_competition_scores(squad_data)
        
        # Update database
        print(f"💾 Updating database for {comp_name}...")
        
        for team_id, data in squad_data.items():
            c.execute("""
                INSERT INTO competition_team_strength 
                (id, competition_id, team_id, team_name, squad_depth_score, 
                 squad_depth_normalized, last_updated, season)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(competition_id, team_id, season) DO UPDATE SET
                    squad_depth_score = excluded.squad_depth_score,
                    squad_depth_normalized = excluded.squad_depth_normalized,
                    last_updated = excluded.last_updated
            """, (
                str(uuid.uuid4()), comp_id, team_id, data['team_name'],
                data['raw_depth_score'], data['depth_normalized'],
                datetime.now(timezone.utc), SEASON
            ))
            
            print(f"   ✅ {data['team_name']}: {data['raw_depth_score']} → {data['depth_normalized']}")
        
        # Show competition summary
        scores = [data['depth_normalized'] for data in squad_data.values()]
        if scores:
            print(f"\n📈 {comp_name} Summary:")
            print(f"   Normalized range: {min(scores):.3f} - {max(scores):.3f}")
            print(f"   Teams analyzed: {len(scores)}")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Competition-aware squad depth analysis complete!")

if __name__ == "__main__":
    # Process all domestic leagues
    update_competition_squad_depth()