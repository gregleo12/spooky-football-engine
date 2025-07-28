#!/usr/bin/env python3
"""
Verify Local PostgreSQL Data
Comprehensive check of local database state before Railway sync
"""
import os
import sys
from datetime import datetime
from database_config import db_config

def verify_local_data():
    """Comprehensive local PostgreSQL data verification"""
    print("🔍 Local PostgreSQL Data Verification")
    print("=" * 60)
    
    # Ensure we're checking local (no DATABASE_URL)
    if os.environ.get('DATABASE_URL'):
        print("⚠️  DATABASE_URL is set - unsetting to check local PostgreSQL")
        del os.environ['DATABASE_URL']
    
    print(f"Database: {db_config.get_db_info()}")
    print()
    
    try:
        conn = db_config.get_connection()
        cursor = conn.cursor()
        
        # 1. Basic counts
        print("📊 Database Overview:")
        cursor.execute("SELECT COUNT(*) FROM teams")
        team_count = cursor.fetchone()[0]
        print(f"  Total teams: {team_count}")
        
        cursor.execute("SELECT COUNT(*) FROM competitions")
        comp_count = cursor.fetchone()[0]
        print(f"  Total competitions: {comp_count}")
        
        cursor.execute("SELECT COUNT(*) FROM competition_team_strength")
        strength_count = cursor.fetchone()[0]
        print(f"  Total strength records: {strength_count}")
        print()
        
        # 2. Teams by competition
        print("📋 Teams by Competition:")
        cursor.execute("""
            SELECT c.name, COUNT(DISTINCT cts.team_id) as team_count
            FROM competition_team_strength cts
            JOIN competitions c ON cts.competition_id = c.id
            GROUP BY c.name
            ORDER BY c.name
        """)
        
        for comp_name, count in cursor.fetchall():
            print(f"  {comp_name}: {count} teams")
        print()
        
        # 3. Parameter completeness check
        print("✅ Parameter Completeness Check:")
        parameters = [
            ('elo_score', 'ELO Score'),
            ('squad_value_score', 'Squad Value'),
            ('form_score', 'Form Score'),
            ('squad_depth_score', 'Squad Depth'),
            ('home_advantage_score', 'Home Advantage'),
            ('fatigue_factor_score', 'Fatigue Factor'),
            ('key_player_availability_score', 'Key Player Availability'),
            ('motivation_factor_score', 'Motivation Factor'),
            ('tactical_matchup_score', 'Tactical Matchup'),
            ('h2h_performance_score', 'H2H Performance'),
            ('scoring_patterns', 'Scoring Patterns (btts_percentage)')
        ]
        
        for param, display_name in parameters:
            if param == 'scoring_patterns':
                param = 'btts_percentage'  # Use a scoring pattern field
            
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM competition_team_strength 
                WHERE {param} IS NOT NULL
            """)
            filled = cursor.fetchone()[0]
            percentage = (filled / strength_count * 100) if strength_count > 0 else 0
            status = "✅" if percentage > 80 else "⚠️" if percentage > 50 else "❌"
            print(f"  {status} {display_name}: {filled}/{strength_count} ({percentage:.1f}%)")
        print()
        
        # 4. Data freshness
        print("🕐 Data Freshness:")
        cursor.execute("""
            SELECT MIN(last_updated), MAX(last_updated), COUNT(DISTINCT DATE(last_updated))
            FROM competition_team_strength
            WHERE last_updated IS NOT NULL
        """)
        min_date, max_date, unique_days = cursor.fetchone()
        print(f"  Oldest update: {min_date}")
        print(f"  Newest update: {max_date}")
        print(f"  Unique update days: {unique_days}")
        print()
        
        # 5. Sample team data
        print("📈 Sample Team Data (Top 5 by strength):")
        cursor.execute("""
            SELECT team_name, local_league_strength, european_strength,
                   elo_score, squad_value_score, form_score, squad_depth_score
            FROM competition_team_strength
            WHERE local_league_strength IS NOT NULL
            ORDER BY local_league_strength DESC
            LIMIT 5
        """)
        
        print(f"{'Team':<25} {'Local':<8} {'Euro':<8} {'ELO':<8} {'Value':<8} {'Form':<8} {'Depth':<8}")
        print("-" * 85)
        
        for row in cursor.fetchall():
            team, local, euro, elo, value, form, depth = row
            print(f"{team:<25} {local:<8.1f} {euro:<8.1f} {elo:<8.1f} {value:<8.0f} "
                  f"{form if form else 'N/A':<8} {depth if depth else 'N/A':<8}")
        print()
        
        # 6. Specific teams check
        print("🎯 Key Teams Verification:")
        key_teams = ['Arsenal', 'Real Madrid', 'Bayern München', 'Juventus', 'Paris Saint Germain']
        
        for team in key_teams:
            cursor.execute("""
                SELECT local_league_strength, elo_score, squad_value_score
                FROM competition_team_strength
                WHERE team_name = %s
            """, (team,))
            
            result = cursor.fetchone()
            if result:
                strength, elo, value = result
                print(f"  {team}: Strength={strength:.1f}, ELO={elo:.1f}, Value=€{value:.0f}M")
            else:
                print(f"  {team}: ❌ NOT FOUND")
        
        cursor.close()
        conn.close()
        
        print("\n✅ Local data verification complete!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error verifying local data: {e}")
        return False

def main():
    """Run verification"""
    print("🚀 Local PostgreSQL Data Verification")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = verify_local_data()
    
    if success:
        print("\n✅ Local PostgreSQL data looks good!")
        print("\nNext step: Run this same script with DATABASE_URL set to check Railway")
    else:
        print("\n❌ Issues found with local data. Fix these before syncing to Railway.")

if __name__ == "__main__":
    main()