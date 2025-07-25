#!/usr/bin/env python3
"""
Test script for the Football Strength Demo
Tests various match scenarios to verify the dual scoring system
"""
import sys
import os
sys.path.append('.')

from demo_app import FootballStrengthDemo

def test_demo_scenarios():
    """Test various match scenarios"""
    print("🧪 TESTING FOOTBALL STRENGTH DEMO")
    print("=" * 60)
    
    demo = FootballStrengthDemo()
    
    # Test scenarios
    test_cases = [
        # Same league matches (should use local scores)
        ("Real Madrid", "Barcelona", "Same league - La Liga El Clasico"),
        ("Manchester City", "Arsenal", "Same league - Premier League top clash"),
        ("Inter", "Napoli", "Same league - Serie A title race"),
        
        # Cross-league matches (should use European scores)
        ("Real Madrid", "Manchester City", "Cross-league - La Liga vs Premier League"),
        ("Bayern München", "Paris Saint Germain", "Cross-league - Bundesliga vs Ligue 1"),
        ("Inter", "Arsenal", "Cross-league - Serie A vs Premier League"),
    ]
    
    for home, away, description in test_cases:
        print(f"\n🏟️ {description}")
        print("-" * 50)
        
        result = demo.analyze_match(home, away)
        
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
            continue
        
        print(f"🏠 {result['home_team']['name']} ({result['home_team']['league']})")
        print(f"✈️ {result['away_team']['name']} ({result['away_team']['league']})")
        print(f"📊 Score Type: {result['score_type']}")
        print(f"💪 Strengths: {result['home_strength']:.1f}% vs {result['away_strength']:.1f}%")
        print(f"🎯 Probabilities: {result['home_probability']}% vs {result['away_probability']}%")
        print(f"🏆 Favorite: {result['favorite']} ({result['favorite_probability']}%)")
        print(f"💡 {result['explanation']}")
    
    print(f"\n✅ Demo testing complete!")
    print("🌐 Launch the web interface with: python3 demo_app.py")
    print("🔗 Then visit: http://localhost:5001")

if __name__ == "__main__":
    test_demo_scenarios()