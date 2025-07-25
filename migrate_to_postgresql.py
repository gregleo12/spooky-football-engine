#!/usr/bin/env python3
"""
SQLite to PostgreSQL Migration Script
Migrates the football strength database to PostgreSQL for production deployment
"""
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import sys
from datetime import datetime

def get_postgresql_connection():
    """Get PostgreSQL connection from environment"""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not found")
        print("Please set DATABASE_URL to your PostgreSQL connection string")
        sys.exit(1)
    
    try:
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        sys.exit(1)

def get_sqlite_connection():
    """Get SQLite connection"""
    sqlite_path = "db/football_strength.db"
    if not os.path.exists(sqlite_path):
        print(f"❌ SQLite database not found at: {sqlite_path}")
        sys.exit(1)
    
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    return conn

def create_postgresql_schema(pg_conn):
    """Create PostgreSQL schema"""
    print("🏗️ Creating PostgreSQL schema...")
    
    with open('postgresql_schema.sql', 'r') as f:
        schema_sql = f.read()
    
    with pg_conn.cursor() as cursor:
        cursor.execute(schema_sql)
    
    pg_conn.commit()
    print("✅ PostgreSQL schema created")

def migrate_teams(sqlite_conn, pg_conn):
    """Migrate teams table"""
    print("👥 Migrating teams...")
    
    sqlite_cursor = sqlite_conn.cursor()
    sqlite_cursor.execute("SELECT * FROM teams")
    teams = sqlite_cursor.fetchall()
    
    with pg_conn.cursor() as pg_cursor:
        for team in teams:
            pg_cursor.execute("""
                INSERT INTO teams (id, name, country, founded, venue_name, venue_city, venue_capacity, logo_url, team_code)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (
                team['id'], team['name'], team.get('country'), team.get('founded'),
                team.get('venue_name'), team.get('venue_city'), team.get('venue_capacity'),
                team.get('logo_url'), team.get('team_code')
            ))
    
    pg_conn.commit()
    print(f"✅ Migrated {len(teams)} teams")

def migrate_competitions(sqlite_conn, pg_conn):
    """Migrate competitions table"""
    print("🏆 Migrating competitions...")
    
    sqlite_cursor = sqlite_conn.cursor()
    sqlite_cursor.execute("SELECT * FROM competitions")
    competitions = sqlite_cursor.fetchall()
    
    with pg_conn.cursor() as pg_cursor:
        for comp in competitions:
            pg_cursor.execute("""
                INSERT INTO competitions (id, name, country, api_league_id, type, tier, season, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (
                comp['id'], comp['name'], comp.get('country'), comp.get('api_league_id'),
                comp.get('type'), comp.get('tier'), comp.get('season'), comp.get('created_at')
            ))
    
    pg_conn.commit()
    print(f"✅ Migrated {len(competitions)} competitions")

def migrate_competition_team_strength(sqlite_conn, pg_conn):
    """Migrate competition_team_strength table"""
    print("💪 Migrating team strength data...")
    
    sqlite_cursor = sqlite_conn.cursor()
    sqlite_cursor.execute("SELECT * FROM competition_team_strength")
    strength_data = sqlite_cursor.fetchall()
    
    with pg_conn.cursor() as pg_cursor:
        for data in strength_data:
            pg_cursor.execute("""
                INSERT INTO competition_team_strength (
                    id, competition_id, team_id, team_name,
                    elo_score, elo_normalized, squad_value_score, squad_value_normalized,
                    form_score, form_normalized, squad_depth_score, squad_depth_normalized,
                    h2h_performance, h2h_normalized, scoring_patterns, scoring_normalized,
                    form_vs_opposition, form_opposition_normalized, competition_context, competition_normalized,
                    overall_strength, local_league_strength, european_strength,
                    last_updated, season
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) ON CONFLICT (id) DO NOTHING
            """, (
                data['id'], data['competition_id'], data['team_id'], data['team_name'],
                data.get('elo_score'), data.get('elo_normalized'), 
                data.get('squad_value_score'), data.get('squad_value_normalized'),
                data.get('form_score'), data.get('form_normalized'),
                data.get('squad_depth_score'), data.get('squad_depth_normalized'),
                data.get('h2h_performance'), data.get('h2h_normalized'),
                data.get('scoring_patterns'), data.get('scoring_normalized'),
                data.get('form_vs_opposition'), data.get('form_opposition_normalized'),
                data.get('competition_context'), data.get('competition_normalized'),
                data.get('overall_strength'), data.get('local_league_strength'), data.get('european_strength'),
                data.get('last_updated'), data.get('season')
            ))
    
    pg_conn.commit()
    print(f"✅ Migrated {len(strength_data)} team strength records")

def migrate_matches(sqlite_conn, pg_conn):
    """Migrate matches table"""
    print("⚽ Migrating matches...")
    
    sqlite_cursor = sqlite_conn.cursor()
    sqlite_cursor.execute("SELECT * FROM matches")
    matches = sqlite_cursor.fetchall()
    
    with pg_conn.cursor() as pg_cursor:
        for match in matches:
            pg_cursor.execute("""
                INSERT INTO matches (
                    id, home_team_id, away_team_id, home_team_name, away_team_name,
                    home_score, away_score, competition_id, competition_name,
                    match_date, season, status, api_fixture_id, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) ON CONFLICT (id) DO NOTHING
            """, (
                match['id'], match.get('home_team_id'), match.get('away_team_id'),
                match.get('home_team_name'), match.get('away_team_name'),
                match.get('home_score'), match.get('away_score'),
                match.get('competition_id'), match.get('competition_name'),
                match.get('match_date'), match.get('season'), match.get('status'),
                match.get('api_fixture_id'), match.get('created_at')
            ))
    
    pg_conn.commit()
    print(f"✅ Migrated {len(matches)} matches")

def verify_migration(pg_conn):
    """Verify migration completed successfully"""
    print("🔍 Verifying migration...")
    
    with pg_conn.cursor() as cursor:
        # Count records in each table
        tables = ['teams', 'competitions', 'competition_team_strength', 'matches']
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   {table}: {count} records")
    
    print("✅ Migration verification complete")

def main():
    """Main migration function"""
    print("🚀 STARTING SQLITE TO POSTGRESQL MIGRATION")
    print("=" * 60)
    
    # Get database connections
    print("📡 Connecting to databases...")
    sqlite_conn = get_sqlite_connection()
    pg_conn = get_postgresql_connection()
    
    try:
        # Create PostgreSQL schema
        create_postgresql_schema(pg_conn)
        
        # Migrate data
        migrate_teams(sqlite_conn, pg_conn)
        migrate_competitions(sqlite_conn, pg_conn)
        migrate_competition_team_strength(sqlite_conn, pg_conn)
        migrate_matches(sqlite_conn, pg_conn)
        
        # Verify migration
        verify_migration(pg_conn)
        
        print("\n🎉 MIGRATION COMPLETED SUCCESSFULLY!")
        print("Your Football Strength database is now running on PostgreSQL")
        
    except Exception as e:
        print(f"\n❌ MIGRATION FAILED: {e}")
        pg_conn.rollback()
        sys.exit(1)
    finally:
        sqlite_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    main()