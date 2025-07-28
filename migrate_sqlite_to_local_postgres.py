#!/usr/bin/env python3
"""
Migration Script: SQLite to Local PostgreSQL
Preserves all current team data including Arsenal's 93.4 strength
"""
import sqlite3
import psycopg2
from datetime import datetime
import sys

# Local PostgreSQL configuration (matches database_config.py)
LOCAL_POSTGRES = {
    'host': 'localhost',
    'port': '5432',
    'database': 'football_strength',
    'user': 'football_user',
    'password': 'local_dev_password'
}

SQLITE_PATH = "db/football_strength.db"

def create_postgres_schema(pg_conn):
    """Create all necessary tables in PostgreSQL"""
    print("🔨 Creating PostgreSQL schema...")
    
    with pg_conn.cursor() as cursor:
        # Drop existing tables if they exist (clean slate)
        cursor.execute("""
            DROP TABLE IF EXISTS competition_team_strength CASCADE;
            DROP TABLE IF EXISTS teams CASCADE;
            DROP TABLE IF EXISTS competitions CASCADE;
        """)
        
        # Create tables with proper schema
        cursor.execute("""
            CREATE TABLE competitions (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                api_league_id INTEGER,
                api_season INTEGER,
                country TEXT,
                confederation TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE teams (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                country TEXT,
                api_team_id INTEGER,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE competition_team_strength (
                id TEXT PRIMARY KEY,
                competition_id TEXT NOT NULL,
                team_id TEXT NOT NULL,
                team_name TEXT NOT NULL,
                
                -- Team Strength Metrics
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
                last_updated TIMESTAMP WITH TIME ZONE,
                season TEXT,
                
                -- Strength indicators
                local_league_strength REAL,
                european_strength REAL,
                
                -- Advanced metrics (Phase 1)
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
                
                -- Historical data (Phase 2)
                h2h_performance_score REAL,
                h2h_performance_normalized REAL,
                
                -- Market data
                squad_value_trend REAL,
                transfer_activity_score REAL,
                
                -- Live factors
                weather_impact_score REAL,
                referee_factor_score REAL,
                
                -- Recent metrics
                recent_ppg REAL,
                home_ppg REAL,
                away_ppg REAL,
                vs_top6_ppg REAL,
                vs_bottom6_ppg REAL,
                
                -- Goal patterns
                goals_scored_0_15 INTEGER,
                goals_scored_16_30 INTEGER,
                goals_scored_31_45 INTEGER,
                goals_scored_46_60 INTEGER,
                goals_scored_61_75 INTEGER,
                goals_scored_76_90 INTEGER,
                goals_conceded_0_15 INTEGER,
                goals_conceded_16_30 INTEGER,
                goals_conceded_31_45 INTEGER,
                goals_conceded_46_60 INTEGER,
                goals_conceded_61_75 INTEGER,
                goals_conceded_76_90 INTEGER,
                
                -- Scoring patterns  
                scoring_first_percentage REAL,
                comeback_capability_score REAL,
                clean_sheet_percentage REAL,
                btts_percentage REAL,
                scoring_consistency REAL,
                
                -- European performance
                european_coefficient REAL,
                european_matches_played INTEGER,
                european_wins INTEGER,
                european_goals_scored INTEGER,
                european_goals_conceded INTEGER,
                
                -- Squad metrics
                avg_player_value REAL,
                squad_age_avg REAL,
                internationals_count INTEGER,
                injury_count INTEGER,
                
                -- Weighted scores
                weighted_overall_strength REAL,
                confidence_score REAL,
                volatility_score REAL,
                momentum_score REAL,
                pressure_handling_score REAL,
                
                -- Market behavior
                odds_accuracy_score REAL,
                market_overperformance REAL,
                
                -- Competition context
                league_position INTEGER,
                points_from_top INTEGER,
                games_played INTEGER,
                confederation TEXT,
                
                FOREIGN KEY (competition_id) REFERENCES competitions(id),
                FOREIGN KEY (team_id) REFERENCES teams(id)
            );
            
            -- Create indexes for performance
            CREATE INDEX idx_competition_team ON competition_team_strength(competition_id, team_id);
            CREATE INDEX idx_team_strength ON competition_team_strength(local_league_strength);
            CREATE INDEX idx_team_name ON competition_team_strength(team_name);
        """)
        
        pg_conn.commit()
        print("✅ Schema created successfully")

def migrate_data(sqlite_conn, pg_conn):
    """Migrate all data from SQLite to PostgreSQL"""
    print("\n📦 Starting data migration...")
    
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    # 1. Migrate competitions
    print("  → Migrating competitions...")
    sqlite_cursor.execute("SELECT * FROM competitions")
    competitions = sqlite_cursor.fetchall()
    
    for comp in competitions:
        pg_cursor.execute("""
            INSERT INTO competitions (id, name, type, api_league_id, api_season, country, confederation, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, comp)
    
    print(f"    ✓ Migrated {len(competitions)} competitions")
    
    # 2. Migrate teams
    print("  → Migrating teams...")
    sqlite_cursor.execute("SELECT * FROM teams")
    teams = sqlite_cursor.fetchall()
    
    for team in teams:
        pg_cursor.execute("""
            INSERT INTO teams (id, name, country, api_team_id, created_at)
            VALUES (%s, %s, %s, %s, %s)
        """, team)
    
    print(f"    ✓ Migrated {len(teams)} teams")
    
    # 3. Migrate competition_team_strength (the big one)
    print("  → Migrating team strength data...")
    sqlite_cursor.execute("SELECT * FROM competition_team_strength")
    
    # Get column names from SQLite
    column_names = [description[0] for description in sqlite_cursor.description]
    
    rows = sqlite_cursor.fetchall()
    
    # Prepare insert query with all columns
    placeholders = ', '.join(['%s'] * len(column_names))
    columns = ', '.join(column_names)
    insert_query = f"INSERT INTO competition_team_strength ({columns}) VALUES ({placeholders})"
    
    # Insert all rows
    for row in rows:
        pg_cursor.execute(insert_query, row)
    
    print(f"    ✓ Migrated {len(rows)} team strength records")
    
    pg_conn.commit()
    print("\n✅ Migration completed successfully!")

def verify_migration(sqlite_conn, pg_conn):
    """Verify data integrity after migration"""
    print("\n🔍 Verifying migration...")
    
    # Check Arsenal's data specifically
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    # SQLite Arsenal data
    sqlite_cursor.execute("""
        SELECT team_name, local_league_strength, european_strength, 
               elo_score, squad_value_score, form_score, squad_depth_score
        FROM competition_team_strength 
        WHERE team_name = 'Arsenal'
    """)
    sqlite_arsenal = sqlite_cursor.fetchone()
    
    # PostgreSQL Arsenal data
    pg_cursor.execute("""
        SELECT team_name, local_league_strength, european_strength,
               elo_score, squad_value_score, form_score, squad_depth_score
        FROM competition_team_strength 
        WHERE team_name = 'Arsenal'
    """)
    pg_arsenal = pg_cursor.fetchone()
    
    if sqlite_arsenal and pg_arsenal:
        print(f"\n  Arsenal verification:")
        print(f"    SQLite  - Strength: {sqlite_arsenal[1]:.1f}, ELO: {sqlite_arsenal[3]:.1f}, Squad Value: €{sqlite_arsenal[4]:.0f}M")
        print(f"    PostgreSQL - Strength: {pg_arsenal[1]:.1f}, ELO: {pg_arsenal[3]:.1f}, Squad Value: €{pg_arsenal[4]:.0f}M")
        
        if abs(sqlite_arsenal[1] - pg_arsenal[1]) < 0.1:
            print("    ✅ Data matches perfectly!")
        else:
            print("    ❌ Data mismatch detected!")
    
    # Check record counts
    sqlite_cursor.execute("SELECT COUNT(*) FROM competition_team_strength")
    sqlite_count = sqlite_cursor.fetchone()[0]
    
    pg_cursor.execute("SELECT COUNT(*) FROM competition_team_strength")
    pg_count = pg_cursor.fetchone()[0]
    
    print(f"\n  Record counts:")
    print(f"    SQLite: {sqlite_count} records")
    print(f"    PostgreSQL: {pg_count} records")
    
    if sqlite_count == pg_count:
        print("    ✅ Record counts match!")
    else:
        print("    ❌ Record count mismatch!")

def main():
    """Main migration process"""
    print("🚀 SQLite to Local PostgreSQL Migration")
    print("="*50)
    
    try:
        # Connect to SQLite
        print(f"\n📂 Connecting to SQLite: {SQLITE_PATH}")
        sqlite_conn = sqlite3.connect(SQLITE_PATH)
        
        # Connect to Local PostgreSQL
        print(f"🐘 Connecting to Local PostgreSQL...")
        pg_conn = psycopg2.connect(**LOCAL_POSTGRES)
        
        # Create schema
        create_postgres_schema(pg_conn)
        
        # Migrate data
        migrate_data(sqlite_conn, pg_conn)
        
        # Verify migration
        verify_migration(sqlite_conn, pg_conn)
        
        # Close connections
        sqlite_conn.close()
        pg_conn.close()
        
        print("\n🎉 Migration completed successfully!")
        print("\nNext steps:")
        print("1. Test agents with local PostgreSQL")
        print("2. Remove SQLite database file")
        print("3. Test with Railway PostgreSQL (set DATABASE_URL)")
        
    except sqlite3.Error as e:
        print(f"\n❌ SQLite error: {e}")
        print("Make sure SQLite database exists at: db/football_strength.db")
        sys.exit(1)
        
    except psycopg2.Error as e:
        print(f"\n❌ PostgreSQL error: {e}")
        print("\nMake sure local PostgreSQL is running:")
        print("  docker compose -f docker-compose.local.yml up -d")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()