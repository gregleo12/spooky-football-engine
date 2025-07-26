#!/usr/bin/env python3
"""
Railway Phase 3 Database Migration
Sets up all Phase 1-3 tables and data in PostgreSQL production database
"""
import os
import sys
from database_config import db_config

def create_phase3_tables():
    """Create all Phase 1-3 database tables in PostgreSQL"""
    
    print("🔧 Creating Phase 1-3 database tables...")
    
    # Phase 2 - Enhanced data tables
    phase2_tables = [
        """
        CREATE TABLE IF NOT EXISTS team_elo_data (
            id SERIAL PRIMARY KEY,
            team_name TEXT NOT NULL,
            team_id INTEGER,
            competition TEXT,
            standard_elo REAL,
            recent_form_elo REAL,
            elo_trend REAL,
            home_elo REAL,
            away_elo REAL,
            elo_confidence REAL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_source TEXT DEFAULT 'enhanced_elo_agent'
        )
        """,
        
        """
        CREATE TABLE IF NOT EXISTS team_form_data (
            id SERIAL PRIMARY KEY,
            team_name TEXT NOT NULL,
            team_id INTEGER,
            competition TEXT,
            raw_form_score REAL,
            opponent_adjusted_form REAL,
            home_form REAL,
            away_form REAL,
            recent_performance REAL,
            performance_rating REAL,
            form_trend REAL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_source TEXT DEFAULT 'advanced_form_agent'
        )
        """,
        
        """
        CREATE TABLE IF NOT EXISTS team_goals_data (
            id SERIAL PRIMARY KEY,
            team_name TEXT NOT NULL,
            team_id INTEGER,
            competition TEXT,
            goals_per_game REAL,
            goals_against_per_game REAL,
            opponent_adjusted_offensive REAL,
            opponent_adjusted_defensive REAL,
            home_goals_avg REAL,
            away_goals_avg REAL,
            scoring_consistency REAL,
            defensive_consistency REAL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_source TEXT DEFAULT 'goals_data_agent'
        )
        """,
        
        """
        CREATE TABLE IF NOT EXISTS team_squad_data (
            id SERIAL PRIMARY KEY,
            team_name TEXT NOT NULL,
            team_id INTEGER,
            competition TEXT,
            total_squad_value REAL,
            starting_xi_avg_value REAL,
            squad_depth_index REAL,
            age_profile REAL,
            international_players INTEGER,
            recent_transfers_in INTEGER,
            recent_transfers_out INTEGER,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_source TEXT DEFAULT 'enhanced_squad_value_agent'
        )
        """,
        
        """
        CREATE TABLE IF NOT EXISTS team_context_data (
            id SERIAL PRIMARY KEY,
            team_name TEXT NOT NULL,
            team_id INTEGER,
            competition TEXT,
            home_advantage_points REAL,
            home_advantage_goals REAL,
            home_advantage_defensive REAL,
            recent_injuries INTEGER,
            fixture_difficulty REAL,
            travel_factor REAL,
            rest_days INTEGER,
            manager_tenure INTEGER,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_source TEXT DEFAULT 'context_data_agent'
        )
        """
    ]
    
    # Phase 3 - Live events tables
    phase3_tables = [
        """
        CREATE TABLE IF NOT EXISTS live_matches (
            id TEXT PRIMARY KEY,
            api_fixture_id INTEGER UNIQUE,
            home_team_id INTEGER,
            away_team_id INTEGER,
            home_team_name TEXT,
            away_team_name TEXT,
            match_status TEXT,
            current_minute INTEGER,
            home_score INTEGER,
            away_score INTEGER,
            competition_id TEXT,
            kickoff_time TIMESTAMP,
            last_event_time TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        """
        CREATE TABLE IF NOT EXISTS live_events (
            id TEXT PRIMARY KEY,
            match_id TEXT NOT NULL,
            api_fixture_id INTEGER,
            event_minute INTEGER,
            event_type TEXT,
            team_id INTEGER,
            player_name TEXT,
            event_details TEXT,
            event_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed BOOLEAN DEFAULT FALSE,
            
            FOREIGN KEY (match_id) REFERENCES live_matches(id)
        )
        """,
        
        """
        CREATE TABLE IF NOT EXISTS live_predictions (
            id TEXT PRIMARY KEY,
            match_id TEXT NOT NULL,
            prediction_minute INTEGER,
            home_win_prob REAL,
            draw_prob REAL,
            away_win_prob REAL,
            over_2_5_prob REAL,
            expected_goals REAL,
            prediction_model TEXT,
            prediction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (match_id) REFERENCES live_matches(id)
        )
        """
    ]
    
    all_tables = phase2_tables + phase3_tables
    
    # Execute table creation
    for i, table_sql in enumerate(all_tables, 1):
        try:
            with db_config.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(table_sql)
                    conn.commit()
            print(f"✅ Created table {i}/{len(all_tables)}")
        except Exception as e:
            print(f"❌ Error creating table {i}: {e}")
            return False
    
    print(f"✅ All {len(all_tables)} Phase 1-3 tables created successfully!")
    return True

def verify_phase3_setup():
    """Verify Phase 1-3 tables exist in production database"""
    
    print("\n🔍 Verifying Phase 1-3 database setup...")
    
    required_tables = [
        'team_elo_data',
        'team_form_data', 
        'team_goals_data',
        'team_squad_data',
        'team_context_data',
        'live_matches',
        'live_events',
        'live_predictions'
    ]
    
    existing_tables = []
    
    for table in required_tables:
        try:
            query = """
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = %s
            """
            result = db_config.execute_query(query, (table,))
            if result:
                existing_tables.append(table)
                print(f"✅ {table}")
            else:
                print(f"❌ {table}")
        except Exception as e:
            print(f"⚠️ Error checking {table}: {e}")
    
    print(f"\n📊 Phase 1-3 Setup Status:")
    print(f"   Tables found: {len(existing_tables)}/{len(required_tables)}")
    print(f"   Database type: {db_config.get_db_type()}")
    
    if len(existing_tables) == len(required_tables):
        print("✅ Phase 1-3 database setup complete!")
        return True
    else:
        print("❌ Phase 1-3 database setup incomplete")
        return False

def main():
    """Main migration execution"""
    
    print("🚀 RAILWAY PHASE 3 DATABASE MIGRATION")
    print("="*60)
    
    # Check if we're in production
    if not db_config.use_postgresql:
        print("❌ This migration is for PostgreSQL production database only")
        print("   Set DATABASE_URL environment variable to run on PostgreSQL")
        return False
    
    print(f"🗄️ Connected to: {db_config.get_db_type()}")
    print(f"🌐 Database URL: {db_config.database_url[:50]}...")
    
    # Create Phase 1-3 tables
    if not create_phase3_tables():
        return False
    
    # Verify setup
    if not verify_phase3_setup():
        return False
    
    print("\n🎉 PHASE 1-3 DATABASE MIGRATION COMPLETE!")
    print("\n📋 Next Steps:")
    print("   1. Live events collection will start automatically")
    print("   2. Enhanced data collection agents will populate tables")
    print("   3. Phase 3 features are now available in production")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Migration successful - Phase 1-3 ready for production!")
    else:
        print("\n❌ Migration failed - check logs for details")
        sys.exit(1)