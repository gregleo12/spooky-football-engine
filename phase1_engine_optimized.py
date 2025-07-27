#!/usr/bin/env python3
"""
Phase 1 Calculation Engine - Optimized Implementation
Temporarily redistributes Fatigue Factor weight to maximize calculation value
"""
import sqlite3
from datetime import datetime
from collections import defaultdict

def calculate_phase1_strength_optimized():
    """
    Calculate team strength using optimized 11-parameter system
    
    OPTIMIZATION: Fatigue Factor temporarily redistributed during off-season
    - Original Fatigue Factor: 3% (currently all teams = 0.5, no discrimination)
    - Redistributed: +1.5% to ELO, +1.5% to Form (our most reliable parameters)
    - Will revert to original weights when fixture data becomes available
    
    Optimized Phase 1 Blueprint (100% weights):
    
    Core Team Strength (64.5%):
    - ELO Score: 21.5% (was 20%)
    - Squad Value Score: 15% 
    - Form Score: 21.5% (was 20%)
    - Squad Depth Score: 10%
    - Offensive Rating: 5%
    - Defensive Rating: 5%
    - Home Advantage: 8%
    
    Advanced Parameters (14%):
    - Motivation Factor: 7%
    - Tactical Matchup: 5% 
    - Key Player Availability: 2%
    
    Temporarily Inactive (0%):
    - Fatigue Factor: 0% (was 3% - will reactivate when fixture data available)
    
    Total: 100% meaningful calculation
    """
    
    print("🚀 PHASE 1 CALCULATION ENGINE - OPTIMIZED FOR OFF-SEASON")
    print("=" * 80)
    print("Implementing optimized Phase 1 blueprint with meaningful 100% weights")
    print("Fatigue Factor (3%) temporarily redistributed to ELO (+1.5%) and Form (+1.5%)")
    print("Will revert when reliable fixture data becomes available")
    print()
    
    # Optimized Phase 1 parameter weights (total = 100%)
    weights = {
        'elo_score': 0.215,                  # 21.5% (was 20% + 1.5% from fatigue)
        'squad_value_score': 0.15,           # 15% (unchanged)
        'form_score': 0.215,                 # 21.5% (was 20% + 1.5% from fatigue)
        'squad_depth_score': 0.10,           # 10% (unchanged)
        'offensive_rating': 0.05,            # 5% (unchanged)
        'defensive_rating': 0.05,            # 5% (unchanged)
        'home_advantage': 0.08,              # 8% (unchanged)
        'motivation_factor': 0.07,           # 7% (unchanged)
        'tactical_matchup': 0.05,            # 5% (unchanged)
        'fatigue_factor': 0.00,              # 0% (temporarily inactive)
        'key_player_availability': 0.02      # 2% (unchanged)
    }
    
    print(f"📊 Optimized Phase 1 Parameter Weights:")
    print("   ACTIVE PARAMETERS:")
    for param, weight in weights.items():
        if weight > 0:
            change = ""
            if param == 'elo_score':
                change = " (+1.5% from fatigue)"
            elif param == 'form_score':
                change = " (+1.5% from fatigue)"
            print(f"   {param}: {weight*100:.1f}%{change}")
    
    print("   TEMPORARILY INACTIVE:")
    print("   fatigue_factor: 0.0% (no discriminating data available)")
    
    print(f"   Total Coverage: {sum(weights.values())*100:.1f}%")
    print()
    
    conn = sqlite3.connect("db/football_strength.db")
    c = conn.cursor()
    
    # Get all competitions
    c.execute("SELECT id, name FROM competitions WHERE type = 'domestic_league' ORDER BY name")
    competitions = c.fetchall()
    
    all_teams_data = []
    
    for comp_id, comp_name in competitions:
        print(f"🏆 Processing {comp_name}")
        print("-" * 40)
        
        # Get teams with all Phase 1 parameters
        query = """
            SELECT 
                cts.team_name,
                cts.elo_score,
                cts.elo_normalized,
                cts.squad_value_score,
                cts.squad_value_normalized,
                cts.form_score,
                cts.form_normalized,
                cts.squad_depth_score,
                cts.squad_depth_normalized,
                cts.offensive_rating,
                cts.offensive_normalized,
                cts.defensive_rating,
                cts.defensive_normalized,
                cts.home_advantage,
                cts.home_advantage_normalized,
                cts.motivation_factor,
                cts.motivation_normalized,
                cts.tactical_matchup,
                cts.tactical_normalized,
                cts.fatigue_factor,
                cts.fatigue_normalized,
                cts.key_player_availability,
                cts.availability_normalized
            FROM competition_team_strength cts
            WHERE cts.competition_id = ? AND cts.season = '2024'
            AND cts.team_name IS NOT NULL
            ORDER BY cts.team_name
        """
        
        c.execute(query, (comp_id,))
        teams = c.fetchall()
        
        if not teams:
            print(f"   ⚠️ No teams found for {comp_name}")
            continue
        
        competition_results = []
        
        for team_data in teams:
            (team_name, elo_raw, elo_norm, squad_val_raw, squad_val_norm,
             form_raw, form_norm, depth_raw, depth_norm, off_raw, off_norm,
             def_raw, def_norm, home_raw, home_norm, motiv_raw, motiv_norm,
             tactical_raw, tactical_norm, fatigue_raw, fatigue_norm,
             availability_raw, availability_norm) = team_data
            
            # Calculate optimized Phase 1 strength using normalized scores
            phase1_strength_optimized = 0.0
            missing_params = []
            
            # Core parameters (with optimized weights)
            if elo_norm is not None:
                phase1_strength_optimized += elo_norm * weights['elo_score']
            else:
                missing_params.append('elo')
                
            if squad_val_norm is not None:
                phase1_strength_optimized += squad_val_norm * weights['squad_value_score']
            else:
                missing_params.append('squad_value')
                
            if form_norm is not None:
                phase1_strength_optimized += form_norm * weights['form_score']
            else:
                missing_params.append('form')
                
            if depth_norm is not None:
                phase1_strength_optimized += depth_norm * weights['squad_depth_score']
            else:
                missing_params.append('squad_depth')
            
            if off_norm is not None:
                phase1_strength_optimized += off_norm * weights['offensive_rating']
            else:
                missing_params.append('offensive')
                
            if def_norm is not None:
                phase1_strength_optimized += def_norm * weights['defensive_rating']
            else:
                missing_params.append('defensive')
                
            if home_norm is not None:
                phase1_strength_optimized += home_norm * weights['home_advantage']
            else:
                missing_params.append('home_advantage')
            
            # Advanced Phase 1 parameters
            if motiv_norm is not None:
                phase1_strength_optimized += motiv_norm * weights['motivation_factor']
            else:
                missing_params.append('motivation')
                
            if tactical_norm is not None:
                phase1_strength_optimized += tactical_norm * weights['tactical_matchup']
            else:
                missing_params.append('tactical')
                
            # Fatigue factor temporarily disabled (weight = 0)
            # if fatigue_norm is not None:
            #     phase1_strength_optimized += fatigue_norm * weights['fatigue_factor']
                
            if availability_norm is not None:
                phase1_strength_optimized += availability_norm * weights['key_player_availability']
            else:
                missing_params.append('availability')
            
            # Calculate completion percentage (out of active parameters)
            active_params = 10  # 11 total - 1 inactive fatigue
            available_params = active_params - len(missing_params)
            completion_pct = (available_params / active_params) * 100
            
            team_result = {
                'team_name': team_name,
                'competition': comp_name,
                'phase1_strength_optimized': round(phase1_strength_optimized, 3),
                'completion_pct': completion_pct,
                'missing_params': missing_params,
                'raw_values': {
                    'elo': elo_raw,
                    'squad_value': squad_val_raw,
                    'form': form_raw,
                    'squad_depth': depth_raw,
                    'offensive': off_raw,
                    'defensive': def_raw,
                    'home_advantage': home_raw,
                    'motivation': motiv_raw,
                    'tactical': tactical_raw,
                    'fatigue': fatigue_raw,
                    'availability': availability_raw
                },
                'normalized_values': {
                    'elo': elo_norm,
                    'squad_value': squad_val_norm,
                    'form': form_norm,
                    'squad_depth': depth_norm,
                    'offensive': off_norm,
                    'defensive': def_norm,
                    'home_advantage': home_norm,
                    'motivation': motiv_norm,
                    'tactical': tactical_norm,
                    'fatigue': fatigue_norm,
                    'availability': availability_norm
                }
            }
            
            competition_results.append(team_result)
            all_teams_data.append(team_result)
        
        # Sort by optimized Phase 1 strength (descending)
        competition_results.sort(key=lambda x: x['phase1_strength_optimized'], reverse=True)
        
        # Show top 5 teams in competition
        print(f"📈 Top 5 teams in {comp_name} (optimized):")
        for i, team in enumerate(competition_results[:5], 1):
            print(f"   {i}. {team['team_name']}: {team['phase1_strength_optimized']:.3f} ({team['completion_pct']:.0f}% complete)")
            if team['missing_params']:
                print(f"      Missing: {', '.join(team['missing_params'])}")
        
        # Calculate competition statistics
        strengths = [team['phase1_strength_optimized'] for team in competition_results]
        completions = [team['completion_pct'] for team in competition_results]
        
        print(f"   Range: {min(strengths):.3f} - {max(strengths):.3f}")
        print(f"   Avg completion: {sum(completions)/len(completions):.1f}%")
        print()
    
    # Add optimized Phase 1 completion column if it doesn't exist
    try:
        c.execute("ALTER TABLE competition_team_strength ADD COLUMN phase1_strength_optimized REAL")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Update database with optimized Phase 1 strength scores
    print("💾 Updating database with optimized Phase 1 scores...")
    
    for team in all_teams_data:
        c.execute("""
            UPDATE competition_team_strength 
            SET phase1_strength_optimized = ?
            WHERE team_name = ? AND season = '2024'
        """, (
            team['phase1_strength_optimized'],
            team['team_name']
        ))
    
    conn.commit()
    
    # Global optimized Phase 1 rankings
    print("🏆 GLOBAL OPTIMIZED PHASE 1 RANKINGS")
    print("=" * 80)
    
    # Sort all teams by optimized Phase 1 strength
    all_teams_data.sort(key=lambda x: x['phase1_strength_optimized'], reverse=True)
    
    # Show top 20 globally
    print("Top 20 teams globally (optimized Phase 1 strength):")
    for i, team in enumerate(all_teams_data[:20], 1):
        print(f"{i:2d}. {team['team_name']} ({team['competition']}): {team['phase1_strength_optimized']:.3f}")
        if team['missing_params']:
            print(f"     Missing: {', '.join(team['missing_params'])}")
    
    # Optimization impact analysis
    print(f"\n📊 OPTIMIZATION IMPACT ANALYSIS")
    print("=" * 80)
    
    total_teams = len(all_teams_data)
    complete_teams = len([t for t in all_teams_data if t['completion_pct'] == 100])
    avg_completion = sum(t['completion_pct'] for t in all_teams_data) / total_teams
    
    print(f"Total teams analyzed: {total_teams}")
    print(f"Teams with 100% active data: {complete_teams} ({complete_teams/total_teams*100:.1f}%)")
    print(f"Average completion (active parameters): {avg_completion:.1f}%")
    
    print(f"\n🔄 REACTIVATION PLAN:")
    print("When reliable fixture data becomes available:")
    print("1. Revert ELO weight: 21.5% → 20.0%")
    print("2. Revert Form weight: 21.5% → 20.0%") 
    print("3. Activate Fatigue Factor: 0% → 3.0%")
    print("4. Update phase1_engine.py with original weights")
    print("5. Run fatigue_factor_agent.py to populate real data")
    
    conn.close()
    
    print(f"\n✅ Optimized Phase 1 calculation engine complete!")
    print(f"Implementing {sum(w for w in weights.values() if w > 0)*100:.1f}% meaningful calculation")
    print("Ready to revert to full 11-parameter system when fixture data available")
    
    return all_teams_data

if __name__ == "__main__":
    calculate_phase1_strength_optimized()