#!/usr/bin/env python3
"""
Phase 2 Verification Check - Betting Odds Generation
Comprehensive validation of odds conversion functionality
"""
import sqlite3
import time
import math
from datetime import datetime

def convert_probability_to_odds(probability):
    """Convert probability percentage to decimal betting odds"""
    if probability <= 0 or probability >= 100:
        return None
    
    # Convert percentage to decimal (0-1)
    prob_decimal = probability / 100.0
    
    # Calculate decimal odds (1 / probability)
    decimal_odds = 1.0 / prob_decimal
    
    return round(decimal_odds, 2)

def calculate_betting_odds(home_strength, away_strength, match_context="neutral"):
    """
    Calculate comprehensive betting odds from team strengths
    
    Returns dict with:
    - Match outcome odds (Home/Draw/Away)
    - Over/Under 2.5 goals
    - Both Teams to Score (BTTS)
    """
    start_time = time.time()
    
    # 1. BASE PROBABILITIES FROM STRENGTH
    total_strength = home_strength + away_strength
    
    if total_strength > 0:
        home_base = (home_strength / total_strength) * 100
        away_base = (away_strength / total_strength) * 100
    else:
        home_base = away_base = 50.0
    
    # 2. HOME ADVANTAGE ADJUSTMENT
    home_advantage = 0.10  # 10% boost for home team
    if match_context == "home":
        home_prob = min(95.0, home_base + (home_advantage * 100))
        away_prob = max(5.0, 100.0 - home_prob)
    elif match_context == "away":
        away_prob = min(95.0, away_base + (home_advantage * 100))
        home_prob = max(5.0, 100.0 - away_prob)
    else:  # neutral
        home_prob = home_base
        away_prob = away_base
    
    # 3. DRAW PROBABILITY CALCULATION
    # Higher draw probability when teams are closely matched
    strength_difference = abs(home_strength - away_strength)
    max_draw_prob = 35.0  # Maximum draw probability
    min_draw_prob = 15.0  # Minimum draw probability
    
    # Linear scaling based on strength difference
    if strength_difference <= 0.1:
        draw_prob = max_draw_prob
    elif strength_difference >= 0.4:
        draw_prob = min_draw_prob
    else:
        # Linear interpolation
        draw_prob = max_draw_prob - ((strength_difference - 0.1) / 0.3) * (max_draw_prob - min_draw_prob)
    
    # 4. NORMALIZE TO 100%
    total_prob = home_prob + away_prob + draw_prob
    home_prob = (home_prob / total_prob) * 100
    away_prob = (away_prob / total_prob) * 100
    draw_prob = (draw_prob / total_prob) * 100
    
    # 5. CONVERT TO DECIMAL ODDS
    home_odds = convert_probability_to_odds(home_prob)
    draw_odds = convert_probability_to_odds(draw_prob)
    away_odds = convert_probability_to_odds(away_prob)
    
    # 6. GOALS MARKET CALCULATIONS
    # Over/Under 2.5 goals based on team offensive strength
    avg_strength = (home_strength + away_strength) / 2.0
    
    # Higher strength teams tend to score more goals
    over_2_5_prob = 45.0 + (avg_strength * 20.0)  # 45-65% range
    over_2_5_prob = max(35.0, min(75.0, over_2_5_prob))
    under_2_5_prob = 100.0 - over_2_5_prob
    
    over_2_5_odds = convert_probability_to_odds(over_2_5_prob)
    under_2_5_odds = convert_probability_to_odds(under_2_5_prob)
    
    # 7. BOTH TEAMS TO SCORE (BTTS)
    # Based on both teams having reasonable offensive capability
    min_strength = min(home_strength, away_strength)
    btts_yes_prob = 50.0 + (min_strength * 25.0)  # 50-75% range
    btts_yes_prob = max(40.0, min(80.0, btts_yes_prob))
    btts_no_prob = 100.0 - btts_yes_prob
    
    btts_yes_odds = convert_probability_to_odds(btts_yes_prob)
    btts_no_odds = convert_probability_to_odds(btts_no_prob)
    
    # 8. PERFORMANCE TIMING
    calculation_time = time.time() - start_time
    
    return {
        'match_outcome': {
            'home_win': {
                'probability': round(home_prob, 1),
                'odds': home_odds
            },
            'draw': {
                'probability': round(draw_prob, 1),
                'odds': draw_odds
            },
            'away_win': {
                'probability': round(away_prob, 1),
                'odds': away_odds
            }
        },
        'goals_market': {
            'over_2_5': {
                'probability': round(over_2_5_prob, 1),
                'odds': over_2_5_odds
            },
            'under_2_5': {
                'probability': round(under_2_5_prob, 1),
                'odds': under_2_5_odds
            }
        },
        'btts_market': {
            'yes': {
                'probability': round(btts_yes_prob, 1),
                'odds': btts_yes_odds
            },
            'no': {
                'probability': round(btts_no_prob, 1),
                'odds': btts_no_odds
            }
        },
        'calculation_time_ms': round(calculation_time * 1000, 2),
        'team_strengths': {
            'home': home_strength,
            'away': away_strength
        }
    }

def run_phase2_verification():
    """Run comprehensive Phase 2 verification tests"""
    
    print("🎯 PHASE 2 VERIFICATION - BETTING ODDS GENERATION")
    print("=" * 80)
    print("Testing conversion from team strength scores to betting odds")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    conn = sqlite3.connect("db/football_strength.db")
    c = conn.cursor()
    
    # TEST 1: GET REAL TEAM STRENGTH DATA
    print("1️⃣ REAL TEAM STRENGTH DATA")
    print("-" * 50)
    
    # Get top teams for testing
    c.execute("""
        SELECT cts.team_name, c.name as league, cts.phase1_strength_optimized
        FROM competition_team_strength cts
        JOIN competitions c ON cts.competition_id = c.id
        WHERE cts.phase1_strength_optimized IS NOT NULL
        AND c.name IN ('Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1')
        ORDER BY cts.phase1_strength_optimized DESC
        LIMIT 10
    """)
    
    top_teams = c.fetchall()
    print("   Real Phase 1 strength scores:")
    for i, (team, league, strength) in enumerate(top_teams[:5], 1):
        print(f"   {i}. {team} ({league}): {strength:.3f}")
    print()
    
    # TEST 2: SAME-LEAGUE MATCHUP ODDS
    print("2️⃣ SAME-LEAGUE MATCHUP - PREMIER LEAGUE")
    print("-" * 50)
    
    # Get Liverpool and Manchester City directly from database
    c.execute("""
        SELECT cts.phase1_strength_optimized
        FROM competition_team_strength cts
        JOIN competitions c ON cts.competition_id = c.id
        WHERE cts.team_name = 'Liverpool' AND c.name = 'Premier League'
    """)
    liverpool_result = c.fetchone()
    liverpool_strength = liverpool_result[0] if liverpool_result else None
    
    c.execute("""
        SELECT cts.phase1_strength_optimized
        FROM competition_team_strength cts
        JOIN competitions c ON cts.competition_id = c.id
        WHERE cts.team_name = 'Manchester City' AND c.name = 'Premier League'
    """)
    city_result = c.fetchone()
    city_strength = city_result[0] if city_result else None
    
    if liverpool_strength and city_strength:
        print(f"   Liverpool vs Manchester City (Anfield)")
        print(f"   Liverpool strength: {liverpool_strength:.3f}")
        print(f"   Manchester City strength: {city_strength:.3f}")
        print()
        
        odds_data = calculate_betting_odds(liverpool_strength, city_strength, "home")
        
        print("   MATCH OUTCOME ODDS:")
        for outcome, data in odds_data['match_outcome'].items():
            print(f"   {outcome.replace('_', ' ').title()}: {data['probability']}% (odds: {data['odds']})")
        
        print(f"\n   GOALS MARKET:")
        for market, data in odds_data['goals_market'].items():
            print(f"   {market.replace('_', ' ').title()}: {data['probability']}% (odds: {data['odds']})")
        
        print(f"\n   BOTH TEAMS TO SCORE:")
        for market, data in odds_data['btts_market'].items():
            print(f"   BTTS {market.title()}: {data['probability']}% (odds: {data['odds']})")
        
        print(f"\n   ⏱️ Calculation time: {odds_data['calculation_time_ms']}ms")
        print()
    
    # TEST 3: CROSS-LEAGUE MATCHUP ODDS
    print("3️⃣ CROSS-LEAGUE MATCHUP - LIVERPOOL VS PSG")
    print("-" * 50)
    
    # Get PSG strength
    c.execute("""
        SELECT cts.team_name, c.name as league, cts.phase1_strength_optimized
        FROM competition_team_strength cts
        JOIN competitions c ON cts.competition_id = c.id
        WHERE cts.team_name LIKE '%Paris Saint Germain%'
        AND cts.phase1_strength_optimized IS NOT NULL
    """)
    
    psg_result = c.fetchone()
    if psg_result and liverpool_strength:
        psg_name, psg_league, psg_strength = psg_result
        
        print(f"   Liverpool vs {psg_name} (Neutral venue)")
        print(f"   Liverpool (Premier League): {liverpool_strength:.3f}")
        print(f"   {psg_name} ({psg_league}): {psg_strength:.3f}")
        print()
        
        odds_data = calculate_betting_odds(liverpool_strength, psg_strength, "neutral")
        
        print("   MATCH OUTCOME ODDS:")
        for outcome, data in odds_data['match_outcome'].items():
            print(f"   {outcome.replace('_', ' ').title()}: {data['probability']}% (odds: {data['odds']})")
        
        print(f"\n   ⏱️ Calculation time: {odds_data['calculation_time_ms']}ms")
        print()
    
    # TEST 4: MULTIPLE MATCHUP PERFORMANCE TEST
    print("4️⃣ PERFORMANCE BENCHMARK - MULTIPLE MATCHUPS")
    print("-" * 50)
    
    # Test 10 random matchups for performance
    test_matchups = [
        ("Liverpool", "Manchester City"),
        ("Real Madrid", "Barcelona"),
        ("Bayern München", "Borussia Dortmund"),
        ("Inter", "Juventus"),
        ("Arsenal", "Chelsea"),
        ("Atlético Madrid", "Valencia"),
        ("AC Milan", "Atalanta"),
        ("RB Leipzig", "Bayer Leverkusen"),
        ("Monaco", "Marseille"),
        ("Tottenham Hotspur", "Manchester United")
    ]
    
    total_time = 0
    successful_calculations = 0
    
    for home_team, away_team in test_matchups:
        # Get team strengths
        c.execute("""
            SELECT cts.phase1_strength_optimized
            FROM competition_team_strength cts
            WHERE cts.team_name = ? AND cts.phase1_strength_optimized IS NOT NULL
        """, (home_team,))
        home_result = c.fetchone()
        
        c.execute("""
            SELECT cts.phase1_strength_optimized
            FROM competition_team_strength cts
            WHERE cts.team_name = ? AND cts.phase1_strength_optimized IS NOT NULL
        """, (away_team,))
        away_result = c.fetchone()
        
        if home_result and away_result:
            home_strength = home_result[0]
            away_strength = away_result[0]
            
            start_time = time.time()
            odds_data = calculate_betting_odds(home_strength, away_strength, "home")
            calc_time = time.time() - start_time
            
            total_time += calc_time
            successful_calculations += 1
            
            print(f"   {home_team} vs {away_team}: {calc_time*1000:.1f}ms")
    
    avg_time = (total_time / successful_calculations) * 1000 if successful_calculations > 0 else 0
    print(f"\n   Successful calculations: {successful_calculations}/{len(test_matchups)}")
    print(f"   Average calculation time: {avg_time:.1f}ms")
    print(f"   Performance target (<2000ms): {'✅ PASS' if avg_time < 2000 else '❌ FAIL'}")
    print()
    
    # TEST 5: ODDS VALIDATION
    print("5️⃣ BETTING ODDS VALIDATION")
    print("-" * 50)
    
    # Initialize default values
    all_odds = []
    min_odds = 1.0
    max_odds = 10.0
    prob_check = False
    
    if liverpool_strength and city_strength:
        odds_data = calculate_betting_odds(liverpool_strength, city_strength, "home")
        
        # Check all odds are realistic (between 1.01 and 50.0)
        all_odds = []
        
        for market_data in [odds_data['match_outcome'], odds_data['goals_market'], odds_data['btts_market']]:
            for outcome_data in market_data.values():
                if outcome_data['odds']:
                    all_odds.append(outcome_data['odds'])
        
        if all_odds:
            min_odds = min(all_odds)
            max_odds = max(all_odds)
        
        print(f"   Total odds generated: {len(all_odds)}")
        print(f"   Odds range: {min_odds} - {max_odds}")
        print(f"   Realistic range (1.01-50.0): {'✅ PASS' if 1.01 <= min_odds and max_odds <= 50.0 else '❌ FAIL'}")
        
        # Check probabilities sum to ~100%
        total_match_prob = sum(data['probability'] for data in odds_data['match_outcome'].values())
        total_goals_prob = sum(data['probability'] for data in odds_data['goals_market'].values())
        total_btts_prob = sum(data['probability'] for data in odds_data['btts_market'].values())
        
        print(f"   Match outcome probabilities: {total_match_prob:.1f}%")
        print(f"   Goals market probabilities: {total_goals_prob:.1f}%")
        print(f"   BTTS market probabilities: {total_btts_prob:.1f}%")
        
        prob_check = all(99.0 <= total <= 101.0 for total in [total_match_prob, total_goals_prob, total_btts_prob])
        print(f"   Probability totals (~100%): {'✅ PASS' if prob_check else '❌ FAIL'}")
    else:
        print("   ⚠️ Could not find Liverpool and Manchester City strength data")
    print()
    
    # TEST 6: API ENDPOINT SIMULATION
    print("6️⃣ API ENDPOINT SIMULATION")
    print("-" * 50)
    
    def simulate_analyze_endpoint(team1, team2):
        """Simulate the /analyze endpoint with odds generation"""
        
        # Get team strengths
        c.execute("""
            SELECT cts.phase1_strength_optimized
            FROM competition_team_strength cts
            WHERE cts.team_name = ?
        """, (team1,))
        team1_result = c.fetchone()
        
        c.execute("""
            SELECT cts.phase1_strength_optimized
            FROM competition_team_strength cts
            WHERE cts.team_name = ?
        """, (team2,))
        team2_result = c.fetchone()
        
        if not team1_result or not team2_result:
            return None
        
        team1_strength = team1_result[0]
        team2_strength = team2_result[0]
        
        # Generate odds
        odds_data = calculate_betting_odds(team1_strength, team2_strength, "home")
        
        # Format like API response
        api_response = {
            'status': 'success',
            'teams': {
                'home': team1,
                'away': team2
            },
            'strength_scores': {
                'home': team1_strength,
                'away': team2_strength
            },
            'betting_odds': odds_data,
            'timestamp': datetime.now().isoformat()
        }
        
        return api_response
    
    # Test API simulation
    api_test = simulate_analyze_endpoint("Liverpool", "Chelsea")
    if api_test:
        print("   ✅ API endpoint simulation successful")
        print(f"   Response keys: {list(api_test.keys())}")
        print(f"   Betting odds generated: {len(api_test['betting_odds'])} markets")
        print(f"   Liverpool vs Chelsea odds:")
        for outcome, data in api_test['betting_odds']['match_outcome'].items():
            print(f"      {outcome.replace('_', ' ').title()}: {data['odds']}")
    else:
        print("   ❌ API endpoint simulation failed")
    print()
    
    # FINAL VERDICT
    print("🎯 PHASE 2 VERIFICATION VERDICT")
    print("=" * 50)
    
    checks = [
        (successful_calculations >= 8, "Multi-market odds generation working"),
        (avg_time < 2000, "Performance under 2 seconds"),
        (min_odds >= 1.01 and max_odds <= 50.0, "Realistic odds range"),
        (prob_check, "Probability mathematics correct"),
        (api_test is not None, "API endpoint ready"),
        (len(all_odds) >= 6, "Multiple betting markets supported")
    ]
    
    passed_checks = sum(1 for check, _ in checks if check)
    
    for check, description in checks:
        status = "✅ PASS" if check else "❌ FAIL"
        print(f"   {status} {description}")
    
    print(f"\n   Overall Status: {passed_checks}/{len(checks)} checks passed")
    
    if passed_checks == len(checks):
        print("   🎉 PHASE 2 VERIFICATION: ✅ COMPLETE SUCCESS")
        print("   Betting odds generation system is fully operational!")
    elif passed_checks >= len(checks) - 1:
        print("   ⚠️ PHASE 2 VERIFICATION: 🟡 MOSTLY COMPLETE")
        print("   Minor issues detected - system largely functional.")
    else:
        print("   ❌ PHASE 2 VERIFICATION: ❌ NEEDS WORK")
        print("   Significant issues detected - odds system needs attention.")
    
    conn.close()
    
    print(f"\n📅 Phase 2 verification completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    run_phase2_verification()