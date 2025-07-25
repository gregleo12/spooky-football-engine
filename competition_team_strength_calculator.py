#!/usr/bin/env python3
"""
Competition-Aware Team Strength Calculator

Calculates final team strength scores for each domestic league using:
- ELO Score: 18% weight (normalized within competition)
- Squad Value Score: 15% weight (normalized within competition)  
- Form Score: 5% weight (normalized within competition)
- Squad Depth Score: 2% weight (normalized within competition)
- H2H Performance: 4% weight (normalized within competition)
- Scoring Patterns: 3% weight (normalized within competition)

Total: 47% of full blueprint (53% future expansion)
"""
import sqlite3
from datetime import datetime
import sys
import os

# Add shared utilities to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents', 'shared'))
from competition_normalizer import update_competition_metric

class CompetitionStrengthCalculator:
    def __init__(self):
        self.weights = {
            'elo': 0.18,        # 18% - Match-based team strength
            'squad_value': 0.15, # 15% - Market-based team quality
            'form': 0.05,       # 5% - Recent performance
            'squad_depth': 0.02, # 2% - Squad size and depth
            'h2h_performance': 0.04,  # 4% - Historical head-to-head performance
            'scoring_patterns': 0.03  # 3% - Goal-scoring patterns and trends
        }
        self.total_weight = sum(self.weights.values())  # 47% of full system (up from 44%)
        
    def connect_database(self):
        """Connect to the football strength database"""
        return sqlite3.connect("db/football_strength.db")
    
    def get_competition_teams(self, competition_name):
        """Get all teams and their normalized metrics for a competition"""
        conn = self.connect_database()
        c = conn.cursor()
        
        c.execute("""
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
                cts.h2h_performance,
                cts.h2h_normalized,
                cts.scoring_patterns,
                cts.scoring_normalized,
                cts.team_id,
                cts.competition_id
            FROM competition_team_strength cts
            JOIN competitions c ON cts.competition_id = c.id
            WHERE c.name = ?
            ORDER BY cts.team_name
        """, (competition_name,))
        
        teams = c.fetchall()
        conn.close()
        
        return teams
    
    def calculate_team_strength(self, team_data):
        """Calculate weighted team strength score using normalized values"""
        (team_name, elo_raw, elo_norm, squad_val_raw, squad_val_norm, 
         form_raw, form_norm, depth_raw, depth_norm, h2h_raw, h2h_norm,
         scoring_raw, scoring_norm, team_id, comp_id) = team_data
        
        # Check for missing data
        missing_data = []
        if elo_norm is None:
            missing_data.append("ELO")
        if squad_val_norm is None:
            missing_data.append("Squad Value")
        if form_norm is None:
            missing_data.append("Form")
        if depth_norm is None:
            missing_data.append("Squad Depth")
        if h2h_norm is None:
            missing_data.append("H2H Performance")
        if scoring_norm is None:
            missing_data.append("Scoring Patterns")
        
        if missing_data:
            return None, missing_data
        
        # Calculate weighted strength using normalized values (0-1 scale)
        strength_score = (
            (elo_norm * self.weights['elo']) +
            (squad_val_norm * self.weights['squad_value']) +
            (form_norm * self.weights['form']) +
            (depth_norm * self.weights['squad_depth']) +
            (h2h_norm * self.weights['h2h_performance']) +
            (scoring_norm * self.weights['scoring_patterns'])
        )
        
        # Convert to percentage (0-47% since we're using 47% of full system)
        strength_percentage = strength_score * 100
        
        return strength_percentage, []
    
    def calculate_competition_strength(self, competition_name):
        """Calculate strength scores for all teams in a competition"""
        print(f"\n🏆 {competition_name.upper()} TEAM STRENGTH CALCULATION")
        print("=" * 60)
        
        teams = self.get_competition_teams(competition_name)
        
        if not teams:
            print(f"❌ No teams found for {competition_name}")
            return []
        
        results = []
        incomplete_teams = []
        
        for team_data in teams:
            team_name = team_data[0]
            strength_score, missing_data = self.calculate_team_strength(team_data)
            
            if strength_score is not None:
                results.append({
                    'team_name': team_name,
                    'strength_score': strength_score,
                    'elo_raw': team_data[1],
                    'elo_normalized': team_data[2],
                    'squad_value_raw': team_data[3],
                    'squad_value_normalized': team_data[4],
                    'form_raw': team_data[5],
                    'form_normalized': team_data[6],
                    'squad_depth_raw': team_data[7],
                    'squad_depth_normalized': team_data[8],
                    'h2h_raw': team_data[9],
                    'h2h_normalized': team_data[10],
                    'scoring_raw': team_data[11],
                    'scoring_normalized': team_data[12],
                    'team_id': team_data[13],
                    'competition_id': team_data[14]
                })
            else:
                incomplete_teams.append((team_name, missing_data))
        
        # Sort by strength score (highest first)
        results.sort(key=lambda x: x['strength_score'], reverse=True)
        
        # Display results
        print(f"📊 Calculated strength for {len(results)} teams")
        if incomplete_teams:
            print(f"⚠️ {len(incomplete_teams)} teams with missing data:")
            for team, missing in incomplete_teams:
                print(f"   • {team}: Missing {', '.join(missing)}")
        
        print(f"\n🏅 {competition_name} TEAM STRENGTH RANKINGS:")
        print("-" * 80)
        print(f"{'Rank':<4} {'Team':<25} {'Strength':<8} {'ELO':<6} {'Squad€':<8} {'Form':<6} {'Depth':<6} {'Scoring':<8}")
        print("-" * 80)
        
        for i, team in enumerate(results, 1):
            rank_emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i:2d}."
            
            print(f"{rank_emoji:<4} {team['team_name']:<25} "
                  f"{team['strength_score']:6.2f}% "
                  f"{team['elo_raw']:6.0f} "
                  f"€{team['squad_value_raw']:6.0f}M "
                  f"{team['form_raw']:5.2f} "
                  f"{team['squad_depth_raw']:5.3f} "
                  f"{team['scoring_raw']:6.1f}")
        
        return results
    
    def save_strength_scores(self, competition_results):
        """Save calculated strength scores back to database"""
        if not competition_results:
            return
        
        conn = self.connect_database()
        c = conn.cursor()
        
        print(f"\n💾 Saving strength scores to database...")
        
        for team in competition_results:
            c.execute("""
                UPDATE competition_team_strength
                SET overall_strength = ?, last_updated = ?
                WHERE team_id = ? AND competition_id = ?
            """, (
                round(team['strength_score'], 3),
                datetime.now(),
                team['team_id'],
                team['competition_id']
            ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Saved {len(competition_results)} strength scores")
    
    def calculate_all_domestic_leagues(self):
        """Calculate strength scores for all domestic leagues"""
        print("🌍 DOMESTIC LEAGUE TEAM STRENGTH CALCULATION")
        print("=" * 80)
        print(f"Using weighted scoring system: ELO({self.weights['elo']*100:.0f}%) + "
              f"Squad Value({self.weights['squad_value']*100:.0f}%) + "
              f"Form({self.weights['form']*100:.0f}%) + "
              f"Squad Depth({self.weights['squad_depth']*100:.0f}%) + "
              f"H2H({self.weights['h2h_performance']*100:.0f}%) + "
              f"Scoring({self.weights['scoring_patterns']*100:.0f}%) = "
              f"{self.total_weight*100:.0f}% Total")
        print("=" * 80)
        
        domestic_leagues = [
            "Premier League",
            "La Liga", 
            "Serie A",
            "Bundesliga",
            "Ligue 1"
        ]
        
        all_results = {}
        
        for league in domestic_leagues:
            results = self.calculate_competition_strength(league)
            if results:
                all_results[league] = results
                self.save_strength_scores(results)
        
        return all_results
    
    def generate_cross_league_comparison(self, all_results):
        """Generate comparison across all leagues using strength scores"""
        print(f"\n🌍 CROSS-LEAGUE STRENGTH COMPARISON")
        print("=" * 80)
        print("Note: These are competition-normalized scores (47% of full system)")
        print("-" * 80)
        
        # Collect all teams across leagues
        all_teams = []
        for league, teams in all_results.items():
            for team in teams:
                all_teams.append({
                    'league': league,
                    'team_name': team['team_name'],
                    'strength_score': team['strength_score'],
                    'elo_raw': team['elo_raw'],
                    'squad_value_raw': team['squad_value_raw']
                })
        
        # Sort by strength score globally
        all_teams.sort(key=lambda x: x['strength_score'], reverse=True)
        
        print(f"🏆 TOP 20 STRONGEST TEAMS ACROSS ALL LEAGUES:")
        print("-" * 80)
        print(f"{'Rank':<4} {'Team':<25} {'League':<15} {'Strength':<8} {'ELO':<6} {'Squad€':<8}")
        print("-" * 80)
        
        for i, team in enumerate(all_teams[:20], 1):
            rank_emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i:2d}."
            
            print(f"{rank_emoji:<4} {team['team_name']:<25} "
                  f"{team['league']:<15} "
                  f"{team['strength_score']:6.2f}% "
                  f"{team['elo_raw']:6.0f} "
                  f"€{team['squad_value_raw']:6.0f}M")
        
        return all_teams
    
    def generate_league_statistics(self, all_results):
        """Generate statistical summary for each league"""
        print(f"\n📊 LEAGUE STRENGTH STATISTICS")
        print("=" * 60)
        
        for league, teams in all_results.items():
            if not teams:
                continue
                
            scores = [team['strength_score'] for team in teams]
            
            avg_strength = sum(scores) / len(scores)
            max_strength = max(scores)
            min_strength = min(scores)
            range_strength = max_strength - min_strength
            
            print(f"\n🏟️ {league}:")
            print(f"   Teams: {len(teams)}")
            print(f"   Average Strength: {avg_strength:.2f}%")
            print(f"   Strongest Team: {teams[0]['team_name']} ({max_strength:.2f}%)")
            print(f"   Weakest Team: {teams[-1]['team_name']} ({min_strength:.2f}%)")
            print(f"   Strength Range: {range_strength:.2f}%")
    
    def run_complete_analysis(self):
        """Run complete team strength analysis for all domestic leagues"""
        print("🚀 STARTING COMPLETE DOMESTIC LEAGUE STRENGTH ANALYSIS")
        print("=" * 80)
        
        # Calculate strength for all leagues
        all_results = self.calculate_all_domestic_leagues()
        
        if not all_results:
            print("❌ No results calculated - check database and data completeness")
            return
        
        # Generate cross-league comparison
        global_rankings = self.generate_cross_league_comparison(all_results)
        
        # Generate league statistics
        self.generate_league_statistics(all_results)
        
        # Final summary
        total_teams = sum(len(teams) for teams in all_results.values())
        print(f"\n🎯 ANALYSIS COMPLETE")
        print("=" * 60)
        print(f"✅ Calculated strength scores for {total_teams} teams across {len(all_results)} leagues")
        print(f"✅ Saved all scores to competition_team_strength.overall_strength")
        print(f"✅ Used {self.total_weight*100:.0f}% of full blueprint (53% future expansion)")
        print(f"✅ All teams ranked within their competitions and globally")
        
        return all_results, global_rankings

def main():
    calculator = CompetitionStrengthCalculator()
    results, global_rankings = calculator.run_complete_analysis()
    return results, global_rankings

if __name__ == "__main__":
    main()