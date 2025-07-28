#!/usr/bin/env python3
"""
Fresh PostgreSQL Database Setup
Creates clean schema and populates with fresh API data
"""
import sys
import os
from datetime import datetime
from database_config import db_config

def create_database_schema():
    """Create complete database schema for PostgreSQL"""
    print("🔨 Creating Fresh PostgreSQL Schema")
    print("=" * 60)
    
    try:
        conn = db_config.get_connection()
        cursor = conn.cursor()
        
        print("📋 Creating competitions table...")
        cursor.execute("""
            DROP TABLE IF EXISTS competition_team_strength CASCADE;
            DROP TABLE IF EXISTS teams CASCADE;
            DROP TABLE IF EXISTS competitions CASCADE;
        """)
        
        # Create competitions table
        cursor.execute("""
            CREATE TABLE competitions (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                api_league_id INTEGER,
                api_season INTEGER DEFAULT 2024,
                country TEXT,
                confederation TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        print("👥 Creating teams table...")
        # Create teams table
        cursor.execute("""
            CREATE TABLE teams (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                country TEXT,
                api_team_id INTEGER,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        print("💪 Creating competition_team_strength table...")
        # Create main strength table with all parameters
        cursor.execute("""
            CREATE TABLE competition_team_strength (
                id TEXT PRIMARY KEY,
                competition_id TEXT NOT NULL,
                team_id TEXT NOT NULL,
                team_name TEXT NOT NULL,
                
                -- Core Team Strength Metrics (normalized within competition)
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
                last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                season TEXT DEFAULT '2024',
                
                -- Strength indicators
                local_league_strength REAL,
                european_strength REAL,
                
                -- Advanced metrics (all 11 parameters)
                home_advantage_score REAL,
                home_advantage_normalized REAL,
                fatigue_factor_score REAL,
                fatigue_factor_normalized REAL,
                key_player_availability_score REAL,
                key_player_availability_normalized REAL,
                motivation_factor_score REAL,
                motivation_factor_normalized REAL,
                tactical_matchup_score REAL,
                tactical_matchup_normalized REAL,
                offensive_rating REAL,
                defensive_rating REAL,
                goals_per_game REAL,
                goals_conceded_per_game REAL,
                
                -- Historical data
                h2h_performance_score REAL,
                h2h_performance_normalized REAL,
                
                -- Market data
                squad_value_trend REAL,
                transfer_activity_score REAL,
                
                -- Form metrics
                recent_ppg REAL,
                home_ppg REAL,
                away_ppg REAL,
                vs_top6_ppg REAL,
                vs_bottom6_ppg REAL,
                
                -- Scoring patterns
                scoring_first_percentage REAL,
                comeback_capability_score REAL,
                clean_sheet_percentage REAL,
                btts_percentage REAL,
                scoring_consistency REAL,
                
                -- Squad metrics
                avg_player_value REAL,
                squad_age_avg REAL,
                internationals_count INTEGER,
                injury_count INTEGER,
                
                -- Competition context
                league_position INTEGER,
                points_from_top INTEGER,
                games_played INTEGER,
                confederation TEXT,
                
                FOREIGN KEY (competition_id) REFERENCES competitions(id),
                FOREIGN KEY (team_id) REFERENCES teams(id)
            );
        """)
        
        print("📊 Creating indexes...")
        # Create indexes for performance
        cursor.execute("""
            CREATE INDEX idx_competition_team ON competition_team_strength(competition_id, team_id);
            CREATE INDEX idx_team_strength ON competition_team_strength(local_league_strength);
            CREATE INDEX idx_team_name ON competition_team_strength(team_name);
            CREATE INDEX idx_last_updated ON competition_team_strength(last_updated);
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n✅ Schema created successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Schema creation failed: {e}")
        return False

def seed_competitions():
    """Seed basic competition data"""
    print("\n🏆 Seeding Competition Data")
    print("=" * 60)
    
    competitions = [
        ('prem-league-id', 'Premier League', 'domestic_league', 39, 'England', 'UEFA'),
        ('la-liga-id', 'La Liga', 'domestic_league', 140, 'Spain', 'UEFA'),
        ('serie-a-id', 'Serie A', 'domestic_league', 135, 'Italy', 'UEFA'),
        ('bundesliga-id', 'Bundesliga', 'domestic_league', 78, 'Germany', 'UEFA'),
        ('ligue1-id', 'Ligue 1', 'domestic_league', 61, 'France', 'UEFA'),
        ('international-id', 'International', 'international', None, 'Global', 'FIFA'),
        ('champions-league-id', 'Champions League', 'european_competition', 2, 'Europe', 'UEFA'),
        ('europa-league-id', 'Europa League', 'european_competition', 3, 'Europe', 'UEFA')
    ]
    
    try:
        conn = db_config.get_connection()
        cursor = conn.cursor()
        
        for comp_id, name, comp_type, api_id, country, confederation in competitions:
            cursor.execute("""
                INSERT INTO competitions (id, name, type, api_league_id, country, confederation)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                type = EXCLUDED.type,
                api_league_id = EXCLUDED.api_league_id
            """, (comp_id, name, comp_type, api_id, country, confederation))
            print(f"  ✅ {name}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"\n✅ {len(competitions)} competitions seeded!")
        return True
        
    except Exception as e:
        print(f"\n❌ Competition seeding failed: {e}")
        return False

def main():
    """Main setup process"""
    print("🚀 Fresh PostgreSQL Database Setup")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Database: {db_config.get_db_info()}")
    print()
    
    # Create schema
    if not create_database_schema():
        sys.exit(1)
    
    # Seed competitions
    if not seed_competitions():
        sys.exit(1)
    
    print("\n🎉 Fresh PostgreSQL setup complete!")
    print("\nNext steps:")
    print("1. Run agents to populate with fresh API data")
    print("2. Verify data population")
    print("3. Proceed with Railway sync")

if __name__ == "__main__":
    main()