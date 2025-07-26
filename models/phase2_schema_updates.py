#!/usr/bin/env python3
"""
Phase 2 Database Schema Updates
Extends the competition-aware schema to support the new 11-parameter system
from Phase 1 data collection agents
"""
import sqlite3
import uuid
from datetime import datetime, timezone
import os
import sys

def create_phase2_schema_updates():
    """Create database schema updates for Phase 2 11-parameter system"""
    print("🚀 PHASE 2: DATABASE SCHEMA UPDATES")
    print("="*60)
    
    conn = sqlite3.connect("db/football_strength.db")
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON;")
    
    # 1. Update competition_team_strength table with new parameters
    print("📊 Adding new parameter columns to competition_team_strength...")
    
    new_columns = [
        # Enhanced ELO parameters
        ("standard_elo", "REAL"),
        ("recent_form_elo", "REAL"),
        ("elo_trend", "TEXT"),
        
        # Advanced Form parameters  
        ("raw_form_score", "REAL"),
        ("opponent_adjusted_form", "REAL"),
        ("form_trend", "TEXT"),
        ("form_consistency", "REAL"),
        
        # Goals Data parameters
        ("goals_per_game", "REAL"),
        ("opponent_adjusted_offensive", "REAL"),
        ("goals_conceded_per_game", "REAL"),
        ("opponent_adjusted_defensive", "REAL"),
        ("clean_sheet_percentage", "REAL"),
        ("over_2_5_percentage", "REAL"),
        ("over_1_5_percentage", "REAL"),
        ("btts_percentage", "REAL"),
        
        # Enhanced Squad Value parameters
        ("total_squad_value", "REAL"),
        ("squad_depth_index", "REAL"),
        ("starting_xi_avg_value", "REAL"),
        ("second_xi_avg_value", "REAL"),
        ("position_balance_score", "REAL"),
        
        # Context Data parameters
        ("overall_home_advantage", "REAL"),
        ("home_advantage_points", "REAL"),
        ("home_advantage_goals", "REAL"),
        ("home_advantage_defensive", "REAL"),
        ("motivation_factor", "REAL"),
        ("current_position", "INTEGER"),
        ("title_race_motivation", "REAL"),
        ("relegation_motivation", "REAL"),
        ("european_motivation", "REAL"),
        ("fixture_density", "REAL"),
        ("days_since_last_match", "INTEGER"),
        
        # Data quality metadata
        ("data_quality_score", "REAL"),
        ("collection_confidence", "REAL"),
        ("data_sources", "TEXT"),  # JSON string of data sources
        ("validation_status", "TEXT")  # passed, failed, pending
    ]
    
    # Add columns that don't exist
    for column_name, column_type in new_columns:
        try:
            c.execute(f"ALTER TABLE competition_team_strength ADD COLUMN {column_name} {column_type}")
            print(f"  ✅ Added column: {column_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"  ⏭️  Column already exists: {column_name}")
            else:
                print(f"  ❌ Error adding {column_name}: {e}")
    
    # 2. Create new dedicated tables for complex data structures
    print("\n🗄️ Creating dedicated parameter tables...")
    
    # Table for detailed ELO data
    c.execute("""
        CREATE TABLE IF NOT EXISTS team_elo_data (
            id TEXT PRIMARY KEY,
            team_id TEXT NOT NULL,
            competition_id TEXT NOT NULL,
            season TEXT DEFAULT '2024',
            
            -- ELO Components
            standard_elo REAL,
            recent_form_elo REAL,
            elo_trend TEXT,
            elo_change_last_5 REAL,
            elo_volatility REAL,
            
            -- Match-based metrics
            matches_analyzed INTEGER,
            recent_matches_weighted INTEGER,
            
            -- Metadata
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
            data_confidence REAL DEFAULT 1.0,
            
            FOREIGN KEY (team_id) REFERENCES teams(id),
            FOREIGN KEY (competition_id) REFERENCES competitions(id),
            UNIQUE(team_id, competition_id, season)
        )
    """)
    
    # Table for detailed form analysis
    c.execute("""
        CREATE TABLE IF NOT EXISTS team_form_data (
            id TEXT PRIMARY KEY,
            team_id TEXT NOT NULL,
            competition_id TEXT NOT NULL,
            season TEXT DEFAULT '2024',
            
            -- Form Components
            raw_form_score REAL,
            opponent_adjusted_form REAL,
            form_trend TEXT,
            form_consistency REAL,
            performance_variance REAL,
            
            -- Match details
            last_5_results TEXT,  -- JSON array of recent results
            matches_analyzed INTEGER,
            avg_opponent_strength REAL,
            
            -- Metadata
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
            data_confidence REAL DEFAULT 1.0,
            
            FOREIGN KEY (team_id) REFERENCES teams(id),
            FOREIGN KEY (competition_id) REFERENCES competitions(id),
            UNIQUE(team_id, competition_id, season)
        )
    """)
    
    # Table for goals analysis
    c.execute("""
        CREATE TABLE IF NOT EXISTS team_goals_data (
            id TEXT PRIMARY KEY,
            team_id TEXT NOT NULL,
            competition_id TEXT NOT NULL,
            season TEXT DEFAULT '2024',
            
            -- Offensive metrics
            goals_per_game REAL,
            opponent_adjusted_offensive REAL,
            shots_per_game REAL,
            shots_on_target_percentage REAL,
            
            -- Defensive metrics
            goals_conceded_per_game REAL,
            opponent_adjusted_defensive REAL,
            clean_sheet_percentage REAL,
            saves_per_game REAL,
            
            -- Market indicators
            over_2_5_percentage REAL,
            over_1_5_percentage REAL,
            btts_percentage REAL,
            under_2_5_percentage REAL,
            
            -- Match context
            home_goals_per_game REAL,
            away_goals_per_game REAL,
            home_goals_conceded_per_game REAL,
            away_goals_conceded_per_game REAL,
            
            -- Metadata
            matches_analyzed INTEGER,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
            data_confidence REAL DEFAULT 1.0,
            
            FOREIGN KEY (team_id) REFERENCES teams(id),
            FOREIGN KEY (competition_id) REFERENCES competitions(id),
            UNIQUE(team_id, competition_id, season)
        )
    """)
    
    # Table for squad analysis
    c.execute("""
        CREATE TABLE IF NOT EXISTS team_squad_data (
            id TEXT PRIMARY KEY,
            team_id TEXT NOT NULL,
            competition_id TEXT NOT NULL,
            season TEXT DEFAULT '2024',
            
            -- Squad value metrics
            total_squad_value REAL,
            squad_depth_index REAL,
            starting_xi_avg_value REAL,
            second_xi_avg_value REAL,
            
            -- Squad composition
            total_players INTEGER,
            goalkeepers INTEGER,
            defenders INTEGER,
            midfielders INTEGER,
            forwards INTEGER,
            position_balance_score REAL,
            
            -- Squad characteristics
            average_age REAL,
            average_height REAL,
            international_players INTEGER,
            
            -- Market data
            most_valuable_player_value REAL,
            market_value_currency TEXT DEFAULT 'EUR',
            last_transfermarkt_update DATETIME,
            
            -- Metadata
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
            data_confidence REAL DEFAULT 1.0,
            data_source TEXT DEFAULT 'transfermarkt',
            
            FOREIGN KEY (team_id) REFERENCES teams(id),
            FOREIGN KEY (competition_id) REFERENCES competitions(id),
            UNIQUE(team_id, competition_id, season)
        )
    """)
    
    # Table for context analysis
    c.execute("""
        CREATE TABLE IF NOT EXISTS team_context_data (
            id TEXT PRIMARY KEY,
            team_id TEXT NOT NULL,
            competition_id TEXT NOT NULL,
            season TEXT DEFAULT '2024',
            
            -- Home advantage metrics
            overall_home_advantage REAL,
            home_advantage_points REAL,
            home_advantage_goals REAL,
            home_advantage_defensive REAL,
            home_win_rate REAL,
            away_win_rate REAL,
            
            -- League position and motivation
            current_position INTEGER,
            motivation_factor REAL,
            title_race_motivation REAL,
            relegation_motivation REAL,
            european_motivation REAL,
            points_from_target REAL,
            
            -- Fixture congestion
            fixture_density REAL,
            days_since_last_match INTEGER,
            matches_last_30_days INTEGER,
            upcoming_fixture_difficulty REAL,
            
            -- Venue performance
            home_matches_played INTEGER,
            away_matches_played INTEGER,
            home_points_per_game REAL,
            away_points_per_game REAL,
            
            -- Metadata
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
            data_confidence REAL DEFAULT 1.0,
            
            FOREIGN KEY (team_id) REFERENCES teams(id),
            FOREIGN KEY (competition_id) REFERENCES competitions(id),
            UNIQUE(team_id, competition_id, season)
        )
    """)
    
    # 3. Create validation and audit tables
    print("\n🔍 Creating validation and audit tables...")
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS data_collection_audit (
            id TEXT PRIMARY KEY,
            team_id TEXT NOT NULL,
            competition_id TEXT NOT NULL,
            agent_name TEXT NOT NULL,
            collection_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            execution_time_seconds REAL,
            success BOOLEAN,
            error_message TEXT,
            data_quality_score REAL,
            confidence_level REAL,
            records_collected INTEGER,
            
            FOREIGN KEY (team_id) REFERENCES teams(id),
            FOREIGN KEY (competition_id) REFERENCES competitions(id)
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS parameter_validation_log (
            id TEXT PRIMARY KEY,
            team_id TEXT NOT NULL,
            competition_id TEXT NOT NULL,
            parameter_name TEXT NOT NULL,
            parameter_value REAL,
            validation_status TEXT,  -- passed, failed, warning
            validation_message TEXT,
            expected_range_min REAL,
            expected_range_max REAL,
            validation_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (team_id) REFERENCES teams(id),
            FOREIGN KEY (competition_id) REFERENCES competitions(id)
        )
    """)
    
    # 4. Create indexes for performance
    print("\n⚡ Creating performance indexes...")
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_competition_team_strength_team ON competition_team_strength(team_id)",
        "CREATE INDEX IF NOT EXISTS idx_competition_team_strength_comp ON competition_team_strength(competition_id)",
        "CREATE INDEX IF NOT EXISTS idx_team_elo_data_team ON team_elo_data(team_id)",
        "CREATE INDEX IF NOT EXISTS idx_team_form_data_team ON team_form_data(team_id)",
        "CREATE INDEX IF NOT EXISTS idx_team_goals_data_team ON team_goals_data(team_id)",
        "CREATE INDEX IF NOT EXISTS idx_team_squad_data_team ON team_squad_data(team_id)",
        "CREATE INDEX IF NOT EXISTS idx_team_context_data_team ON team_context_data(team_id)",
        "CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON data_collection_audit(collection_timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_validation_timestamp ON parameter_validation_log(validation_timestamp)"
    ]
    
    for index_sql in indexes:
        c.execute(index_sql)
        index_name = index_sql.split("idx_")[1].split(" ")[0]
        print(f"  ✅ Created index: idx_{index_name}")
    
    # 5. Create views for easy data access
    print("\n👁️ Creating convenience views...")
    
    c.execute("""
        CREATE VIEW IF NOT EXISTS team_complete_profile AS
        SELECT 
            cts.team_name,
            cts.competition_id,
            comp.name as competition_name,
            
            -- Enhanced ELO
            ted.standard_elo,
            ted.recent_form_elo,
            ted.elo_trend,
            
            -- Advanced Form
            tfd.raw_form_score,
            tfd.opponent_adjusted_form,
            tfd.form_trend,
            tfd.form_consistency,
            
            -- Goals Analysis
            tgd.goals_per_game,
            tgd.goals_conceded_per_game,
            tgd.clean_sheet_percentage,
            tgd.over_2_5_percentage,
            
            -- Squad Analysis
            tsd.total_squad_value,
            tsd.squad_depth_index,
            tsd.starting_xi_avg_value,
            
            -- Context Analysis
            tcd.overall_home_advantage,
            tcd.motivation_factor,
            tcd.current_position,
            tcd.fixture_density,
            
            -- Overall strength
            cts.overall_strength,
            cts.last_updated
            
        FROM competition_team_strength cts
        LEFT JOIN competitions comp ON cts.competition_id = comp.id
        LEFT JOIN team_elo_data ted ON cts.team_id = ted.team_id AND cts.competition_id = ted.competition_id
        LEFT JOIN team_form_data tfd ON cts.team_id = tfd.team_id AND cts.competition_id = tfd.competition_id
        LEFT JOIN team_goals_data tgd ON cts.team_id = tgd.team_id AND cts.competition_id = tgd.competition_id
        LEFT JOIN team_squad_data tsd ON cts.team_id = tsd.team_id AND cts.competition_id = tsd.competition_id
        LEFT JOIN team_context_data tcd ON cts.team_id = tcd.team_id AND cts.competition_id = tcd.competition_id
    """)
    
    conn.commit()
    
    # 6. Show schema summary
    print(f"\n📋 PHASE 2 SCHEMA SUMMARY")
    print("="*50)
    
    # Count tables
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = c.fetchall()
    print(f"📊 Total tables: {len(tables)}")
    
    for table in tables:
        table_name = table[0]
        c.execute(f"PRAGMA table_info({table_name})")
        columns = c.fetchall()
        print(f"   {table_name}: {len(columns)} columns")
    
    # Count indexes  
    c.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
    indexes = c.fetchall()
    print(f"⚡ Performance indexes: {len(indexes)}")
    
    # Count views
    c.execute("SELECT name FROM sqlite_master WHERE type='view'")
    views = c.fetchall()
    print(f"👁️  Convenience views: {len(views)}")
    
    print(f"\n✅ Phase 2 database schema updates completed!")
    print(f"   • Enhanced competition_team_strength with 39 new parameters")
    print(f"   • 5 dedicated parameter tables for detailed analysis")
    print(f"   • 2 audit tables for data quality tracking")
    print(f"   • 9 performance indexes for fast queries")
    print(f"   • 1 complete profile view for easy access")
    print(f"   • Ready for Phase 1 data collection agents integration")
    
    conn.close()

if __name__ == "__main__":
    create_phase2_schema_updates()