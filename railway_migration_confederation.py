#!/usr/bin/env python3
"""
Railway PostgreSQL Migration: Add Confederation Support
Adds confederation column and data for international teams
"""
import os
from database_config import db_config

def add_confederations_to_postgresql():
    """Add confederation column and data to Railway PostgreSQL"""
    
    # Confederation mappings
    confederations = {
        # UEFA (Europe)
        'Germany': 'UEFA', 'France': 'UEFA', 'England': 'UEFA', 'Spain': 'UEFA',
        'Italy': 'UEFA', 'Portugal': 'UEFA', 'Netherlands': 'UEFA', 'Belgium': 'UEFA',
        'Croatia': 'UEFA', 'Denmark': 'UEFA', 'Switzerland': 'UEFA', 'Poland': 'UEFA',
        'Wales': 'UEFA', 'Serbia': 'UEFA', 'Austria': 'UEFA', 'Ukraine': 'UEFA',
        'Czech Republic': 'UEFA', 'Turkey': 'UEFA', 'Sweden': 'UEFA', 'Russia': 'UEFA',
        'Scotland': 'UEFA',
        
        # CONMEBOL (South America)
        'Brazil': 'CONMEBOL', 'Argentina': 'CONMEBOL', 'Uruguay': 'CONMEBOL', 
        'Colombia': 'CONMEBOL', 'Chile': 'CONMEBOL', 'Peru': 'CONMEBOL',
        'Ecuador': 'CONMEBOL', 'Paraguay': 'CONMEBOL', 'Bolivia': 'CONMEBOL', 
        'Venezuela': 'CONMEBOL',
        
        # CONCACAF (North/Central America, Caribbean)
        'Mexico': 'CONCACAF', 'USA': 'CONCACAF', 'Canada': 'CONCACAF',
        'Costa Rica': 'CONCACAF', 'Jamaica': 'CONCACAF', 'Panama': 'CONCACAF',
        
        # CAF (Africa)
        'Morocco': 'CAF', 'Senegal': 'CAF', 'Tunisia': 'CAF', 'Algeria': 'CAF',
        'Nigeria': 'CAF', 'Egypt': 'CAF', 'Ghana': 'CAF', 'Cameroon': 'CAF',
        'South Africa': 'CAF',
        
        # AFC (Asia)
        'Japan': 'AFC', 'South Korea': 'AFC', 'Iran': 'AFC', 'Saudi Arabia': 'AFC',
        'Australia': 'AFC', 'Qatar': 'AFC', 'Iraq': 'AFC', 'China': 'AFC',
        'Thailand': 'AFC', 'India': 'AFC'
    }
    
    conn = db_config.get_connection()
    c = conn.cursor()
    
    try:
        # Check if confederation column exists
        c.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'competition_team_strength' 
            AND column_name = 'confederation'
        """)
        
        column_exists = c.fetchone() is not None
        
        if not column_exists:
            print("Adding confederation column to PostgreSQL...")
            c.execute("ALTER TABLE competition_team_strength ADD COLUMN confederation TEXT")
            print("✅ Confederation column added")
        else:
            print("✅ Confederation column already exists")
        
        # Get international teams
        c.execute("""
            SELECT cts.team_name, cts.team_id, cts.competition_id 
            FROM competition_team_strength cts
            JOIN competitions c ON cts.competition_id = c.id
            WHERE c.name = 'International'
        """)
        
        international_teams = c.fetchall()
        print(f"Found {len(international_teams)} international teams")
        
        # Update confederations
        updated = 0
        for team_name, team_id, comp_id in international_teams:
            if team_name in confederations:
                confederation = confederations[team_name]
                c.execute("""
                    UPDATE competition_team_strength 
                    SET confederation = %s 
                    WHERE team_id = %s AND competition_id = %s
                """, (confederation, team_id, comp_id))
                print(f"✅ Updated {team_name} -> {confederation}")
                updated += 1
            else:
                print(f"⚠️  No confederation mapping for: {team_name}")
        
        conn.commit()
        print(f"\n✅ Updated {updated}/{len(international_teams)} teams with confederation data")
        
        # Show summary by confederation
        c.execute("""
            SELECT confederation, COUNT(*) as count
            FROM competition_team_strength cts
            JOIN competitions c ON cts.competition_id = c.id
            WHERE c.name = 'International' AND confederation IS NOT NULL
            GROUP BY confederation
            ORDER BY count DESC
        """)
        
        print("\n📊 Teams by Confederation:")
        for conf, count in c.fetchall():
            print(f"  {conf}: {count} teams")
            
        # Test the API query
        print("\n🧪 Testing API query...")
        c.execute("""
            SELECT 
                cts.team_name,
                c.name as league,
                COALESCE(cts.overall_strength, 
                    (COALESCE(cts.elo_score, 0) * 0.18 + 
                     COALESCE(cts.squad_value_score, 0) * 0.15 + 
                     COALESCE(cts.form_score, 0) * 0.05 + 
                     COALESCE(cts.squad_depth_score, 0) * 0.02 + 
                     COALESCE(cts.h2h_performance, 0) * 0.04 + 
                     COALESCE(cts.scoring_patterns, 0) * 0.03)) as calculated_strength,
                cts.confederation
            FROM competition_team_strength cts
            JOIN competitions c ON cts.competition_id = c.id
            WHERE c.name = 'International'
            ORDER BY calculated_strength DESC
            LIMIT 5
        """)
        
        sample_teams = c.fetchall()
        print("Sample international teams:")
        for team_name, league, strength, confederation in sample_teams:
            print(f"  {team_name} ({confederation}): {strength:.2f}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        raise
    
    finally:
        conn.close()
    
    print("\n🎯 Migration complete! Railway database now supports confederations.")

if __name__ == "__main__":
    print("🚀 Starting Railway PostgreSQL Confederation Migration...")
    add_confederations_to_postgresql()