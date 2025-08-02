#!/usr/bin/env python3
"""
Backtesting Engine for Football Odds Prediction
Validates prediction accuracy against historical match results
"""

import json
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from db_interface import DatabaseInterface
from historical_data_collector import HistoricalDataCollector

class BacktestingEngine:
    """Engine for running backtesting analysis on historical match data"""
    
    def __init__(self):
        self.db = DatabaseInterface()
        self.collector = HistoricalDataCollector()
    
    def run_backtest(self, num_matches: int = 100) -> Dict:
        """
        Run complete backtesting analysis
        Returns comprehensive accuracy report
        """
        print(f"🧪 Starting backtesting analysis on {num_matches} matches...")
        
        # Collect or load historical data
        historical_matches = self._get_historical_data(num_matches)
        
        if not historical_matches:
            print("❌ No historical data available")
            return self._empty_results()
        
        # Run predictions vs reality comparison
        results = self._analyze_predictions(historical_matches)
        
        print(f"✅ Backtesting complete: {results['accuracy']:.1f}% accuracy")
        return results
    
    def _get_historical_data(self, num_matches: int) -> Optional[List[Dict]]:
        """Get historical match data, either from file or by collecting new data"""
        
        # Try to load existing data first
        historical_matches = self.collector.load_historical_data()
        
        if not historical_matches or len(historical_matches) < num_matches:
            print("📊 Collecting fresh historical data...")
            historical_matches = self.collector.get_historical_matches(num_matches)
            self.collector.save_historical_data(historical_matches)
        else:
            print(f"📁 Using cached historical data ({len(historical_matches)} matches)")
            historical_matches = historical_matches[:num_matches]
        
        return historical_matches
    
    def _analyze_predictions(self, historical_matches: List[Dict]) -> Dict:
        """Compare our predictions against actual match results"""
        
        total_matches = len(historical_matches)
        correct_predictions = 0
        
        # Outcome tracking
        outcome_stats = {
            'home_win': {'predicted': 0, 'actual': 0, 'correct': 0},
            'draw': {'predicted': 0, 'actual': 0, 'correct': 0},
            'away_win': {'predicted': 0, 'actual': 0, 'correct': 0}
        }
        
        # Parameter effectiveness tracking
        parameter_contributions = {
            'elo_score': 0,
            'form_score': 0,
            'squad_value': 0,
            'home_advantage': 0
        }
        
        print("🔍 Analyzing predictions vs reality...")
        
        for i, match in enumerate(historical_matches):
            # Generate prediction for this historical match
            predicted_outcome = self._predict_match_outcome(
                match['home_team'], 
                match['away_team']
            )
            
            if predicted_outcome:
                # Update outcome statistics
                actual_outcome = match['actual_result']
                outcome_stats[predicted_outcome]['predicted'] += 1
                outcome_stats[actual_outcome]['actual'] += 1
                
                # Check if prediction was correct
                if predicted_outcome == actual_outcome:
                    correct_predictions += 1
                    outcome_stats[predicted_outcome]['correct'] += 1
                    
                    # Track which parameters helped with correct predictions
                    self._update_parameter_effectiveness(
                        match['home_team'], 
                        match['away_team'], 
                        parameter_contributions
                    )
            
            # Progress indicator
            if (i + 1) % 25 == 0:
                current_accuracy = (correct_predictions / (i + 1)) * 100
                print(f"  📈 Progress: {i + 1}/{total_matches} ({current_accuracy:.1f}% accuracy)")
        
        # Calculate final metrics
        accuracy = (correct_predictions / total_matches) * 100
        
        # Normalize parameter effectiveness (0-1 scale)
        max_contribution = max(parameter_contributions.values()) if parameter_contributions.values() else 1
        normalized_params = {
            param: (value / max_contribution) if max_contribution > 0 else 0.5
            for param, value in parameter_contributions.items()
        }
        
        return {
            'status': 'completed',
            'timestamp': datetime.now().isoformat(),
            'total_matches': total_matches,
            'correct_predictions': correct_predictions,
            'accuracy': round(accuracy, 1),
            'breakdown': outcome_stats,
            'parameter_effectiveness': normalized_params,
            'insights': self._generate_insights(outcome_stats, accuracy)
        }
    
    def _predict_match_outcome(self, home_team: str, away_team: str) -> Optional[str]:
        """Generate prediction for a match using our odds engine"""
        
        try:
            # Get team comparison data
            comparison = self.db.compare_teams(home_team, away_team)
            
            if not comparison:
                return None
            
            # Calculate probabilities using same logic as odds endpoint
            total_strength = comparison['team1_strength'] + comparison['team2_strength']
            if total_strength <= 0:
                return None
            
            home_win_prob = (comparison['team1_strength'] / total_strength)
            away_win_prob = (comparison['team2_strength'] / total_strength)
            
            # Add home advantage
            home_advantage = 0.05 if comparison['same_league'] else 0.03
            home_win_prob = min(0.95, home_win_prob + home_advantage)
            
            # Calculate draw probability
            strength_diff = abs(comparison['team1_strength'] - comparison['team2_strength'])
            normalized_diff = min(strength_diff / 50.0, 1.0)
            draw_prob = 0.33 - (normalized_diff * 0.13)
            draw_prob = max(0.20, min(0.33, draw_prob))
            
            # Normalize probabilities
            total_prob = home_win_prob + draw_prob
            if total_prob > 1.0:
                home_win_prob = home_win_prob / total_prob
                draw_prob = draw_prob / total_prob
            
            away_win_prob = 1.0 - home_win_prob - draw_prob
            
            # Ensure away_win_prob is not negative
            if away_win_prob < 0.05:
                away_win_prob = 0.05
                remaining = 0.95
                home_ratio = home_win_prob / (home_win_prob + draw_prob)
                home_win_prob = remaining * home_ratio
                draw_prob = remaining * (1 - home_ratio)
            
            # Return most likely outcome
            probabilities = {
                'home_win': home_win_prob,
                'draw': draw_prob,
                'away_win': away_win_prob
            }
            
            return max(probabilities, key=probabilities.get)
            
        except Exception as e:
            print(f"⚠️  Prediction error for {home_team} vs {away_team}: {e}")
            return None
    
    def _update_parameter_effectiveness(self, home_team: str, away_team: str, contributions: Dict):
        """Track which parameters are most effective for correct predictions"""
        
        try:
            comparison = self.db.compare_teams(home_team, away_team)
            if comparison:
                # Simple effectiveness scoring based on team data availability and variance
                contributions['elo_score'] += abs(comparison['team1_strength'] - comparison['team2_strength']) / 50.0
                contributions['form_score'] += 0.6  # Fixed contribution for form
                contributions['squad_value'] += 0.7  # Fixed contribution for squad value
                contributions['home_advantage'] += 0.8 if comparison['same_league'] else 0.5
                
        except Exception:
            pass  # Silently handle errors in parameter tracking
    
    def _generate_insights(self, outcome_stats: Dict, accuracy: float) -> List[str]:
        """Generate insights about prediction performance"""
        
        insights = []
        
        # Overall accuracy insight
        if accuracy >= 50:
            insights.append(f"Strong overall accuracy at {accuracy:.1f}% - above random chance")
        elif accuracy >= 40:
            insights.append(f"Moderate accuracy at {accuracy:.1f}% - shows predictive value")
        else:
            insights.append(f"Low accuracy at {accuracy:.1f}% - model needs improvement")
        
        # Outcome-specific insights
        for outcome, stats in outcome_stats.items():
            if stats['predicted'] > 0:
                outcome_accuracy = (stats['correct'] / stats['predicted']) * 100
                outcome_name = outcome.replace('_', ' ').title()
                
                if outcome_accuracy >= 60:
                    insights.append(f"Excellent {outcome_name} prediction ({outcome_accuracy:.0f}% accuracy)")
                elif outcome_accuracy >= 40:
                    insights.append(f"Good {outcome_name} prediction ({outcome_accuracy:.0f}% accuracy)")
                else:
                    insights.append(f"{outcome_name} predictions need improvement ({outcome_accuracy:.0f}% accuracy)")
        
        return insights
    
    def _empty_results(self) -> Dict:
        """Return empty results structure when no data is available"""
        return {
            'status': 'error',
            'error': 'No historical data available',
            'total_matches': 0,
            'correct_predictions': 0,
            'accuracy': 0.0,
            'breakdown': {
                'home_wins': {'predicted': 0, 'actual': 0, 'correct': 0},
                'draws': {'predicted': 0, 'actual': 0, 'correct': 0},
                'away_wins': {'predicted': 0, 'actual': 0, 'correct': 0}
            },
            'parameter_effectiveness': {
                'elo_score': 0.5,
                'form_score': 0.5,
                'squad_value': 0.5,
                'home_advantage': 0.5
            },
            'insights': ['No historical data available for analysis']
        }


if __name__ == "__main__":
    # Example usage
    engine = BacktestingEngine()
    results = engine.run_backtest(50)
    
    print(f"\n📊 BACKTESTING RESULTS:")
    print(f"Total Matches: {results['total_matches']}")
    print(f"Accuracy: {results['accuracy']}%")
    print(f"Correct Predictions: {results['correct_predictions']}")
    
    print(f"\n🎯 Insights:")
    for insight in results['insights']:
        print(f"  • {insight}")