#!/usr/bin/env python3
"""Debug script that mimics exact production API logic"""

from db_interface import DatabaseInterface

def debug_production_odds(team1, team2):
    """Replicate exact production API logic"""
    db = DatabaseInterface()
    
    print(f"🔍 PRODUCTION API LOGIC: {team1} vs {team2}")
    print("=" * 50)
    
    comparison = db.compare_teams(team1, team2)
    
    if not comparison:
        print("❌ Teams not found!")
        return
    
    # Calculate base probabilities
    total_strength = comparison['team1_strength'] + comparison['team2_strength']
    if total_strength > 0:
        home_win_prob = (comparison['team1_strength'] / total_strength)
        away_win_prob = (comparison['team2_strength'] / total_strength)
    else:
        home_win_prob = away_win_prob = 0.45
    
    # Add home advantage
    home_advantage = 0.05 if comparison['same_league'] else 0.03
    home_win_prob = min(0.95, home_win_prob + home_advantage)
    
    # Calculate draw probability based on team similarity
    strength_diff = abs(comparison['team1_strength'] - comparison['team2_strength'])
    normalized_diff = min(strength_diff / 50.0, 1.0)
    draw_prob = 0.33 - (normalized_diff * 0.13)
    draw_prob = max(0.20, min(0.33, draw_prob))
    
    print(f"Before normalization: Home={home_win_prob:.3f}, Draw={draw_prob:.3f}")
    
    # Normalize probabilities to ensure they sum to 1.0
    total_prob = home_win_prob + draw_prob
    if total_prob > 1.0:
        # Scale down proportionally
        home_win_prob = home_win_prob / total_prob
        draw_prob = draw_prob / total_prob
    
    away_win_prob = 1.0 - home_win_prob - draw_prob
    
    print(f"After normalization: Home={home_win_prob:.3f}, Draw={draw_prob:.3f}, Away={away_win_prob:.3f}")
    
    # Ensure away_win_prob is not negative
    if away_win_prob < 0.05:
        print(f"🚨 RESCALING: away_win_prob {away_win_prob:.3f} < 0.05")
        away_win_prob = 0.05
        # Rescale home and draw
        remaining = 0.95
        home_ratio = home_win_prob / (home_win_prob + draw_prob)
        home_win_prob = remaining * home_ratio
        draw_prob = remaining * (1 - home_ratio)
        print(f"After rescaling: Home={home_win_prob:.3f}, Draw={draw_prob:.3f}, Away={away_win_prob:.3f}")
    
    # Convert to decimal odds with margin
    margin = 1.05
    draw_odds = round(margin / draw_prob, 2)
    
    print(f"\n🎯 FINAL: Draw prob={draw_prob:.3f} ({draw_prob*100:.1f}%), Odds={draw_odds}")
    
if __name__ == "__main__":
    debug_production_odds("Arsenal", "Liverpool")
    print("\n" + "="*60 + "\n")
    debug_production_odds("Manchester City", "Southampton")