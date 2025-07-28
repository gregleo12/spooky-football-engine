#!/usr/bin/env python3
"""
Enhanced Squad Value Agent - Phase 1 Parameter Implementation
Improved squad value calculation with position weighting and market trends
"""
import requests
import json
import uuid
import os
import sys
from datetime import datetime, timezone
from collections import defaultdict
from bs4 import BeautifulSoup

# Add project root to path for database config
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from database_config import db_config

API_KEY = '53faec37f076f995841d30d0f7b2dd9d'
BASE_URL = 'https://v3.football.api-sports.io'
HEADERS = {"x-apisports-key": API_KEY}
SEASON = 2024
FALLBACK_SCORE = 50.0  # €50M default squad value

# Load team API ID mapping
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEAM_API_IDS_PATH = os.path.join(SCRIPT_DIR, "..", "shared", "team_api_ids.json")

try:
    with open(TEAM_API_IDS_PATH, 'r', encoding='utf-8') as f:
        TEAM_API_IDS = json.load(f)
except FileNotFoundError:
    print(f"⚠️ Warning: team_api_ids.json not found at {TEAM_API_IDS_PATH}")
    TEAM_API_IDS = {}

# Team name to Transfermarkt URL mapping (subset for validation)
TRANSFERMARKT_MAPPING = {
    'Arsenal': 'fc-arsenal',
    'Chelsea': 'fc-chelsea',
    'Manchester City': 'manchester-city',
    'Manchester United': 'manchester-united',
    'Liverpool': 'fc-liverpool',
    'Tottenham Hotspur': 'tottenham-hotspur',
    'Real Madrid': 'real-madrid',
    'Barcelona': 'fc-barcelona',
    'Atletico Madrid': 'atletico-madrid',
    'Bayern München': 'fc-bayern-munchen',
    'Borussia Dortmund': 'borussia-dortmund',
    'RB Leipzig': 'rasenballsport-leipzig',
    'Paris Saint Germain': 'paris-saint-germain',
    'AC Milan': 'ac-mailand',
    'Inter': 'inter-mailand',
    'Juventus': 'juventus-turin'
}

def fetch_squad_players(team_api_id, team_name):
    """Fetch squad players from API-Football"""
    url = f"{BASE_URL}/players"
    params = {
        "team": team_api_id,
        "season": SEASON,
        "page": 1
    }
    
    all_players = []
    max_pages = 3  # Limit for efficiency
    
    for page in range(1, max_pages + 1):
        params["page"] = page
        
        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=15)
            data = response.json()
            
            if response.status_code != 200:
                print(f"   ⚠️ API Error {response.status_code} for {team_name}")
                break
            
            players = data.get("response", [])
            if not players:
                break
                
            all_players.extend(players)
            
            # Check if more pages exist
            paging = data.get("paging", {})
            if page >= paging.get("total", 1):
                break
                
        except Exception as e:
            print(f"   ❌ Error fetching players for {team_name}: {e}")
            break
    
    return all_players

def scrape_transfermarkt_value(team_name):
    """Scrape squad value from Transfermarkt (fallback method)"""
    if team_name not in TRANSFERMARKT_MAPPING:
        return None
    
    team_url = TRANSFERMARKT_MAPPING[team_name]
    url = f"https://www.transfermarkt.com/{team_url}/startseite/verein/1"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for squad value element
        value_elements = soup.find_all('span', class_='waehrung')
        for element in value_elements:
            text = element.get_text(strip=True)
            if '€' in text and ('m' in text.lower() or 'k' in text.lower()):
                # Parse value like "€1.25bn" or "€850.00m"
                value_str = text.replace('€', '').replace(',', '').lower()
                if 'bn' in value_str:
                    value = float(value_str.replace('bn', '')) * 1000
                elif 'm' in value_str:
                    value = float(value_str.replace('m', ''))
                elif 'k' in value_str:
                    value = float(value_str.replace('k', '')) / 1000
                else:
                    continue
                return round(value, 2)
                
    except Exception as e:
        print(f"   ⚠️ Could not scrape Transfermarkt for {team_name}: {e}")
    
    return None

def calculate_enhanced_squad_value(players, team_name):
    """Calculate enhanced squad value with position weighting and age factors"""
    if not players:
        # Try Transfermarkt scraping as fallback
        tm_value = scrape_transfermarkt_value(team_name)
        return tm_value if tm_value else FALLBACK_SCORE
    
    # Position value multipliers (based on market reality)
    position_multipliers = {
        'Goalkeeper': 0.8,    # GKs typically worth less
        'Defender': 1.0,      # Standard baseline
        'Midfielder': 1.2,    # Often most valuable
        'Attacker': 1.3       # Forwards command premium
    }
    
    total_value = 0
    player_count = 0
    position_distribution = defaultdict(int)
    age_groups = defaultdict(int)
    
    for player_data in players:
        player = player_data.get('player', {})
        stats = player_data.get('statistics', [{}])
        
        if not stats:
            continue
            
        # Get position
        position = 'Unknown'
        if stats and len(stats) > 0:
            position = stats[0].get('games', {}).get('position', 'Unknown')
        
        # Standardize position names
        if position in ['Goalkeeper', 'G']:
            position_category = 'Goalkeeper'
        elif position in ['Defender', 'D']:
            position_category = 'Defender'
        elif position in ['Midfielder', 'M']:
            position_category = 'Midfielder'
        elif position in ['Attacker', 'F']:
            position_category = 'Attacker'
        else:
            position_category = 'Defender'  # Default
        
        # Get age
        age = player.get('age', 25)
        if age is None:
            age = 25
        
        # Age value factor (peak value around 24-27)
        if age < 20:
            age_factor = 0.7  # Young, unproven
        elif age < 24:
            age_factor = 0.9  # Developing
        elif age <= 27:
            age_factor = 1.0  # Peak value
        elif age <= 30:
            age_factor = 0.9  # Still valuable
        elif age <= 33:
            age_factor = 0.7  # Declining value
        else:
            age_factor = 0.5  # Veteran
        
        # Base player value estimation (simplified model)
        # Based on games played and position
        games_played = stats[0].get('games', {}).get('appearences', 0) if stats else 0
        
        if games_played == 0:
            base_value = 1.0  # Minimal value for unused players
        elif games_played < 5:
            base_value = 3.0  # Squad players
        elif games_played < 15:
            base_value = 8.0  # Rotation players
        elif games_played < 25:
            base_value = 15.0  # Regular players
        else:
            base_value = 25.0  # Key players
        
        # Apply modifiers
        position_multiplier = position_multipliers.get(position_category, 1.0)
        player_value = base_value * position_multiplier * age_factor
        
        total_value += player_value
        player_count += 1
        position_distribution[position_category] += 1
        
        # Age group tracking
        if age < 23:
            age_groups['young'] += 1
        elif age <= 28:
            age_groups['prime'] += 1
        else:
            age_groups['veteran'] += 1
    
    if player_count == 0:
        return FALLBACK_SCORE
    
    # Squad balance bonuses
    balance_bonus = 1.0
    
    # Position balance bonus (well-distributed squad gets bonus)
    gk_ratio = position_distribution['Goalkeeper'] / max(1, player_count)
    def_ratio = position_distribution['Defender'] / max(1, player_count)
    mid_ratio = position_distribution['Midfielder'] / max(1, player_count)
    att_ratio = position_distribution['Attacker'] / max(1, player_count)
    
    # Ideal ratios: ~10% GK, 35% DEF, 35% MID, 20% ATT
    position_balance = (
        abs(gk_ratio - 0.10) +
        abs(def_ratio - 0.35) +
        abs(mid_ratio - 0.35) +
        abs(att_ratio - 0.20)
    )
    
    if position_balance < 0.2:  # Well balanced
        balance_bonus *= 1.1
    elif position_balance > 0.4:  # Poorly balanced
        balance_bonus *= 0.9
    
    # Age diversity bonus (mix of young, prime, veteran is good)
    if age_groups['young'] > 0 and age_groups['prime'] > 0 and age_groups['veteran'] > 0:
        balance_bonus *= 1.05
    
    # Squad size factor
    if player_count < 20:
        size_factor = 0.9  # Small squad penalty
    elif player_count > 35:
        size_factor = 0.95  # Bloated squad slight penalty
    else:
        size_factor = 1.0
    
    final_value = total_value * balance_bonus * size_factor
    
    return round(final_value, 2)

def normalize_competition_scores(competition_data):
    """Normalize squad values within competition (0-1 scale)"""
    if not competition_data:
        return competition_data
    
    values = [data['enhanced_squad_value'] for data in competition_data.values()]
    
    if not values or len(set(values)) == 1:
        # All teams have same value, assign 0.5 to all
        for team_data in competition_data.values():
            team_data['squad_value_normalized'] = 0.5
        return competition_data
    
    min_value = min(values)
    max_value = max(values)
    value_range = max_value - min_value
    
    # Normalize each team's value within competition
    for team_data in competition_data.values():
        if value_range > 0:
            normalized = (team_data['enhanced_squad_value'] - min_value) / value_range
        else:
            normalized = 0.5
        team_data['squad_value_normalized'] = round(normalized, 3)
    
    return competition_data

def update_enhanced_squad_values(competition_name=None):
    """Update enhanced squad values for specified competition or all competitions"""
    print("💰 ENHANCED SQUAD VALUE ANALYSIS - PHASE 1")
    print("=" * 60)
    
    conn = db_config.get_connection()
    c = conn.cursor()
        # Get competitions to process
    if competition_name:
        c.execute("SELECT id, name FROM competitions WHERE name = %s", (competition_name,))
    else:
        c.execute("SELECT id, name FROM competitions WHERE type = 'domestic_league'")
    
    competitions = c.fetchall()
    
    for comp_id, comp_name in competitions:
        print(f"\n💰 Processing {comp_name}")
        print("-" * 40)
        
        # Get teams in this competition
        c.execute("""
            SELECT cts.team_id, cts.team_name, cts.squad_value_score
            FROM competition_team_strength cts
            WHERE cts.competition_id = %s AND cts.season = %s
            AND cts.team_name IS NOT NULL
        """, (comp_id, str(SEASON)))
        
        competition_teams = c.fetchall()
        
        if not competition_teams:
            print(f"   ⚠️ No teams found for {comp_name}")
            continue
        
        squad_data = {}
        
        # Analyze each team's enhanced squad value
        for i, (team_id, team_name, current_value) in enumerate(competition_teams, 1):
            print(f"[{i}/{len(competition_teams)}] Processing {team_name}...")
            
            # Get API ID from mapping
            api_team_id = TEAM_API_IDS.get(team_name)
            
            if not api_team_id:
                print(f"   ⚠️ No API ID for {team_name}, using current value: €{current_value}M")
                squad_data[team_id] = {
                    "team_name": team_name,
                    "enhanced_squad_value": current_value or FALLBACK_SCORE
                }
                continue

            try:
                # Fetch squad players
                players = fetch_squad_players(api_team_id, team_name)
                print(f"   📊 Found {len(players)} players")
                
                # Calculate enhanced squad value
                enhanced_value = calculate_enhanced_squad_value(players, team_name)
                
                # If enhanced calculation fails, fall back to current value
                if enhanced_value == FALLBACK_SCORE and current_value and current_value > 0:
                    enhanced_value = current_value
                
                squad_data[team_id] = {
                    "team_name": team_name,
                    "enhanced_squad_value": enhanced_value
                }
                
                print(f"   💰 Enhanced squad value: €{enhanced_value}M")
                if current_value:
                    diff = enhanced_value - current_value
                    print(f"   📈 Change from current: {diff:+.1f}M")
                
            except Exception as e:
                print(f"   ❌ Failed for {team_name}: {e}")
                squad_data[team_id] = {
                    "team_name": team_name,
                    "enhanced_squad_value": current_value or FALLBACK_SCORE
                }
        
        # Normalize scores within this competition
        print(f"\n📊 Normalizing {comp_name} values...")
        squad_data = normalize_competition_scores(squad_data)
        
        # Update database
        print(f"💾 Updating database for {comp_name}...")
        
        for team_id, data in squad_data.items():
            c.execute("""
                UPDATE competition_team_strength 
                SET squad_value_score = %s, squad_value_normalized = %s,
                    last_updated = %s
                WHERE team_id = %s AND competition_id = %s AND season = %s
            """, (
                data['enhanced_squad_value'], data['squad_value_normalized'],
                datetime.now(timezone.utc), team_id, comp_id, str(SEASON)
            ))
            
            print(f"   ✅ {data['team_name']}: €{data['enhanced_squad_value']}M → {data['squad_value_normalized']:.3f}")
        
        # Show competition summary
        values = [data['enhanced_squad_value'] for data in squad_data.values()]
        if values:
            print(f"\n📈 {comp_name} Summary:")
            print(f"   Value range: €{min(values):.1f}M - €{max(values):.1f}M")
            print(f"   Teams analyzed: {len(squad_data)}")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Enhanced squad value analysis complete!")

if __name__ == '__main__':
    # Process all domestic leagues
    update_enhanced_squad_values()