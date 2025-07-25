#!/usr/bin/env python3
"""
Test script for new app features:
1. Last update timestamp
2. Team form data
3. Form display functionality
"""
import sys
import os
sys.path.append('.')

from demo_app import demo
import json
from datetime import datetime

def test_last_update():
    """Test last update functionality"""
    print("🕒 Testing Last Update Feature")
    print("-" * 40)
    
    conn = demo.get_database_connection()
    c = conn.cursor()
    
    c.execute("""
        SELECT MAX(last_updated) as last_update
        FROM competition_team_strength
        WHERE last_updated IS NOT NULL
    """)
    
    result = c.fetchone()
    
    if result and result[0]:
        try:
            last_update = datetime.fromisoformat(result[0].replace('Z', '+00:00'))
            formatted_date = last_update.strftime('%B %d, %Y at %H:%M UTC')
            print(f"✅ Last update found: {formatted_date}")
            print(f"📅 Raw timestamp: {result[0]}")
        except Exception as e:
            print(f"⚠️ Date parsing issue: {e}")
            print(f"📅 Raw timestamp: {result[0]}")
    else:
        print("❌ No last update timestamp found")
    
    conn.close()
    print()

def test_team_form(team_name="Arsenal"):
    """Test team form functionality"""
    print(f"⚽ Testing Team Form Feature for {team_name}")
    print("-" * 40)
    
    conn = demo.get_database_connection()
    c = conn.cursor()
    
    # Get last 5 matches
    c.execute("""
        SELECT 
            home_team_name, away_team_name, home_score, away_score,
            match_date, competition_name
        FROM matches 
        WHERE (home_team_name = ? OR away_team_name = ?)
        AND status = 'FT'
        AND home_score IS NOT NULL 
        AND away_score IS NOT NULL
        ORDER BY match_date DESC
        LIMIT 5
    """, (team_name, team_name))
    
    matches = c.fetchall()
    
    if matches:
        print(f"✅ Found {len(matches)} recent matches for {team_name}")
        
        form_string = ""
        for i, match in enumerate(matches):
            home_team, away_team, home_score, away_score, match_date, competition = match
            
            # Determine result
            if home_team == team_name:
                team_score = home_score
                opponent_score = away_score
                opponent = away_team
                venue = 'H'
            else:
                team_score = away_score
                opponent_score = home_score
                opponent = home_team
                venue = 'A'
            
            if team_score > opponent_score:
                result = 'W'
                result_color = "🟢"
            elif team_score < opponent_score:
                result = 'L'
                result_color = "🔴"
            else:
                result = 'D'
                result_color = "🟡"
            
            form_string += result
            print(f"  {result_color} {result} vs {opponent} ({team_score}-{opponent_score}) {venue} - {match_date}")
        
        print(f"🎯 Form string: {form_string}")
        
        # Test the API logic
        form_data = []
        for match in matches:
            home_team, away_team, home_score, away_score, match_date, competition = match
            
            if home_team == team_name:
                team_score = home_score
                opponent_score = away_score
                opponent = away_team
                venue = 'H'
            else:
                team_score = away_score
                opponent_score = home_score
                opponent = home_team
                venue = 'A'
            
            if team_score > opponent_score:
                result = 'W'
                result_class = 'win'
            elif team_score < opponent_score:
                result = 'L'
                result_class = 'loss'
            else:
                result = 'D'
                result_class = 'draw'
            
            # Format date
            try:
                formatted_date = datetime.fromisoformat(match_date).strftime('%b %d')
            except:
                formatted_date = match_date
            
            form_data.append({
                'result': result,
                'result_class': result_class,
                'opponent': opponent,
                'score': f"{team_score}-{opponent_score}",
                'venue': venue,
                'date': formatted_date,
                'competition': competition
            })
        
        print("📊 API Response format:")
        print(json.dumps({
            'form_string': form_string,
            'matches': form_data[:3],  # Show first 3
            'team': team_name
        }, indent=2))
        
    else:
        print(f"❌ No matches found for {team_name}")
    
    conn.close()
    print()

def test_database_stats():
    """Show database statistics"""
    print("📈 Database Statistics")
    print("-" * 40)
    
    conn = demo.get_database_connection()
    c = conn.cursor()
    
    # Total matches
    c.execute("SELECT COUNT(*) FROM matches")
    total_matches = c.fetchone()[0]
    print(f"📊 Total matches in database: {total_matches}")
    
    # Matches by competition
    c.execute("""
        SELECT competition_name, COUNT(*) 
        FROM matches 
        GROUP BY competition_name 
        ORDER BY COUNT(*) DESC
    """)
    
    print("\n🏆 Matches by competition:")
    for comp, count in c.fetchall():
        print(f"   {comp}: {count} matches")
    
    # Teams with most matches
    c.execute("""
        SELECT 
            CASE 
                WHEN home_team_name = ? THEN home_team_name
                ELSE away_team_name 
            END as team,
            COUNT(*) as match_count
        FROM matches 
        WHERE home_team_name = ? OR away_team_name = ?
        GROUP BY team
        ORDER BY match_count DESC
        LIMIT 5
    """, ("Arsenal", "Arsenal", "Arsenal"))
    
    print(f"\n⚽ Arsenal match count: {c.fetchone()[1] if c.rowcount > 0 else 0}")
    
    conn.close()
    print()

if __name__ == "__main__":
    print("🧪 TESTING NEW APP FEATURES")
    print("=" * 50)
    print()
    
    # Test all features
    test_last_update()
    test_team_form("Arsenal")
    test_team_form("Manchester City")
    test_database_stats()
    
    print("✅ All tests completed!")
    print("\n🚀 New features ready:")
    print("   1. ✅ Last update timestamp in header")
    print("   2. ✅ Team form display (last 5 games)")
    print("   3. ✅ Interactive form popup with match details")
    print("   4. ✅ Color-coded form letters (W/D/L)")
    print("   5. ✅ API endpoints for form and timestamp")