#!/usr/bin/env python3
"""
Dual Strength Scoring System

Creates two types of team strength scores:
1. LOCAL LEAGUE STRENGTH: Normalized within each league (0-100%)
   - Shows relative strength within domestic competition
   - Best team in each league = 100%, worst = 0%
   
2. EUROPEAN STRENGTH: Normalized across all 96 teams (0-100%)
   - Shows absolute strength across all European leagues
   - Best team globally = 100%, worst globally = 0%
   
This allows for both domestic league comparisons and cross-league analysis.
"""
import sqlite3
from datetime import datetime
import sys
import os

# Add shared utilities to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents', 'shared'))

class DualStrengthCalculator:
    def __init__(self):
        self.weights = {
            'elo': 0.18,        # 18% - Match-based team strength
            'squad_value': 0.15, # 15% - Market-based team quality
            'form': 0.05,       # 5% - Recent performance
            'squad_depth': 0.02  # 2% - Squad size and depth
        }
        self.total_weight = sum(self.weights.values())  # 40% of full system
        
    def connect_database(self):
        """Connect to the football strength database"""
        return sqlite3.connect("db/football_strength.db")
    
    def update_database_schema(self):
        """Add new columns for dual strength scores"""
        conn = self.connect_database()
        c = conn.cursor()
        
        print("🗄️ UPDATING DATABASE SCHEMA")
        print("=" * 50)
        
        # Check if columns already exist
        c.execute("PRAGMA table_info(competition_team_strength)")
        columns = [row[1] for row in c.fetchall()]
        
        new_columns = []
        
        if 'local_league_strength' not in columns:
            c.execute("ALTER TABLE competition_team_strength ADD COLUMN local_league_strength REAL")
            new_columns.append('local_league_strength')
        
        if 'european_strength' not in columns:
            c.execute("ALTER TABLE competition_team_strength ADD COLUMN european_strength REAL")
            new_columns.append('european_strength')
        
        conn.commit()
        
        if new_columns:
            print(f"✅ Added columns: {', '.join(new_columns)}")
        else:
            print("✅ Schema already up to date")
        
        conn.close()
        return len(new_columns) > 0
    
    def get_all_teams_data(self):
        """Get all teams and their raw metrics across all competitions"""
        conn = self.connect_database()
        c = conn.cursor()
        
        c.execute("""
            SELECT 
                c.name as competition,
                cts.team_name,
                cts.elo_score,
                cts.squad_value_score,
                cts.form_score,
                cts.squad_depth_score,
                cts.team_id,
                cts.competition_id
            FROM competition_team_strength cts
            JOIN competitions c ON cts.competition_id = c.id
            WHERE c.name IN ('Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1')
            ORDER BY c.name, cts.team_name
        """)
        
        teams = c.fetchall()
        conn.close()
        
        return teams
    
    def calculate_european_strength_scores(self, all_teams):
        """Calculate European strength scores (normalized across all 96 teams)"""
        print("🌍 CALCULATING EUROPEAN STRENGTH SCORES")
        print("=" * 60)
        
        # Filter teams with complete data
        complete_teams = []
        incomplete_teams = []
        
        for team_data in all_teams:
            comp, name, elo, squad_val, form, depth, team_id, comp_id = team_data
            
            if all(x is not None for x in [elo, squad_val, form, depth]):
                complete_teams.append(team_data)
            else:
                missing = [param for param, val in zip(['ELO', 'Squad Value', 'Form', 'Squad Depth'], 
                                                     [elo, squad_val, form, depth]) if val is None]
                incomplete_teams.append((name, comp, missing))
        
        if incomplete_teams:
            print(f"⚠️ {len(incomplete_teams)} teams with missing data (excluded from European scoring):")
            for name, comp, missing in incomplete_teams[:5]:  # Show first 5
                print(f"   • {name} ({comp}): Missing {', '.join(missing)}")
            if len(incomplete_teams) > 5:
                print(f"   ... and {len(incomplete_teams) - 5} more")
        
        print(f"✅ Processing {len(complete_teams)} teams with complete data")
        
        # Extract raw values for European normalization
        elo_values = [team[2] for team in complete_teams]
        squad_values = [team[3] for team in complete_teams]
        form_values = [team[4] for team in complete_teams]
        depth_values = [team[5] for team in complete_teams]
        
        # Calculate European-wide normalization ranges
        elo_min, elo_max = min(elo_values), max(elo_values)
        squad_min, squad_max = min(squad_values), max(squad_values)
        form_min, form_max = min(form_values), max(form_values)
        depth_min, depth_max = min(depth_values), max(depth_values)
        
        print(f"🔢 European Normalization Ranges:")
        print(f"   ELO: {elo_min:.0f} - {elo_max:.0f}")
        print(f"   Squad Value: €{squad_min:.0f}M - €{squad_max:.0f}M")
        print(f"   Form: {form_min:.2f} - {form_max:.2f}")
        print(f"   Squad Depth: {depth_min:.3f} - {depth_max:.3f}")
        
        # Calculate European strength scores
        european_scores = []
        
        for team_data in complete_teams:
            comp, name, elo, squad_val, form, depth, team_id, comp_id = team_data
            
            # Normalize each parameter across all European teams (0-1 scale)
            elo_norm = (elo - elo_min) / (elo_max - elo_min) if elo_max > elo_min else 0
            squad_norm = (squad_val - squad_min) / (squad_max - squad_min) if squad_max > squad_min else 0
            form_norm = (form - form_min) / (form_max - form_min) if form_max > form_min else 0
            depth_norm = (depth - depth_min) / (depth_max - depth_min) if depth_max > depth_min else 0
            
            # Calculate weighted European strength
            european_strength = (
                (elo_norm * self.weights['elo']) +
                (squad_norm * self.weights['squad_value']) +
                (form_norm * self.weights['form']) +
                (depth_norm * self.weights['squad_depth'])
            )
            
            # Convert to percentage (0-40% scale, then scale to 0-100%)
            european_percentage = (european_strength / self.total_weight) * 100
            
            european_scores.append({
                'competition': comp,
                'team_name': name,
                'european_strength': european_percentage,
                'team_id': team_id,
                'competition_id': comp_id,
                'elo_raw': elo,
                'squad_value_raw': squad_val,
                'form_raw': form,
                'depth_raw': depth
            })
        
        # Sort by European strength (highest first)
        european_scores.sort(key=lambda x: x['european_strength'], reverse=True)
        
        return european_scores
    
    def calculate_local_league_scores(self, european_scores):
        """Calculate local league strength scores (normalized within each league)"""
        print(f"\n🏟️ CALCULATING LOCAL LEAGUE STRENGTH SCORES")
        print("=" * 60)
        
        # Group teams by competition
        leagues = {}
        for team in european_scores:
            comp = team['competition']
            if comp not in leagues:
                leagues[comp] = []
            leagues[comp].append(team)
        
        local_scores = []
        
        for league, teams in leagues.items():
            print(f"\n📊 {league} ({len(teams)} teams):")
            
            # Get European strength values for this league
            euro_strengths = [team['european_strength'] for team in teams]
            
            if len(euro_strengths) > 1:
                # Normalize within league (0-100% scale)
                min_strength = min(euro_strengths)
                max_strength = max(euro_strengths)
                range_strength = max_strength - min_strength
                
                print(f"   European range: {min_strength:.2f}% - {max_strength:.2f}%")
                
                for team in teams:
                    if range_strength > 0:
                        local_strength = ((team['european_strength'] - min_strength) / range_strength) * 100
                    else:
                        local_strength = 100.0  # If all teams equal, give them 100%
                    
                    team['local_league_strength'] = local_strength
                    local_scores.append(team)
                
                # Sort by local strength for display
                teams.sort(key=lambda x: x['local_league_strength'], reverse=True)
                
                print(f"   Top 3: ", end="")
                for i, team in enumerate(teams[:3]):
                    print(f"{team['team_name']} ({team['local_league_strength']:.1f}%)", end="")
                    if i < 2 and i < len(teams) - 1:
                        print(", ", end="")
                print()
                
                print(f"   Bottom 1: {teams[-1]['team_name']} ({teams[-1]['local_league_strength']:.1f}%)")
            
            else:
                # Single team - give it 100%
                teams[0]['local_league_strength'] = 100.0
                local_scores.append(teams[0])
        
        return local_scores
    
    def save_dual_scores(self, dual_scores):
        """Save both local and European strength scores to database"""
        print(f"\n💾 SAVING DUAL STRENGTH SCORES")
        print("=" * 50)
        
        conn = self.connect_database()
        c = conn.cursor()
        
        saved_count = 0
        
        for team in dual_scores:
            c.execute("""
                UPDATE competition_team_strength
                SET local_league_strength = ?, 
                    european_strength = ?,
                    last_updated = ?
                WHERE team_id = ? AND competition_id = ?
            """, (
                round(team['local_league_strength'], 2),
                round(team['european_strength'], 2),
                datetime.now(),
                team['team_id'],
                team['competition_id']
            ))
            saved_count += 1
        
        conn.commit()
        conn.close()
        
        print(f"✅ Saved dual scores for {saved_count} teams")
        return saved_count
    
    def generate_comparative_analysis(self, dual_scores):
        """Generate analysis comparing local vs European scores"""
        print(f"\n📊 DUAL SCORING SYSTEM ANALYSIS")
        print("=" * 80)
        
        # Sort by European strength for global rankings
        global_rankings = sorted(dual_scores, key=lambda x: x['european_strength'], reverse=True)
        
        print(f"🌍 TOP 10 EUROPEAN STRENGTH RANKINGS:")
        print("-" * 80)
        print(f"{'Rank':<4} {'Team':<25} {'League':<15} {'European':<8} {'Local':<8} {'Diff':<6}")
        print("-" * 80)
        
        for i, team in enumerate(global_rankings[:10], 1):
            diff = team['local_league_strength'] - team['european_strength']
            rank_emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i:2d}."
            
            print(f"{rank_emoji:<4} {team['team_name']:<25} "
                  f"{team['competition']:<15} "
                  f"{team['european_strength']:6.1f}% "
                  f"{team['local_league_strength']:6.1f}% "
                  f"{diff:+5.1f}")
        
        # Find interesting cases
        print(f"\n🔍 INTERESTING CASES:")
        print("-" * 60)
        
        # Teams with biggest local vs European differences
        biggest_diffs = sorted(dual_scores, key=lambda x: abs(x['local_league_strength'] - x['european_strength']), reverse=True)
        
        print(f"💪 Biggest local league dominance (Local >> European):")
        for team in biggest_diffs[:3]:
            diff = team['local_league_strength'] - team['european_strength']
            if diff > 20:  # Only show if difference > 20%
                print(f"   • {team['team_name']} ({team['competition']}): Local {team['local_league_strength']:.1f}% vs European {team['european_strength']:.1f}% (+{diff:.1f})")
        
        print(f"\n🌍 European powerhouses in weak local position:")
        high_european_low_local = [t for t in dual_scores if t['european_strength'] > 50 and t['local_league_strength'] < 80]
        for team in sorted(high_european_low_local, key=lambda x: x['european_strength'], reverse=True)[:3]:
            diff = team['local_league_strength'] - team['european_strength']
            print(f"   • {team['team_name']} ({team['competition']}): European {team['european_strength']:.1f}% vs Local {team['local_league_strength']:.1f}% ({diff:+.1f})")
        
        # League strength analysis
        print(f"\n🏟️ LEAGUE STRENGTH COMPARISON:")
        print("-" * 60)
        
        leagues = {}
        for team in dual_scores:
            comp = team['competition']
            if comp not in leagues:
                leagues[comp] = []
            leagues[comp].append(team)
        
        league_stats = []
        for league, teams in leagues.items():
            avg_european = sum(t['european_strength'] for t in teams) / len(teams)
            max_european = max(t['european_strength'] for t in teams)
            min_european = min(t['european_strength'] for t in teams)
            
            league_stats.append({
                'league': league,
                'avg_european': avg_european,
                'max_european': max_european,
                'min_european': min_european,
                'range': max_european - min_european,
                'teams': len(teams)
            })
        
        # Sort by average European strength
        league_stats.sort(key=lambda x: x['avg_european'], reverse=True)
        
        print(f"{'League':<15} {'Avg Euro':<8} {'Top Team':<8} {'Range':<8} {'Teams':<6}")
        print("-" * 60)
        for stat in league_stats:
            print(f"{stat['league']:<15} "
                  f"{stat['avg_european']:6.1f}% "
                  f"{stat['max_european']:6.1f}% "
                  f"{stat['range']:6.1f}% "
                  f"{stat['teams']:4d}")
        
        return global_rankings, league_stats
    
    def run_dual_analysis(self):
        """Run complete dual strength scoring analysis"""
        print("🚀 STARTING DUAL STRENGTH SCORING SYSTEM")
        print("=" * 80)
        print("Creating LOCAL LEAGUE (within-league) and EUROPEAN (cross-league) strength scores")
        print("=" * 80)
        
        # Update database schema
        schema_updated = self.update_database_schema()
        
        # Get all team data
        all_teams = self.get_all_teams_data()
        print(f"📊 Retrieved data for {len(all_teams)} teams across 5 leagues")
        
        # Calculate European strength scores (normalized across all teams)
        european_scores = self.calculate_european_strength_scores(all_teams)
        
        # Calculate local league scores (normalized within each league)
        dual_scores = self.calculate_local_league_scores(european_scores)
        
        # Save to database
        saved_count = self.save_dual_scores(dual_scores)
        
        # Generate comparative analysis
        global_rankings, league_stats = self.generate_comparative_analysis(dual_scores)
        
        # Final summary
        print(f"\n🎯 DUAL SCORING SYSTEM COMPLETE")
        print("=" * 60)
        print(f"✅ Created LOCAL LEAGUE scores: 0-100% within each domestic league")
        print(f"✅ Created EUROPEAN scores: 0-100% across all 96 teams")
        print(f"✅ Saved dual scores for {saved_count} teams to database")
        print(f"✅ Generated comparative analysis and rankings")
        print(f"✅ Both scoring systems ready for prediction game integration")
        
        return dual_scores, global_rankings, league_stats

def main():
    calculator = DualStrengthCalculator()
    dual_scores, global_rankings, league_stats = calculator.run_dual_analysis()
    return dual_scores, global_rankings, league_stats

if __name__ == "__main__":
    main()