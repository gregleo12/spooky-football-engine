#!/usr/bin/env python3
"""
Create competition-aware database schema for multi-league prediction system
Supports Top 5 European leagues + European competitions
"""
import sqlite3
import uuid
from datetime import datetime, timezone

def create_competition_aware_schema():
    print("🏆 CREATING COMPETITION-AWARE SCHEMA")
    print("="*60)
    
    conn = sqlite3.connect("db/football_strength.db")
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON;")
    
    # 1. Create competitions reference table
    print("📋 Creating competitions table...")
    c.execute("""
        CREATE TABLE IF NOT EXISTS competitions (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            country TEXT,
            api_league_id INTEGER,
            type TEXT CHECK(type IN ('domestic_league', 'european_competition')),
            tier INTEGER, -- 1=top tier, 2=second tier, etc.
            season TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 2. Insert target competitions
    print("🌍 Inserting target competitions...")
    competitions = [
        # Top 5 European Leagues (2024-25 season)
        (str(uuid.uuid4()), "Premier League", "England", 39, "domestic_league", 1, "2024"),
        (str(uuid.uuid4()), "La Liga", "Spain", 140, "domestic_league", 1, "2024"), 
        (str(uuid.uuid4()), "Serie A", "Italy", 135, "domestic_league", 1, "2024"),
        (str(uuid.uuid4()), "Bundesliga", "Germany", 78, "domestic_league", 1, "2024"),
        (str(uuid.uuid4()), "Ligue 1", "France", 61, "domestic_league", 1, "2024"),
        
        # European Competitions (2024-25 season)
        (str(uuid.uuid4()), "Champions League", "Europe", 2, "european_competition", 1, "2024"),
        (str(uuid.uuid4()), "Europa League", "Europe", 3, "european_competition", 2, "2024"),
        (str(uuid.uuid4()), "Conference League", "Europe", 848, "european_competition", 3, "2024"),
    ]
    
    for comp in competitions:
        c.execute("""
            INSERT OR IGNORE INTO competitions 
            (id, name, country, api_league_id, type, tier, season) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, comp)
    
    # 3. Create new competition-specific team strength table
    print("💪 Creating competition_team_strength table...")
    c.execute("""
        CREATE TABLE IF NOT EXISTS competition_team_strength (
            id TEXT PRIMARY KEY,
            competition_id TEXT NOT NULL,
            team_id TEXT NOT NULL,
            team_name TEXT NOT NULL,
            
            -- Team Strength Metrics (normalized within competition)
            elo_score REAL,
            elo_normalized REAL,
            squad_value_score REAL,
            squad_value_normalized REAL, 
            form_score REAL,
            form_normalized REAL,
            squad_depth_score REAL,
            squad_depth_normalized REAL,
            
            -- Composite scores
            overall_strength REAL,
            
            -- Metadata
            last_updated DATETIME,
            season TEXT DEFAULT '2024',
            
            FOREIGN KEY (competition_id) REFERENCES competitions(id),
            FOREIGN KEY (team_id) REFERENCES teams(id),
            UNIQUE(competition_id, team_id, season)
        )
    """)
    
    # 4. Create competition team participation mapping
    print("🔗 Creating competition_teams table...")
    c.execute("""
        CREATE TABLE IF NOT EXISTS competition_teams (
            id TEXT PRIMARY KEY,
            competition_id TEXT NOT NULL,
            team_id TEXT NOT NULL,
            team_name TEXT NOT NULL,
            api_team_id INTEGER,
            season TEXT DEFAULT '2024',
            status TEXT DEFAULT 'active', -- active, relegated, promoted, eliminated
            added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (competition_id) REFERENCES competitions(id),
            FOREIGN KEY (team_id) REFERENCES teams(id),
            UNIQUE(competition_id, team_id, season)
        )
    """)
    
    # 5. Migrate current Premier League data
    print("📦 Migrating current Premier League data...")
    
    # Get Premier League competition ID
    c.execute("SELECT id FROM competitions WHERE name = 'Premier League'")
    pl_comp_id = c.fetchone()[0]
    
    # Insert current teams into competition_teams
    c.execute("SELECT id, name FROM teams")
    teams = c.fetchall()
    
    with open("agents/shared/team_api_ids.json") as f:
        import json
        team_api_ids = json.load(f)
    
    for team_id, team_name in teams:
        api_team_id = team_api_ids.get(team_name)
        c.execute("""
            INSERT OR IGNORE INTO competition_teams 
            (id, competition_id, team_id, team_name, api_team_id, season)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (str(uuid.uuid4()), pl_comp_id, team_id, team_name, api_team_id, "2024"))
    
    # Migrate existing team_strength_metrics to competition-specific table
    c.execute("""
        INSERT OR IGNORE INTO competition_team_strength 
        (id, competition_id, team_id, team_name, elo_score, squad_value_score, 
         form_score, squad_depth_score, last_updated, season)
        SELECT 
            ?, ?, team_id, team_name, 
            elo_score, squad_value_score, form_score, squad_depth_score,
            last_updated, '2024'
        FROM team_strength_metrics
    """, (str(uuid.uuid4()), pl_comp_id))
    
    conn.commit()
    
    # 6. Show created structure
    print(f"\n📊 COMPETITION STRUCTURE")
    print("="*40)
    
    c.execute("SELECT name, country, type, api_league_id FROM competitions ORDER BY type, tier")
    competitions = c.fetchall()
    
    for name, country, comp_type, api_id in competitions:
        print(f"   {name:<20} | {country:<10} | {comp_type:<20} | API:{api_id}")
    
    print(f"\n✅ Competition-aware schema created!")
    print(f"   • {len(competitions)} competitions configured")
    print(f"   • {len(teams)} teams migrated to Premier League")
    print(f"   • Ready for multi-competition strength analysis")
    
    conn.close()

if __name__ == "__main__":
    create_competition_aware_schema()