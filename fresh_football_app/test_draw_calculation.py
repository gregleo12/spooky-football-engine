#!/usr/bin/env python3
"""Test the exact draw calculation that should be happening"""

# Exact values from production API
team1_strength = 485.711046
team2_strength = 463.70635

print("🔍 TESTING EXACT PRODUCTION VALUES")
print("=" * 50)

# Step-by-step calculation
total_strength = team1_strength + team2_strength
home_win_prob = team1_strength / total_strength
away_win_prob = team2_strength / total_strength

print(f"Total strength: {total_strength}")
print(f"Initial home win prob: {home_win_prob:.6f}")
print(f"Initial away win prob: {away_win_prob:.6f}")

# Add home advantage (same league)
home_advantage = 0.05
home_win_prob = min(0.95, home_win_prob + home_advantage)

print(f"Home win prob with advantage: {home_win_prob:.6f}")

# Calculate draw probability
strength_diff = abs(team1_strength - team2_strength)
normalized_diff = min(strength_diff / 50.0, 1.0)
draw_prob = 0.33 - (normalized_diff * 0.13)
draw_prob = max(0.20, min(0.33, draw_prob))

print(f"Strength difference: {strength_diff}")
print(f"Normalized difference: {normalized_diff}")
print(f"Raw draw prob: {draw_prob:.6f}")

# Check if we need to normalize
total_prob = home_win_prob + draw_prob
print(f"Total prob before normalization: {total_prob:.6f}")

if total_prob > 1.0:
    home_win_prob = home_win_prob / total_prob
    draw_prob = draw_prob / total_prob
    print(f"NORMALIZED - Home: {home_win_prob:.6f}, Draw: {draw_prob:.6f}")

away_win_prob = 1.0 - home_win_prob - draw_prob
print(f"Away win prob: {away_win_prob:.6f}")

# Check if away prob is too low
if away_win_prob < 0.05:
    print("🚨 RESCALING because away < 0.05")
    away_win_prob = 0.05
    remaining = 0.95
    home_ratio = home_win_prob / (home_win_prob + draw_prob)
    home_win_prob = remaining * home_ratio
    draw_prob = remaining * (1 - home_ratio)

print(f"\nFINAL PROBABILITIES:")
print(f"Home: {home_win_prob:.3f} ({home_win_prob*100:.1f}%)")
print(f"Draw: {draw_prob:.3f} ({draw_prob*100:.1f}%)")
print(f"Away: {away_win_prob:.3f} ({away_win_prob*100:.1f}%)")
print(f"Total: {home_win_prob + draw_prob + away_win_prob:.3f}")

# Calculate odds
margin = 1.05
home_odds = round(margin / home_win_prob, 2)
draw_odds = round(margin / draw_prob, 2)
away_odds = round(margin / away_win_prob, 2)

print(f"\nFINAL ODDS:")
print(f"Home: {home_odds}")
print(f"Draw: {draw_odds}")
print(f"Away: {away_odds}")

print(f"\nPRODUCTION SHOWS: Home=1.87, Draw=10.5, Away=3.1")