#!/usr/bin/env python3
"""
Competition-aware squad value agent with per-competition normalization
Scrapes squad values from Transfermarkt for teams within each league
"""
import sqlite3
import requests
from bs4 import BeautifulSoup
import time
import re
import sys
import os

# Add shared utilities to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from competition_normalizer import update_competition_metric, get_competition_teams

# Transfermarkt league mappings
TRANSFERMARKT_LEAGUES = {
    "Premier League": "premier-league",
    "La Liga": "primera-division", 
    "Serie A": "serie-a",
    "Bundesliga": "1-bundesliga",
    "Ligue 1": "ligue-1"
}

def scrape_transfermarkt_squad_values(league_url_name, league_name):
    """Scrape squad values from Transfermarkt for a specific league"""
    print(f"   🌐 Scraping Transfermarkt for {league_name}...")
    
    base_url = "https://www.transfermarkt.com"
    # Use the original working URLs that show team squad values
    league_ids = {
        "premier-league": "GB1",
        "primera-division": "ES1", 
        "serie-a": "IT1",
        "1-bundesliga": "L1",
        "ligue-1": "FR1"
    }
    league_id = league_ids.get(league_url_name, "GB1")
    league_url = f"{base_url}/{league_url_name}/startseite/wettbewerb/{league_id}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print(f"   🌐 Accessing: {league_url}")
        response = requests.get(league_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find table with team squad values
        table = soup.find('table', {'class': 'items'})
        if not table:
            print(f"   ⚠️ Could not find squad values table for {league_name}")
            return {}
        
        team_values = {}
        rows = table.find_all('tr')[1:]  # Skip header row
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 4:
                continue
                
            # Extract team name
            team_cell = cols[1]  # Usually the second column
            team_link = team_cell.find('a')
            if not team_link:
                continue
                
            team_name = team_link.get_text(strip=True)
            
            # Extract squad value (usually last column)
            value_cell = cols[-1]
            value_text = value_cell.get_text(strip=True)
            
            # Parse value (e.g., "€1.34bn", "€500.00m", "€45.30m")
            value_match = re.search(r'€([\d.]+)(bn|m|k)?', value_text.lower())
            if value_match:
                amount = float(value_match.group(1))
                unit = value_match.group(2) or ''
                
                if unit == 'bn':
                    value_millions = amount * 1000  # Convert billions to millions
                elif unit == 'k':
                    value_millions = amount / 1000  # Convert thousands to millions
                elif unit == 'm' or unit == '':
                    value_millions = amount  # Already in millions
                else:
                    value_millions = amount
                
                team_values[team_name] = value_millions
        
        print(f"   ✅ Found squad values for {len(team_values)} teams")
        if team_values:
            sample_teams = list(team_values.keys())[:3]
            print(f"   🔍 Sample teams: {', '.join(sample_teams)}")
        return team_values
        
    except Exception as e:
        print(f"   ❌ Error scraping {league_name}: {e}")
        return {}

def normalize_team_name(scraped_name, db_teams):
    """Match scraped team name to database team name"""
    # Direct match first
    if scraped_name in db_teams:
        return scraped_name
    
    # Comprehensive name mappings based on debug analysis
    name_mappings = {
        # Premier League - current season teams
        "AFC Bournemouth": "Bournemouth",
        "Arsenal FC": "Arsenal", 
        "Brentford FC": "Brentford",
        "Chelsea FC": "Chelsea",
        "Everton FC": "Everton",
        "Fulham FC": "Fulham",
        "Liverpool FC": "Liverpool",
        # Note: Some Transfermarkt teams are from wrong season (Burnley, Leeds, Sunderland)
        # Our DB has the correct 2024-25 teams: Ipswich, Leicester, Southampton
        
        # La Liga - exact mappings needed
        "Athletic Bilbao": "Athletic Club",
        "Atlético de Madrid": "Atletico Madrid", 
        "Celta de Vigo": "Celta Vigo",
        "Deportivo Alavés": "Alaves",
        "FC Barcelona": "Barcelona",
        "Getafe CF": "Getafe",
        "Girona FC": "Girona",
        "CA Osasuna": "Osasuna",
        "RCD Espanyol Barcelona": "Espanyol",
        "RCD Mallorca": "Mallorca",
        "Real Betis Balompié": "Real Betis",
        "Sevilla FC": "Sevilla",
        "Valencia CF": "Valencia",
        "Villarreal CF": "Villarreal",
        
        # Serie A - exact mappings needed  
        "ACF Fiorentina": "Fiorentina",
        "Atalanta BC": "Atalanta",
        "Bologna FC 1909": "Bologna",
        "Cagliari Calcio": "Cagliari",
        "Como 1907": "Como",
        "Genoa CFC": "Genoa",
        "Hellas Verona": "Verona",
        "Inter Milan": "Inter",
        "Juventus FC": "Juventus",
        "Parma Calcio 1913": "Parma",
        "SS Lazio": "Lazio",
        "SSC Napoli": "Napoli",
        "Torino FC": "Torino",
        "US Lecce": "Lecce",
        "Udinese Calcio": "Udinese",
        
        # Bundesliga - exact mappings needed
        "1.FC Heidenheim 1846": "1. FC Heidenheim",
        "1.FC Union Berlin": "Union Berlin",
        "1.FSV Mainz 05": "FSV Mainz 05",
        "Bayer 04 Leverkusen": "Bayer Leverkusen",
        "Bayern Munich": "Bayern München",
        "SV Werder Bremen": "Werder Bremen",
        "TSG 1899 Hoffenheim": "1899 Hoffenheim",
        
        # Ligue 1 - exact mappings needed
        "AJ Auxerre": "Auxerre",
        "AS Monaco": "Monaco",
        "Angers SCO": "Angers", 
        "FC Nantes": "Nantes",
        "FC Toulouse": "Toulouse",
        "LOSC Lille": "Lille",
        "Le Havre AC": "Le Havre",
        "OGC Nice": "Nice",
        "Olympique Lyon": "Lyon",
        "Olympique Marseille": "Marseille",
        "Paris Saint-Germain": "Paris Saint Germain",
        "RC Lens": "Lens",
        "RC Strasbourg Alsace": "Strasbourg",
        "Stade Rennais FC": "Rennes",
        "Stade Reims": "Reims",
        "Montpellier HSC": "Montpellier",
        
        # Additional Serie A mappings
        "FC Empoli": "Empoli",
        "AC Monza": "Monza",
        "Venezia FC": "Venezia"
    }
    
    # Check mappings
    if scraped_name in name_mappings:
        mapped_name = name_mappings[scraped_name]
        if mapped_name in db_teams:
            return mapped_name
    
    # Enhanced fuzzy matching with better heuristics
    scraped_lower = scraped_name.lower()
    scraped_words = set(scraped_lower.split())
    
    best_match = None
    best_score = 0
    
    for db_team in db_teams:
        db_lower = db_team.lower()
        db_words = set(db_lower.split())
        
        # Check for partial contains (existing logic)
        if scraped_lower in db_lower or db_lower in scraped_lower:
            return db_team
        
        # Check for word overlap
        common_words = scraped_words & db_words
        if common_words:
            # Score based on number of common words and their importance
            score = len(common_words)
            
            # Boost score for important words
            important_words = {'fc', 'united', 'city', 'real', 'athletic', 'club'}
            if any(word in important_words for word in common_words):
                score += 2
            
            if score > best_score:
                best_match = db_team
                best_score = score
    
    # Return best match if score is high enough
    if best_score >= 1:
        return best_match
    
    return None

def update_competition_squad_values(competition_name=None):
    """Update squad values for specified competition or all competitions"""
    print("💰 COMPETITION-AWARE SQUAD VALUE ANALYSIS")
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
        if comp_name not in TRANSFERMARKT_LEAGUES:
            print(f"\n⚠️ No Transfermarkt mapping for {comp_name}")
            continue
            
        print(f"\n🏆 Processing {comp_name}")
        print("-" * 40)
        
        # Get teams in this competition
        competition_teams = get_competition_teams(comp_id, conn)
        
        if not competition_teams:
            print(f"   ⚠️ No teams found for {comp_name}")
            continue
        
        # Create database team mapping
        db_teams = {team_name: team_id for team_id, team_name, api_team_id in competition_teams}
        
        # Scrape squad values from Transfermarkt
        league_url_name = TRANSFERMARKT_LEAGUES[comp_name]
        scraped_values = scrape_transfermarkt_squad_values(league_url_name, comp_name)
        
        if not scraped_values:
            continue
        
        # Match scraped data to database teams
        team_scores = {}
        matched_teams = 0
        
        for scraped_name, value_millions in scraped_values.items():
            db_team_name = normalize_team_name(scraped_name, db_teams.keys())
            
            if db_team_name:
                team_id = db_teams[db_team_name]
                team_scores[team_id] = value_millions
                matched_teams += 1
                print(f"   ✅ {db_team_name}: €{value_millions:.1f}M")
            else:
                print(f"   ⚠️ Could not match: {scraped_name}")
        
        print(f"   📊 Matched {matched_teams}/{len(scraped_values)} teams")
        
        # Update database with competition-aware normalization
        if team_scores:
            update_competition_metric(
                comp_id, "squad_value_score", "squad_value_normalized", team_scores, conn
            )
            
            # Show value range
            values = list(team_scores.values())
            print(f"   💰 Value range: €{min(values):.1f}M - €{max(values):.1f}M")
        
        # Rate limiting for Transfermarkt
        time.sleep(2)
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Competition-aware squad value analysis complete!")

if __name__ == "__main__":
    # Process all domestic leagues
    update_competition_squad_values()