#!/usr/bin/env python3
"""Debug script to trace draw odds calculation"""

from db_interface import DatabaseInterface

def debug_draw_odds(team1, team2):
    """Debug the draw odds calculation step by step"""
    db = DatabaseInterface()
    
    print(f"🔍 DEBUGGING DRAW ODDS: {team1} vs {team2}")
    print("=" * 50)
    
    # Get team comparison
    comparison = db.compare_teams(team1, team2)
    
    if not comparison:
        print("❌ Teams not found!")
        return
    
    print(f"Team 1 ({team1}) strength: {comparison['team1_strength']}")
    print(f"Team 2 ({team2}) strength: {comparison['team2_strength']}")
    print(f"Same league: {comparison['same_league']}")
    
    # Calculate base probabilities
    total_strength = comparison['team1_strength'] + comparison['team2_strength']
    print(f"Total strength: {total_strength}")
    
    if total_strength > 0:
        home_win_prob = (comparison['team1_strength'] / total_strength)
        away_win_prob = (comparison['team2_strength'] / total_strength)
    else:
        home_win_prob = away_win_prob = 0.45
        
    print(f"Initial home win prob: {home_win_prob}")
    print(f"Initial away win prob: {away_win_prob}")
    
    # Add home advantage
    home_advantage = 0.05 if comparison['same_league'] else 0.03
    home_win_prob = min(0.95, home_win_prob + home_advantage)
    print(f"Home win prob (with advantage): {home_win_prob}")
    
    # Calculate draw probability
    strength_diff = abs(comparison['team1_strength'] - comparison['team2_strength'])
    print(f"Strength difference: {strength_diff}")
    
    normalized_diff = min(strength_diff / 50.0, 1.0)
    print(f"Normalized difference: {normalized_diff}")
    
    draw_prob = 0.33 - (normalized_diff * 0.13)
    print(f"Raw draw prob: {draw_prob}")
    
    draw_prob = max(0.20, min(0.33, draw_prob))
    print(f"Clamped draw prob: {draw_prob}")
    
    # Normalize probabilities
    total_prob = home_win_prob + draw_prob
    print(f"Total prob before normalization: {total_prob}")
    
    if total_prob > 1.0:
        home_win_prob = home_win_prob / total_prob
        draw_prob = draw_prob / total_prob
        print(f"Normalized home win prob: {home_win_prob}")
        print(f"Normalized draw prob: {draw_prob}")
    
    away_win_prob = 1.0 - home_win_prob - draw_prob
    print(f"Final away win prob: {away_win_prob}")
    
    if away_win_prob < 0.05:
        away_win_prob = 0.05
        remaining = 0.95
        home_ratio = home_win_prob / (home_win_prob + draw_prob)
        home_win_prob = remaining * home_ratio
        draw_prob = remaining * (1 - home_ratio)
        print(f"RESCALED - Home: {home_win_prob}, Draw: {draw_prob}, Away: {away_win_prob}")
    
    # Calculate final odds
    margin = 1.05
    draw_odds = round(margin / draw_prob, 2)
    
    print(f"\n🎯 FINAL RESULTS:")
    print(f"Draw probability: {draw_prob} ({draw_prob * 100:.1f}%)")
    print(f"Draw odds: {draw_odds}")
    
if __name__ == "__main__":
    debug_draw_odds("Arsenal", "Liverpool")
    print("\n" + "="*50)
    debug_draw_odds("Manchester City", "Southampton")