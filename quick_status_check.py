#!/usr/bin/env python3
"""
Quick Status Check
Fast overview of current database state for rapid assessment
"""
import os
from datetime import datetime
from database_config import db_config

def quick_status():
    """Quick database status check"""
    print(f"⚡ Quick Status Check")
    print(f"Database: {db_config.get_db_info()}")
    print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
    print("-" * 40)
    
    try:
        conn = db_config.get_connection()
        cursor = conn.cursor()
        
        # Essential counts
        cursor.execute("SELECT COUNT(*) FROM teams")
        teams = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM competition_team_strength")
        records = cursor.fetchone()[0]
        
        # Quick Arsenal check
        cursor.execute("""
            SELECT local_league_strength, elo_score 
            FROM competition_team_strength 
            WHERE team_name = 'Arsenal' 
            LIMIT 1
        """)
        arsenal = cursor.fetchone()
        
        print(f"Teams: {teams}")
        print(f"Records: {records}")
        if arsenal:
            print(f"Arsenal: Strength={arsenal[0]:.1f}, ELO={arsenal[1]:.1f}")
        else:
            print("Arsenal: Not found")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    quick_status()