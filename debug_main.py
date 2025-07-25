import sqlite3

print("🔍 Starting debug...")

try:
    conn = sqlite3.connect("db/football_strength.db")
    c = conn.cursor()
    print("✅ Connected to database")
    
    # Check teams
    c.execute("SELECT COUNT(*) FROM teams")
    team_count = c.fetchone()[0]
    print(f"📊 Found {team_count} teams")
    
    # Check parameters  
    c.execute("SELECT COUNT(*) FROM team_parameters")
    param_count = c.fetchone()[0]
    print(f"📊 Found {param_count} parameters")
    
    # Show some sample data
    c.execute("SELECT name FROM teams LIMIT 3")
    sample_teams = c.fetchall()
    print(f"📝 Sample teams: {[team[0] for team in sample_teams]}")
    
    # Show parameter types
    c.execute("SELECT DISTINCT parameter FROM team_parameters")
    param_types = [row[0] for row in c.fetchall()]
    print(f"📝 Parameter types: {param_types}")
    
    # Test one team's data
    if sample_teams:
        test_team = sample_teams[0][0]
        c.execute("SELECT id FROM teams WHERE name = ?", (test_team,))
        team_id = c.fetchone()[0]
        
        c.execute("SELECT parameter, value FROM team_parameters WHERE team_id = ?", (team_id,))
        params = c.fetchall()
        print(f"📝 {test_team} parameters: {params}")
    
    conn.close()
    print("✅ Debug complete")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()