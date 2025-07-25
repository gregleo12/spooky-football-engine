#!/usr/bin/env python3
"""
Check and display dual strength scores from database
"""
import sqlite3

def check_dual_scores():
    print("🔍 CHECKING DUAL STRENGTH SCORES IN DATABASE")
    print("="*60)
    
    conn = sqlite3.connect("db/football_strength.db")
    c = conn.cursor()
    
    # Check if columns exist
    c.execute("PRAGMA table_info(competition_team_strength)")
    columns = [row[1] for row in c.fetchall()]
    
    dual_columns = ['local_league_strength', 'european_strength']
    print("📊 COLUMN CHECK:")
    for col in dual_columns:
        status = "✅" if col in columns else "❌"
        print(f"{status} {col}")
    
    # Check data count
    c.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(local_league_strength) as local_count,
            COUNT(european_strength) as euro_count
        FROM competition_team_strength
    """)
    
    total, local_count, euro_count = c.fetchone()
    print(f"\n📈 DATA COUNT:")
    print(f"Total teams: {total}")
    print(f"Teams with local scores: {local_count}")
    print(f"Teams with European scores: {euro_count}")
    
    # Show top 10 teams
    print(f"\n🏆 TOP 10 EUROPEAN STRENGTH SCORES:")
    print("-" * 70)
    print(f"{'Rank':<4} {'Team':<25} {'League':<15} {'Local':<8} {'European':<8}")
    print("-" * 70)
    
    c.execute("""
        SELECT 
            c.name as league,
            cts.team_name,
            cts.local_league_strength,
            cts.european_strength
        FROM competition_team_strength cts
        JOIN competitions c ON cts.competition_id = c.id
        WHERE cts.european_strength IS NOT NULL
        ORDER BY cts.european_strength DESC
        LIMIT 10
    """)
    
    for i, (league, team, local, european) in enumerate(c.fetchall(), 1):
        rank = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i:2d}."
        print(f"{rank:<4} {team:<25} {league:<15} {local:6.1f}%  {european:6.1f}%")
    
    # Show example queries
    print(f"\n💡 EXAMPLE QUERIES TO ACCESS DATA:")
    print("-" * 70)
    
    print("\n1️⃣ Get all Premier League teams with dual scores:")
    print("SELECT team_name, local_league_strength, european_strength")
    print("FROM competition_team_strength cts")
    print("JOIN competitions c ON cts.competition_id = c.id") 
    print("WHERE c.name = 'Premier League'")
    print("ORDER BY local_league_strength DESC;")
    
    print("\n2️⃣ Get top 5 European teams:")
    print("SELECT team_name, european_strength")
    print("FROM competition_team_strength")
    print("ORDER BY european_strength DESC LIMIT 5;")
    
    print("\n3️⃣ Compare specific teams:")
    print("SELECT team_name, local_league_strength, european_strength")
    print("FROM competition_team_strength")
    print("WHERE team_name IN ('Real Madrid', 'Manchester City', 'Inter');")
    
    # Test these queries
    print(f"\n🧪 TESTING QUERY RESULTS:")
    print("-" * 70)
    
    print("\nTop 5 European teams:")
    c.execute("SELECT team_name, european_strength FROM competition_team_strength ORDER BY european_strength DESC LIMIT 5")
    for team, strength in c.fetchall():
        print(f"  {team:<25}: {strength:.1f}%")
    
    print("\nPremier League top 3 (local):")
    c.execute("""
        SELECT team_name, local_league_strength 
        FROM competition_team_strength cts
        JOIN competitions c ON cts.competition_id = c.id
        WHERE c.name = 'Premier League'
        ORDER BY local_league_strength DESC LIMIT 3
    """)
    for team, strength in c.fetchall():
        print(f"  {team:<25}: {strength:.1f}%")
    
    conn.close()
    
    print(f"\n✅ Dual strength scores are available in the database!")
    print(f"📊 Access via: competition_team_strength.local_league_strength & european_strength")

if __name__ == "__main__":
    check_dual_scores()