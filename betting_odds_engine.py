#!/usr/bin/env python3
"""
Betting Odds Engine - Phase 2 Implementation
Converts team strength scores to realistic betting odds across multiple markets
"""
import time
from typing import Dict, Optional, Tuple

class BettingOddsEngine:
    """
    Production-ready betting odds engine for Phase 2
    
    Converts Phase 1 team strength scores (0-1) into:
    - Match outcome odds (Home/Draw/Away)
    - Over/Under 2.5 goals
    - Both Teams to Score (BTTS)
    - Correct Score predictions
    """
    
    def __init__(self):
        self.home_advantage = 0.10  # 10% boost for home teams
        self.bookmaker_margin = 0.05  # 5% margin for realistic odds
    
    def convert_probability_to_odds(self, probability: float) -> Optional[float]:
        """Convert probability percentage to decimal betting odds"""
        if probability <= 0 or probability >= 100:
            return None
        
        # Convert percentage to decimal (0-1) 
        prob_decimal = probability / 100.0
        
        # Add bookmaker margin for realistic odds
        adjusted_prob = prob_decimal * (1 + self.bookmaker_margin)
        adjusted_prob = min(0.99, adjusted_prob)  # Cap at 99%
        
        # Calculate decimal odds
        decimal_odds = 1.0 / adjusted_prob
        
        return round(decimal_odds, 2)
    
    def calculate_match_outcome_probabilities(self, home_strength: float, away_strength: float, 
                                            venue: str = "home") -> Tuple[float, float, float]:
        """
        Calculate match outcome probabilities (Home/Draw/Away)
        
        Args:
            home_strength: Team strength score (0-1)
            away_strength: Team strength score (0-1) 
            venue: "home", "away", or "neutral"
            
        Returns:
            Tuple of (home_prob, draw_prob, away_prob) percentages
        """
        total_strength = home_strength + away_strength
        
        if total_strength > 0:
            home_base = (home_strength / total_strength) * 100
            away_base = (away_strength / total_strength) * 100
        else:
            home_base = away_base = 50.0
        
        # Apply venue advantage
        if venue == "home":
            home_prob = min(95.0, home_base + (self.home_advantage * 100))
            away_prob = max(5.0, 100.0 - home_prob)
        elif venue == "away":
            away_prob = min(95.0, away_base + (self.home_advantage * 100))
            home_prob = max(5.0, 100.0 - away_prob)
        else:  # neutral venue
            home_prob = home_base
            away_prob = away_base
        
        # Calculate draw probability based on team closeness
        strength_difference = abs(home_strength - away_strength)
        max_draw_prob = 35.0  # Evenly matched teams
        min_draw_prob = 15.0  # Mismatched teams
        
        if strength_difference <= 0.1:
            draw_prob = max_draw_prob
        elif strength_difference >= 0.4:
            draw_prob = min_draw_prob
        else:
            # Linear interpolation
            draw_prob = max_draw_prob - ((strength_difference - 0.1) / 0.3) * (max_draw_prob - min_draw_prob)
        
        # Normalize to 100%
        total_prob = home_prob + away_prob + draw_prob
        home_prob = (home_prob / total_prob) * 100
        away_prob = (away_prob / total_prob) * 100
        draw_prob = (draw_prob / total_prob) * 100
        
        return home_prob, draw_prob, away_prob
    
    def calculate_goals_market_probabilities(self, home_strength: float, away_strength: float) -> Tuple[float, float]:
        """
        Calculate Over/Under 2.5 goals probabilities
        
        Returns:
            Tuple of (over_2_5_prob, under_2_5_prob) percentages
        """
        # Higher strength teams tend to create more goal-scoring opportunities
        avg_strength = (home_strength + away_strength) / 2.0
        
        # Base probability influenced by team quality
        over_2_5_prob = 45.0 + (avg_strength * 20.0)  # Range: 45-65%
        over_2_5_prob = max(35.0, min(75.0, over_2_5_prob))
        
        under_2_5_prob = 100.0 - over_2_5_prob
        
        return over_2_5_prob, under_2_5_prob
    
    def calculate_btts_probabilities(self, home_strength: float, away_strength: float) -> Tuple[float, float]:
        """
        Calculate Both Teams to Score probabilities
        
        Returns:
            Tuple of (btts_yes_prob, btts_no_prob) percentages
        """
        # Based on both teams' attacking capabilities
        min_strength = min(home_strength, away_strength)
        avg_strength = (home_strength + away_strength) / 2.0
        
        # If both teams are strong, more likely both score
        btts_yes_prob = 50.0 + (min_strength * 25.0) + (avg_strength * 10.0)
        btts_yes_prob = max(35.0, min(80.0, btts_yes_prob))
        
        btts_no_prob = 100.0 - btts_yes_prob
        
        return btts_yes_prob, btts_no_prob
    
    def generate_comprehensive_odds(self, home_team: str, away_team: str, 
                                  home_strength: float, away_strength: float,
                                  venue: str = "home") -> Dict:
        """
        Generate comprehensive betting odds for a match
        
        Args:
            home_team: Home team name
            away_team: Away team name
            home_strength: Home team strength (0-1)
            away_strength: Away team strength (0-1)
            venue: "home", "away", or "neutral"
            
        Returns:
            Dictionary with all betting markets and odds
        """
        start_time = time.time()
        
        # 1. Match Outcome Odds
        home_prob, draw_prob, away_prob = self.calculate_match_outcome_probabilities(
            home_strength, away_strength, venue
        )
        
        match_outcome_odds = {
            'home_win': {
                'team': home_team,
                'probability': round(home_prob, 1),
                'odds': self.convert_probability_to_odds(home_prob)
            },
            'draw': {
                'probability': round(draw_prob, 1),
                'odds': self.convert_probability_to_odds(draw_prob)
            },
            'away_win': {
                'team': away_team,
                'probability': round(away_prob, 1),
                'odds': self.convert_probability_to_odds(away_prob)
            }
        }
        
        # 2. Goals Market
        over_prob, under_prob = self.calculate_goals_market_probabilities(home_strength, away_strength)
        
        goals_market_odds = {
            'over_2_5': {
                'probability': round(over_prob, 1),
                'odds': self.convert_probability_to_odds(over_prob)
            },
            'under_2_5': {
                'probability': round(under_prob, 1),
                'odds': self.convert_probability_to_odds(under_prob)
            }
        }
        
        # 3. Both Teams to Score
        btts_yes_prob, btts_no_prob = self.calculate_btts_probabilities(home_strength, away_strength)
        
        btts_market_odds = {
            'yes': {
                'probability': round(btts_yes_prob, 1),
                'odds': self.convert_probability_to_odds(btts_yes_prob)
            },
            'no': {
                'probability': round(btts_no_prob, 1),
                'odds': self.convert_probability_to_odds(btts_no_prob)
            }
        }
        
        # 4. Most Likely Correct Score
        correct_score = self.predict_most_likely_score(home_prob, away_prob, draw_prob)
        
        # 5. Performance metrics
        calculation_time = time.time() - start_time
        
        return {
            'match_info': {
                'home_team': home_team,
                'away_team': away_team,
                'venue': venue,
                'home_strength': round(home_strength, 3),
                'away_strength': round(away_strength, 3)
            },
            'match_outcome': match_outcome_odds,
            'goals_market': goals_market_odds,
            'btts_market': btts_market_odds,
            'predicted_score': correct_score,
            'performance': {
                'calculation_time_ms': round(calculation_time * 1000, 2),
                'bookmaker_margin': f"{self.bookmaker_margin*100:.1f}%"
            }
        }
    
    def predict_most_likely_score(self, home_prob: float, away_prob: float, draw_prob: float) -> Dict:
        """Predict most likely correct score based on probabilities"""
        
        if home_prob > away_prob and home_prob > draw_prob:
            if home_prob > 60:
                return {'score': '2-0', 'probability': round(home_prob * 0.15, 1)}
            else:
                return {'score': '1-0', 'probability': round(home_prob * 0.20, 1)}
        elif away_prob > home_prob and away_prob > draw_prob:
            if away_prob > 60:
                return {'score': '0-2', 'probability': round(away_prob * 0.15, 1)}
            else:
                return {'score': '0-1', 'probability': round(away_prob * 0.20, 1)}
        else:
            return {'score': '1-1', 'probability': round(draw_prob * 0.25, 1)}

# Global instance for Flask app
odds_engine = BettingOddsEngine()

def quick_odds_calculation(home_team: str, away_team: str, 
                          home_strength: float, away_strength: float) -> Dict:
    """Quick odds calculation for API endpoints"""
    return odds_engine.generate_comprehensive_odds(
        home_team, away_team, home_strength, away_strength
    )