#!/usr/bin/env python3
"""
Local PostgreSQL Database Setup
Creates tables and sample data for testing fresh football app
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import uuid

# Local database connection
LOCAL_DB_URL = "postgresql://localhost:5432/football_local"

def create_tables():
    """Create the database schema"""
    conn = psycopg2.connect(LOCAL_DB_URL)
    cursor = conn.cursor()
    
    # Create competitions table
    cursor.execute("""
        DROP TABLE IF EXISTS competition_team_strength CASCADE;
        DROP TABLE IF EXISTS competitions CASCADE;
        
        CREATE TABLE competitions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(100) NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Create competition_team_strength table with all 10 parameters
    cursor.execute("""
        CREATE TABLE competition_team_strength (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            competition_id UUID REFERENCES competitions(id),
            team_id UUID,
            team_name VARCHAR(100) NOT NULL,
            season VARCHAR(10) DEFAULT '2024',
            
            -- Core 10 parameters
            elo_score DECIMAL(8,4),
            elo_normalized DECIMAL(5,4),
            form_score DECIMAL(5,2),
            form_normalized DECIMAL(5,4),
            squad_value_score DECIMAL(10,1),
            squad_value_normalized DECIMAL(5,4),
            squad_depth_score DECIMAL(5,3),
            squad_depth_normalized DECIMAL(5,4),
            key_player_availability_score DECIMAL(5,3),
            key_player_availability_normalized DECIMAL(5,4),
            motivation_factor_score DECIMAL(5,3),
            motivation_factor_normalized DECIMAL(5,4),
            tactical_matchup_score DECIMAL(5,3),
            tactical_matchup_normalized DECIMAL(5,4),
            offensive_rating DECIMAL(5,3),
            offensive_normalized DECIMAL(5,4),
            defensive_rating DECIMAL(5,3),
            defensive_normalized DECIMAL(5,4),
            h2h_performance_score DECIMAL(5,3),
            h2h_performance_normalized DECIMAL(5,4),
            
            -- Additional fields
            overall_strength DECIMAL(8,4),
            confederation VARCHAR(50),
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            UNIQUE(competition_id, team_name, season)
        );
    """)
    
    conn.commit()
    conn.close()
    print("✅ Database tables created")

def insert_sample_data():
    """Insert realistic sample data for testing"""
    conn = psycopg2.connect(LOCAL_DB_URL)
    cursor = conn.cursor()
    
    # Insert competitions
    leagues = [
        ('Premier League',),
        ('La Liga',),
        ('Serie A',),
        ('Bundesliga',),
        ('Ligue 1',)
    ]
    
    cursor.executemany(
        "INSERT INTO competitions (name) VALUES (%s) ON CONFLICT (name) DO NOTHING",
        leagues
    )
    
    # Get competition IDs
    cursor.execute("SELECT id, name FROM competitions")
    comp_map = {name: str(comp_id) for comp_id, name in cursor.fetchall()}
    
    # Sample teams with realistic data
    teams_data = [
        # Premier League
        ('Premier League', 'Arsenal', 1594.6, 0.72, 1.6, 0.70, 1320.0, 0.85, 1.988, 0.90, 0.2, 0.15, 0.94, 0.80, 0.729, 0.75, 0.726, 0.68, 2.0, 0.95, 1.024, 0.82),
        ('Premier League', 'Liverpool', 1614.0, 0.78, 1.0, 0.60, 1150.0, 0.78, 1.988, 0.90, 0.2, 0.15, 1.0, 0.85, 0.754, 0.77, 0.905, 0.88, 2.0, 0.95, 1.061, 0.85),
        ('Premier League', 'Manchester City', 1583.5, 0.75, 2.2, 0.85, 1340.0, 0.90, 1.950, 0.88, 0.4, 0.30, 1.0, 0.85, 0.800, 0.82, 0.950, 0.92, 1.8, 0.85, 1.100, 0.90),
        ('Premier League', 'Chelsea', 1567.5, 0.70, 0.8, 0.50, 1250.0, 0.82, 1.920, 0.86, 0.1, 0.10, 0.75, 0.70, 0.710, 0.72, 0.680, 0.65, 1.9, 0.90, 0.980, 0.78),
        ('Premier League', 'Tottenham', 1416.3, 0.45, 1.4, 0.65, 847.0, 0.55, 1.800, 0.75, 0.3, 0.25, 0.60, 0.55, 0.650, 0.68, 0.750, 0.72, 1.5, 0.70, 0.920, 0.75),
        
        # La Liga
        ('La Liga', 'Real Madrid', 1626.0, 0.80, 2.8, 0.95, 1370.0, 0.95, 2.100, 0.95, 0.8, 0.70, 1.0, 0.85, 0.850, 0.88, 0.920, 0.90, 2.2, 1.00, 1.200, 0.95),
        ('La Liga', 'Barcelona', 1642.8, 0.85, 2.4, 0.88, 1130.0, 0.75, 2.050, 0.92, 0.6, 0.55, 0.95, 0.82, 0.820, 0.85, 0.880, 0.85, 2.1, 0.98, 1.150, 0.92),
        ('La Liga', 'Atletico Madrid', 1587.5, 0.76, 1.8, 0.75, 689.0, 0.45, 1.950, 0.88, 0.4, 0.35, 0.85, 0.75, 0.780, 0.80, 0.650, 0.62, 2.3, 1.00, 1.080, 0.88),
        ('La Liga', 'Sevilla', 1448.2, 0.50, 0.8, 0.48, 157.4, 0.25, 1.046, 0.45, 0.8, 0.70, 1.0, 0.85, 0.565, 0.58, 0.442, 0.42, 1.727, 0.80, 1.039, 0.82),
        ('La Liga', 'Valencia', 1499.8, 0.58, 1.4, 0.68, 134.3, 0.22, 1.041, 0.44, 0.8, 0.70, 0.32, 0.30, 0.577, 0.59, 0.463, 0.44, 1.759, 0.82, 1.142, 0.88),
        
        # Serie A
        ('Serie A', 'Inter', 1616.2, 0.78, 2.6, 0.90, 580.5, 0.38, 2.000, 0.90, 0.5, 0.45, 0.90, 0.78, 0.800, 0.82, 0.850, 0.82, 2.4, 1.00, 1.120, 0.90),
        ('Serie A', 'Napoli', 1619.0, 0.80, 1.2, 0.62, 542.8, 0.35, 1.980, 0.89, 0.3, 0.28, 0.70, 0.65, 0.750, 0.78, 0.820, 0.80, 2.2, 0.98, 1.090, 0.88),
        ('Serie A', 'Juventus', 1584.4, 0.75, 1.8, 0.75, 611.2, 0.40, 2.020, 0.91, 0.4, 0.35, 0.80, 0.72, 0.780, 0.80, 0.680, 0.65, 2.1, 0.95, 1.050, 0.85),
        ('Serie A', 'AC Milan', 1546.6, 0.65, 1.0, 0.58, 489.3, 0.32, 1.900, 0.85, 0.2, 0.18, 0.75, 0.68, 0.720, 0.74, 0.760, 0.73, 1.9, 0.88, 1.020, 0.82),
        ('Serie A', 'AS Roma', 1595.6, 0.76, 1.6, 0.72, 378.9, 0.28, 1.950, 0.88, 0.3, 0.28, 0.65, 0.60, 0.740, 0.76, 0.720, 0.70, 2.0, 0.92, 1.070, 0.86),
        
        # Bundesliga  
        ('Bundesliga', 'Bayern München', 1589.2, 0.76, 2.4, 0.88, 889.0, 0.60, 2.100, 0.95, 0.6, 0.55, 0.95, 0.82, 0.820, 0.85, 0.900, 0.88, 2.1, 0.95, 1.180, 0.94),
        ('Bundesliga', 'RB Leipzig', 1556.8, 0.68, 1.8, 0.75, 423.7, 0.30, 1.920, 0.86, 0.4, 0.35, 0.80, 0.72, 0.760, 0.78, 0.810, 0.78, 1.8, 0.82, 1.040, 0.84),
        ('Bundesliga', 'Borussia Dortmund', 1532.1, 0.62, 1.2, 0.62, 387.9, 0.28, 1.880, 0.84, 0.3, 0.28, 0.70, 0.65, 0.720, 0.74, 0.780, 0.75, 1.7, 0.78, 1.010, 0.81),
        ('Bundesliga', 'Bayer Leverkusen', 1578.4, 0.73, 2.0, 0.82, 356.2, 0.26, 1.940, 0.87, 0.5, 0.45, 0.85, 0.75, 0.780, 0.80, 0.830, 0.80, 1.9, 0.88, 1.060, 0.86),
        
        # Ligue 1
        ('Ligue 1', 'Paris Saint Germain', 1649.0, 0.88, 1.4, 0.68, 1140.0, 0.78, 2.200, 1.00, 0.9, 0.85, 1.0, 0.85, 0.900, 0.92, 0.950, 0.92, 2.3, 1.00, 1.250, 1.00),
        ('Ligue 1', 'Monaco', 1534.7, 0.63, 1.6, 0.72, 312.4, 0.24, 1.850, 0.82, 0.4, 0.35, 0.75, 0.68, 0.710, 0.72, 0.760, 0.73, 1.8, 0.82, 1.020, 0.82),
        ('Ligue 1', 'Marseille', 1518.9, 0.58, 1.0, 0.58, 298.7, 0.23, 1.820, 0.80, 0.3, 0.28, 0.65, 0.60, 0.680, 0.70, 0.720, 0.70, 1.7, 0.78, 0.980, 0.78),
        ('Ligue 1', 'Lille', 1496.2, 0.54, 0.8, 0.48, 187.3, 0.18, 1.750, 0.75, 0.2, 0.18, 0.60, 0.55, 0.640, 0.66, 0.680, 0.66, 1.6, 0.72, 0.920, 0.74),
    ]
    
    # Insert team data
    for team_data in teams_data:
        league_name = team_data[0]
        comp_id = comp_map[league_name]
        
        cursor.execute("""
            INSERT INTO competition_team_strength (
                competition_id, team_name, season,
                elo_score, elo_normalized, form_score, form_normalized,
                squad_value_score, squad_value_normalized, squad_depth_score, squad_depth_normalized,
                key_player_availability_score, key_player_availability_normalized,
                motivation_factor_score, motivation_factor_normalized,
                tactical_matchup_score, tactical_matchup_normalized,
                offensive_rating, offensive_normalized,
                defensive_rating, defensive_normalized,
                h2h_performance_score, h2h_performance_normalized
            ) VALUES (
                %s, %s, '2024',
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) ON CONFLICT (competition_id, team_name, season) DO NOTHING
        """, (comp_id,) + team_data[1:])
    
    conn.commit()
    conn.close()
    print(f"✅ Sample data inserted: {len(teams_data)} teams across 5 leagues")

def verify_setup():
    """Verify the database setup"""
    conn = psycopg2.connect(LOCAL_DB_URL)
    cursor = conn.cursor()
    
    # Check competitions
    cursor.execute("SELECT COUNT(*) FROM competitions")
    comp_count = cursor.fetchone()[0]
    
    # Check teams
    cursor.execute("SELECT COUNT(*) FROM competition_team_strength")
    team_count = cursor.fetchone()[0]
    
    # Check parameter coverage
    cursor.execute("""
        SELECT 
            COUNT(CASE WHEN elo_score IS NOT NULL THEN 1 END) as elo_coverage,
            COUNT(CASE WHEN form_score IS NOT NULL THEN 1 END) as form_coverage,
            COUNT(CASE WHEN squad_value_score IS NOT NULL THEN 1 END) as squad_value_coverage,
            COUNT(CASE WHEN h2h_performance_score IS NOT NULL THEN 1 END) as h2h_coverage,
            COUNT(*) as total
        FROM competition_team_strength
    """)
    coverage = cursor.fetchone()
    
    conn.close()
    
    print(f"📊 Database verification:")
    print(f"   - Competitions: {comp_count}")
    print(f"   - Teams: {team_count}")
    print(f"   - ELO coverage: {coverage[0]}/{coverage[4]} ({coverage[0]/coverage[4]*100:.1f}%)")
    print(f"   - Form coverage: {coverage[1]}/{coverage[4]} ({coverage[1]/coverage[4]*100:.1f}%)")
    print(f"   - Squad Value coverage: {coverage[2]}/{coverage[4]} ({coverage[2]/coverage[4]*100:.1f}%)")
    print(f"   - H2H coverage: {coverage[3]}/{coverage[4]} ({coverage[3]/coverage[4]*100:.1f}%)")
    
    return comp_count > 0 and team_count > 0

if __name__ == '__main__':
    print("🏗️ Setting up local PostgreSQL database...")
    
    try:
        create_tables()
        insert_sample_data()
        
        if verify_setup():
            print("✅ Local database setup complete!")
            print("🔗 Connection string: postgresql://localhost:5432/football_local")
        else:
            print("❌ Database verification failed")
            
    except Exception as e:
        print(f"❌ Setup failed: {e}")