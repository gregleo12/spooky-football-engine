#!/usr/bin/env python3
"""
Add confederation information to international teams
UEFA, CONMEBOL, CONCACAF, CAF, AFC, OFC
"""
import sqlite3

def add_confederations():
    """Add confederation column and data to international teams"""
    
    # Confederation mappings
    confederations = {
        # UEFA (Europe)
        'Germany': 'UEFA',
        'France': 'UEFA', 
        'England': 'UEFA',
        'Spain': 'UEFA',
        'Italy': 'UEFA',
        'Portugal': 'UEFA',
        'Netherlands': 'UEFA',
        'Belgium': 'UEFA',
        'Croatia': 'UEFA',
        'Denmark': 'UEFA',
        'Switzerland': 'UEFA',
        'Poland': 'UEFA',
        'Wales': 'UEFA',
        'Serbia': 'UEFA',
        'Austria': 'UEFA',
        'Ukraine': 'UEFA',
        'Czech Republic': 'UEFA',
        'Turkey': 'UEFA',
        'Sweden': 'UEFA',
        'Russia': 'UEFA',
        
        # CONMEBOL (South America)
        'Brazil': 'CONMEBOL',
        'Argentina': 'CONMEBOL',
        'Uruguay': 'CONMEBOL',
        'Colombia': 'CONMEBOL',
        'Chile': 'CONMEBOL',
        'Peru': 'CONMEBOL',
        'Ecuador': 'CONMEBOL',
        'Paraguay': 'CONMEBOL',
        'Bolivia': 'CONMEBOL',
        'Venezuela': 'CONMEBOL',
        
        # CONCACAF (North/Central America, Caribbean)
        'Mexico': 'CONCACAF',
        'USA': 'CONCACAF',
        'Canada': 'CONCACAF',
        'Costa Rica': 'CONCACAF',
        'Jamaica': 'CONCACAF',
        'Panama': 'CONCACAF',
        
        # CAF (Africa)
        'Morocco': 'CAF',
        'Senegal': 'CAF',
        'Tunisia': 'CAF',
        'Algeria': 'CAF',
        'Nigeria': 'CAF',
        'Egypt': 'CAF',
        'Ghana': 'CAF',
        'Cameroon': 'CAF',
        'South Africa': 'CAF',
        
        # AFC (Asia)
        'Japan': 'AFC',
        'South Korea': 'AFC',
        'Iran': 'AFC',
        'Saudi Arabia': 'AFC',
        'Australia': 'AFC',  # Australia moved from OFC to AFC
        'Qatar': 'AFC',
        'Iraq': 'AFC',
        'China': 'AFC',
        'Thailand': 'AFC',
        'India': 'AFC'
    }
    
    conn = sqlite3.connect("db/football_strength.db")
    c = conn.cursor()
    
    # Check if confederation column exists
    c.execute("PRAGMA table_info(competition_team_strength)")
    columns = [col[1] for col in c.fetchall()]
    
    if 'confederation' not in columns:
        print("Adding confederation column...")
        c.execute("ALTER TABLE competition_team_strength ADD COLUMN confederation TEXT")
    
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
                SET confederation = ? 
                WHERE team_id = ? AND competition_id = ?
            """, (confederation, team_id, comp_id))
            print(f"Updated {team_name} -> {confederation}")
            updated += 1
        else:
            print(f"⚠️  No confederation mapping for: {team_name}")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Updated {updated}/{len(international_teams)} teams with confederation data")
    
    # Show summary by confederation
    conn = sqlite3.connect("db/football_strength.db")
    c = conn.cursor()
    
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
    
    conn.close()

if __name__ == "__main__":
    add_confederations()