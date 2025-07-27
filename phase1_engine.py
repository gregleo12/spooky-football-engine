#!/usr/bin/env python3
"""
Phase 1 Calculation Engine - Complete Implementation
Calculates team strength using all 11 Phase 1 parameters with proper weighting
"""
import sqlite3
from datetime import datetime
from collections import defaultdict

def calculate_phase1_strength():
    """
    Calculate team strength using all 11 Phase 1 parameters
    
    Complete Phase 1 Blueprint (100% weights):
    
    Core Team Strength (62%):
    - ELO Score: 20%
    - Squad Value Score: 15% 
    - Form Score: 20%
    - Squad Depth Score: 10%
    - Offensive Rating: 5%
    - Defensive Rating: 5%
    - Home Advantage: 8%
    
    Advanced Parameters (17%):
    - Motivation Factor: 7%
    - Tactical Matchup: 5% 
    - Fatigue Factor: 3%
    - Key Player Availability: 2%
    
    Total: 100% complete Phase 1 system
    """
    
    print("🚀 PHASE 1 CALCULATION ENGINE - COMPLETE IMPLEMENTATION")
    print("=" * 70)
    print("Implementing complete Phase 1 blueprint with 11 parameters")
    print("Coverage: 100% of Phase 1 system architecture")
    print()
    
    # Complete Phase 1 parameter weights (total = 100%)
    weights = {
        'elo_score': 0.20,                   # 20% - Match-based team strength
        'squad_value_score': 0.15,           # 15% - Market-based team quality  
        'form_score': 0.20,                  # 20% - Recent performance
        'squad_depth_score': 0.10,           # 10% - Squad size and depth
        'offensive_rating': 0.05,            # 5% - Goals scored performance
        'defensive_rating': 0.05,            # 5% - Goals conceded performance  
        'home_advantage': 0.08,              # 8% - Home vs away performance
        'motivation_factor': 0.07,           # 7% - League position motivation
        'tactical_matchup': 0.05,            # 5% - Playing style analysis
        'fatigue_factor': 0.03,              # 3% - Fixture congestion
        'key_player_availability': 0.02      # 2% - Injury/suspension impact
    }
    
    print(f"📊 Phase 1 Parameter Weights:")
    for param, weight in weights.items():
        print(f"   {param}: {weight*100:.0f}%")
    print(f"   Total Coverage: {sum(weights.values())*100:.0f}%")
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
            
            # Use normalized scores for within-competition ranking
            # Use raw scores for cross-competition comparison
            
            # Calculate Phase 1 strength using normalized scores
            phase1_strength = 0.0
            missing_params = []
            
            # Core parameters
            if elo_norm is not None:
                phase1_strength += elo_norm * weights['elo_score']
            else:
                missing_params.append('elo')
                
            if squad_val_norm is not None:
                phase1_strength += squad_val_norm * weights['squad_value_score']
            else:
                missing_params.append('squad_value')
                
            if form_norm is not None:
                phase1_strength += form_norm * weights['form_score']
            else:
                missing_params.append('form')
                
            if depth_norm is not None:
                phase1_strength += depth_norm * weights['squad_depth_score']
            else:
                missing_params.append('squad_depth')
            
            if off_norm is not None:
                phase1_strength += off_norm * weights['offensive_rating']
            else:
                missing_params.append('offensive')
                
            if def_norm is not None:
                phase1_strength += def_norm * weights['defensive_rating']
            else:
                missing_params.append('defensive')
                
            if home_norm is not None:
                phase1_strength += home_norm * weights['home_advantage']
            else:
                missing_params.append('home_advantage')
            
            # Advanced Phase 1 parameters
            if motiv_norm is not None:
                phase1_strength += motiv_norm * weights['motivation_factor']
            else:
                missing_params.append('motivation')
                
            if tactical_norm is not None:
                phase1_strength += tactical_norm * weights['tactical_matchup']
            else:
                missing_params.append('tactical')
                
            if fatigue_norm is not None:
                phase1_strength += fatigue_norm * weights['fatigue_factor']
            else:
                missing_params.append('fatigue')
                
            if availability_norm is not None:
                phase1_strength += availability_norm * weights['key_player_availability']
            else:
                missing_params.append('availability')
            
            # Calculate completion percentage
            available_params = 11 - len(missing_params)
            completion_pct = (available_params / 11) * 100
            
            team_result = {
                'team_name': team_name,
                'competition': comp_name,
                'phase1_strength': round(phase1_strength, 3),
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
        
        # Sort by Phase 1 strength (descending)
        competition_results.sort(key=lambda x: x['phase1_strength'], reverse=True)
        
        # Show top 5 teams in competition
        print(f"📈 Top 5 teams in {comp_name}:")
        for i, team in enumerate(competition_results[:5], 1):
            print(f"   {i}. {team['team_name']}: {team['phase1_strength']:.3f} ({team['completion_pct']:.0f}% complete)")
            if team['missing_params']:
                print(f"      Missing: {', '.join(team['missing_params'])}")
        
        # Calculate competition statistics
        strengths = [team['phase1_strength'] for team in competition_results]
        completions = [team['completion_pct'] for team in competition_results]
        
        print(f"   Range: {min(strengths):.3f} - {max(strengths):.3f}")
        print(f"   Avg completion: {sum(completions)/len(completions):.1f}%")
        print()
    
    # Add Phase 1 completion columns if they don't exist
    try:
        c.execute("ALTER TABLE competition_team_strength ADD COLUMN phase1_strength REAL")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        c.execute("ALTER TABLE competition_team_strength ADD COLUMN phase1_completion REAL")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Update database with Phase 1 strength scores
    print("💾 Updating database with Phase 1 scores...")
    
    for team in all_teams_data:
        c.execute("""
            UPDATE competition_team_strength 
            SET phase1_strength = ?, phase1_completion = ?
            WHERE team_name = ? AND season = '2024'
        """, (
            team['phase1_strength'],
            team['completion_pct'],
            team['team_name']
        ))
    
    conn.commit()
    
    # Global Phase 1 rankings
    print("🏆 GLOBAL PHASE 1 RANKINGS")
    print("=" * 60)
    
    # Sort all teams by Phase 1 strength
    all_teams_data.sort(key=lambda x: x['phase1_strength'], reverse=True)
    
    # Show top 20 globally
    print("Top 20 teams globally (Phase 1 strength):")
    for i, team in enumerate(all_teams_data[:20], 1):
        print(f"{i:2d}. {team['team_name']} ({team['competition']}): {team['phase1_strength']:.3f}")
        if team['missing_params']:
            print(f"     Missing: {', '.join(team['missing_params'])}")
    
    # Phase 1 completion statistics
    print(f"\n📊 PHASE 1 IMPLEMENTATION STATUS")
    print("=" * 60)
    
    total_teams = len(all_teams_data)
    complete_teams = len([t for t in all_teams_data if t['completion_pct'] == 100])
    avg_completion = sum(t['completion_pct'] for t in all_teams_data) / total_teams
    
    print(f"Total teams analyzed: {total_teams}")
    print(f"Teams with 100% Phase 1 data: {complete_teams} ({complete_teams/total_teams*100:.1f}%)")
    print(f"Average completion: {avg_completion:.1f}%")
    
    # Parameter availability analysis
    param_counts = defaultdict(int)
    for team in all_teams_data:
        for param in team['missing_params']:
            param_counts[param] += 1
    
    if param_counts:
        print(f"\nMissing parameter analysis:")
        for param, count in sorted(param_counts.items(), key=lambda x: x[1], reverse=True):
            missing_pct = count / total_teams * 100
            print(f"   {param}: {count} teams missing ({missing_pct:.1f}%)")
    
    # Top performing teams by parameter
    print(f"\n🥇 TOP PERFORMERS BY PARAMETER")
    print("-" * 40)
    
    for param in ['elo', 'squad_value', 'form', 'squad_depth', 'offensive', 'defensive', 'home_advantage', 'motivation', 'tactical', 'fatigue', 'availability']:
        # Find team with highest raw value for this parameter
        teams_with_param = [t for t in all_teams_data if t['raw_values'][param] is not None]
        if teams_with_param:
            best_team = max(teams_with_param, key=lambda x: x['raw_values'][param])
            print(f"{param.replace('_', ' ').title()}: {best_team['team_name']} ({best_team['raw_values'][param]:.3f})")
    
    conn.close()
    
    print(f"\n✅ Phase 1 calculation engine complete!")
    print(f"Implementing {sum(weights.values())*100:.0f}% complete Phase 1 system with all 11 parameters")
    
    return all_teams_data

if __name__ == "__main__":
    calculate_phase1_strength()