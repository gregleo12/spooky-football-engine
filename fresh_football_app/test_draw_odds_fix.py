#!/usr/bin/env python3
"""
Test script to verify draw odds fix
Tests multiple team combinations to ensure realistic draw odds
"""
from new_app import app
import json

# Test combinations with different strength differences
test_matches = [
    # Evenly matched teams (should have draw odds around 3.0-3.5)
    ("Arsenal", "Liverpool"),
    ("Manchester City", "Chelsea"),
    ("Barcelona", "Real Madrid"),
    
    # Moderate difference (should have draw odds around 3.5-4.5)
    ("Arsenal", "Tottenham Hotspur"),
    ("Bayern München", "RB Leipzig"),
    
    # Large difference (should have draw odds around 4.5-6.0)
    ("Manchester City", "Southampton"),
    ("Real Madrid", "Las Palmas"),
]

print("🔍 Testing Draw Odds Fix")
print("=" * 60)

with app.test_client() as client:
    for team1, team2 in test_matches:
        response = client.get(f'/api/odds/{team1}/{team2}')
        
        if response.status_code == 200:
            odds_data = json.loads(response.data)
            match_odds = odds_data['match_outcome']
            
            home_odds = match_odds['home_win']['odds']
            draw_odds = match_odds['draw']['odds']
            away_odds = match_odds['away_win']['odds']
            
            home_prob = match_odds['home_win']['probability']
            draw_prob = match_odds['draw']['probability']
            away_prob = match_odds['away_win']['probability']
            
            # Get comparison data to see strength difference
            comp_response = client.get(f'/api/compare/{team1}/{team2}')
            if comp_response.status_code == 200:
                comp_data = json.loads(comp_response.data)
                strength_diff = abs(comp_data['team1_strength'] - comp_data['team2_strength'])
                print(f"\n{team1} vs {team2} (strength diff: {strength_diff:.3f}):")
            else:
                print(f"\n{team1} vs {team2}:")
            
            print(f"  Home: {home_odds:.2f} ({home_prob}%)")
            print(f"  Draw: {draw_odds:.2f} ({draw_prob}%) {'✅' if draw_odds != 10.5 else '❌ BUG!'}")
            print(f"  Away: {away_odds:.2f} ({away_prob}%)")
            print(f"  Total probability: {home_prob + draw_prob + away_prob}%")
            
            # Verify draw odds are realistic
            if draw_odds == 10.5:
                print(f"  ❌ FAILED: Draw odds still stuck at 10.5!")
            elif 2.5 <= draw_odds <= 6.5:
                print(f"  ✅ PASSED: Draw odds are realistic!")
            else:
                print(f"  ⚠️  WARNING: Draw odds {draw_odds} outside expected range")
        else:
            print(f"\n❌ Error fetching odds for {team1} vs {team2}: {response.status_code}")

print("\n" + "=" * 60)
print("Test complete!")