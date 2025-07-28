#!/usr/bin/env python3
"""
Compare Local vs Railway PostgreSQL
Identifies differences between environments to guide synchronization
"""
import os
import psycopg2
from datetime import datetime
from database_config import db_config

def get_environment_data(connection_name, connection):
    """Get key metrics from a database connection"""
    cursor = connection.cursor()
    
    data = {
        'name': connection_name,
        'teams': 0,
        'competitions': 0,
        'strength_records': 0,
        'sample_teams': {},
        'parameters': {},
        'last_update': None
    }
    
    try:
        # Basic counts
        cursor.execute("SELECT COUNT(*) FROM teams")
        data['teams'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM competitions")
        data['competitions'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM competition_team_strength")
        data['strength_records'] = cursor.fetchone()[0]
        
        # Sample team data
        sample_teams = ['Arsenal', 'Real Madrid', 'Bayern München', 'Liverpool', 'Paris Saint Germain']
        for team in sample_teams:
            cursor.execute("""
                SELECT local_league_strength, european_strength, elo_score, 
                       squad_value_score, last_updated
                FROM competition_team_strength
                WHERE team_name = %s
                ORDER BY last_updated DESC
                LIMIT 1
            """, (team,))
            
            result = cursor.fetchone()
            if result:
                data['sample_teams'][team] = {
                    'local_strength': result[0],
                    'european_strength': result[1],
                    'elo_score': result[2],
                    'squad_value': result[3],
                    'last_updated': result[4]
                }
        
        # Parameter completeness
        parameters = ['elo_score', 'squad_value_score', 'form_score', 'squad_depth_score',
                     'h2h_performance_score', 'btts_percentage']
        
        for param in parameters:
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM competition_team_strength 
                WHERE {param} IS NOT NULL
            """)
            data['parameters'][param] = cursor.fetchone()[0]
        
        # Latest update
        cursor.execute("""
            SELECT MAX(last_updated) 
            FROM competition_team_strength
        """)
        data['last_update'] = cursor.fetchone()[0]
        
    except Exception as e:
        print(f"Error getting data from {connection_name}: {e}")
    
    cursor.close()
    return data

def compare_environments():
    """Compare local and Railway PostgreSQL environments"""
    print("🔄 Comparing Local vs Railway PostgreSQL")
    print("=" * 60)
    
    # Get local data
    print("\n📍 Checking Local PostgreSQL...")
    local_config = {
        'host': 'localhost',
        'port': '5432',
        'database': 'football_strength',
        'user': 'football_user',
        'password': 'local_dev_password'
    }
    
    try:
        local_conn = psycopg2.connect(**local_config)
        local_data = get_environment_data("Local", local_conn)
        local_conn.close()
        print("✅ Local data retrieved")
    except Exception as e:
        print(f"❌ Cannot connect to local PostgreSQL: {e}")
        return False
    
    # Get Railway data
    print("\n☁️  Checking Railway PostgreSQL...")
    railway_url = os.environ.get('DATABASE_URL')
    
    if not railway_url:
        print("❌ DATABASE_URL not set. Cannot check Railway PostgreSQL.")
        print("\n💡 Set DATABASE_URL first:")
        print("   export DATABASE_URL='your-railway-postgresql-url'")
        return False
    
    try:
        railway_conn = psycopg2.connect(railway_url)
        railway_data = get_environment_data("Railway", railway_conn)
        railway_conn.close()
        print("✅ Railway data retrieved")
    except Exception as e:
        print(f"❌ Cannot connect to Railway PostgreSQL: {e}")
        return False
    
    # Compare results
    print("\n📊 Environment Comparison:")
    print("-" * 60)
    print(f"{'Metric':<30} {'Local':<15} {'Railway':<15} {'Status'}")
    print("-" * 60)
    
    # Basic counts
    metrics = [
        ('Total Teams', local_data['teams'], railway_data['teams']),
        ('Competitions', local_data['competitions'], railway_data['competitions']),
        ('Strength Records', local_data['strength_records'], railway_data['strength_records'])
    ]
    
    for metric, local_val, railway_val in metrics:
        status = "✅" if local_val == railway_val else "❌"
        print(f"{metric:<30} {local_val:<15} {railway_val:<15} {status}")
    
    # Parameters
    print("\nParameter Coverage:")
    for param in local_data['parameters']:
        local_val = local_data['parameters'].get(param, 0)
        railway_val = railway_data['parameters'].get(param, 0)
        status = "✅" if abs(local_val - railway_val) < 5 else "❌"
        print(f"  {param:<28} {local_val:<15} {railway_val:<15} {status}")
    
    # Sample teams
    print("\n🎯 Sample Team Comparison:")
    for team in local_data['sample_teams']:
        print(f"\n{team}:")
        
        local_team = local_data['sample_teams'].get(team, {})
        railway_team = railway_data['sample_teams'].get(team, {})
        
        if not local_team:
            print("  ❌ Not found in Local")
        elif not railway_team:
            print("  ❌ Not found in Railway")
        else:
            # Compare key metrics
            metrics = [
                ('Local Strength', local_team.get('local_strength'), railway_team.get('local_strength')),
                ('ELO Score', local_team.get('elo_score'), railway_team.get('elo_score')),
                ('Squad Value', local_team.get('squad_value'), railway_team.get('squad_value'))
            ]
            
            for metric, local_val, railway_val in metrics:
                if local_val and railway_val:
                    diff = abs(local_val - railway_val)
                    status = "✅" if diff < 0.1 else "⚠️" if diff < 1 else "❌"
                    print(f"  {metric}: Local={local_val:.1f}, Railway={railway_val:.1f} {status}")
                else:
                    print(f"  {metric}: Missing data")
    
    # Data freshness
    print("\n🕐 Data Freshness:")
    print(f"  Local last update: {local_data['last_update']}")
    print(f"  Railway last update: {railway_data['last_update']}")
    
    if local_data['last_update'] and railway_data['last_update']:
        time_diff = abs((local_data['last_update'] - railway_data['last_update']).total_seconds())
        if time_diff < 3600:  # Less than 1 hour
            print("  ✅ Data freshness similar")
        else:
            print(f"  ⚠️ Time difference: {time_diff/3600:.1f} hours")
    
    return True

def main():
    """Run comparison"""
    print("🚀 PostgreSQL Environment Comparison")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = compare_environments()
    
    if success:
        print("\n✅ Comparison complete!")
        print("\nNext steps:")
        print("1. If Railway is missing data, run agents with DATABASE_URL set")
        print("2. If Railway has stale data, update with agents")
        print("3. Run this script again to verify sync")

if __name__ == "__main__":
    main()