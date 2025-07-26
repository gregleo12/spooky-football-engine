#!/usr/bin/env python3
"""
Modular Calculator Engine - Phase 2
Flexible calculation system for team strength scores using Phase 1 collected data
Supports multiple market types and A/B testing of different formulas
"""
import sys
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union
from abc import ABC, abstractmethod
import json

# Add data collection agents to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'data_collection_v2'))

from data_validation_framework_clean import DataValidationFramework

class CalculationFormula(ABC):
    """Abstract base class for different calculation formulas"""
    
    @abstractmethod
    def calculate_overall_strength(self, team_data: Dict[str, Any]) -> float:
        """Calculate overall team strength score"""
        pass
    
    @abstractmethod
    def get_formula_name(self) -> str:
        """Get human-readable formula name"""
        pass
    
    @abstractmethod
    def get_formula_description(self) -> str:
        """Get formula description"""
        pass

class OriginalWeightedFormula(CalculationFormula):
    """Original 47% weighted formula from Phase 1"""
    
    def __init__(self):
        self.weights = {
            'elo_score': 0.18,
            'squad_value_score': 0.15,
            'form_score': 0.05,
            'squad_depth_score': 0.02,
            'h2h_performance': 0.04,
            'scoring_patterns': 0.03
        }
    
    def calculate_overall_strength(self, team_data: Dict[str, Any]) -> float:
        """Calculate using original weighted formula"""
        total_score = 0.0
        
        # Map new parameter names to old weights
        parameter_mapping = {
            'standard_elo': 'elo_score',
            'total_squad_value': 'squad_value_score',
            'raw_form_score': 'form_score',
            'squad_depth_index': 'squad_depth_score'
        }
        
        for new_param, old_weight_key in parameter_mapping.items():
            if new_param in team_data and old_weight_key in self.weights:
                # Normalize to 0-1 scale (assuming values are already in reasonable ranges)
                normalized_value = min(1.0, max(0.0, team_data[new_param] / 100))
                total_score += normalized_value * self.weights[old_weight_key]
        
        return total_score
    
    def get_formula_name(self) -> str:
        return "Original Weighted (47%)"
    
    def get_formula_description(self) -> str:
        return "Original 6-parameter weighted formula: ELO(18%) + Squad Value(15%) + Form(5%) + Squad Depth(2%) + H2H(4%) + Scoring(3%)"

class EnhancedElevenParameterFormula(CalculationFormula):
    """Enhanced 11-parameter formula using all Phase 1 data"""
    
    def __init__(self):
        self.weights = {
            # Enhanced ELO (20% total)
            'standard_elo': 0.12,
            'recent_form_elo': 0.08,
            
            # Advanced Form (15% total)
            'raw_form_score': 0.05,
            'opponent_adjusted_form': 0.08,
            'form_consistency': 0.02,
            
            # Goals Analysis (20% total)
            'goals_per_game': 0.08,
            'opponent_adjusted_offensive': 0.05,
            'goals_conceded_per_game': 0.04,
            'opponent_adjusted_defensive': 0.03,
            
            # Squad Analysis (15% total)
            'total_squad_value': 0.08,
            'squad_depth_index': 0.04,
            'starting_xi_avg_value': 0.03,
            
            # Context Analysis (10% total)
            'overall_home_advantage': 0.04,
            'motivation_factor': 0.04,
            'fixture_density': 0.02
        }
    
    def calculate_overall_strength(self, team_data: Dict[str, Any]) -> float:
        """Calculate using enhanced 11-parameter formula"""
        total_score = 0.0
        total_possible_weight = 0.0
        
        for parameter, weight in self.weights.items():
            if parameter in team_data:
                value = team_data[parameter]
                
                # Normalize different parameter types
                normalized_value = self._normalize_parameter(parameter, value)
                total_score += normalized_value * weight
                total_possible_weight += weight
        
        # Scale to account for missing parameters
        if total_possible_weight > 0:
            total_score = (total_score / total_possible_weight) * sum(self.weights.values())
        
        return total_score
    
    def _normalize_parameter(self, parameter: str, value: Union[int, float]) -> float:
        """Normalize parameter value to 0-1 scale"""
        # Parameter-specific normalization ranges
        normalization_ranges = {
            'standard_elo': (1000, 2000),
            'recent_form_elo': (1000, 2000),
            'raw_form_score': (0, 3),
            'opponent_adjusted_form': (0, 5),
            'form_consistency': (0, 1),
            'goals_per_game': (0, 4),
            'opponent_adjusted_offensive': (0, 5),
            'goals_conceded_per_game': (0, 4),  # Inverted (lower is better)
            'opponent_adjusted_defensive': (0, 5),  # Inverted (lower is better)
            'total_squad_value': (10, 2000),
            'squad_depth_index': (0, 200),
            'starting_xi_avg_value': (0, 200),
            'overall_home_advantage': (0, 1),
            'motivation_factor': (0, 1),
            'fixture_density': (0, 3)
        }
        
        if parameter not in normalization_ranges:
            return min(1.0, max(0.0, value / 100))  # Default normalization
        
        min_val, max_val = normalization_ranges[parameter]
        
        # Handle inverted parameters (lower is better)
        if parameter in ['goals_conceded_per_game', 'opponent_adjusted_defensive']:
            normalized = 1.0 - ((value - min_val) / (max_val - min_val))
        else:
            normalized = (value - min_val) / (max_val - min_val)
        
        return min(1.0, max(0.0, normalized))
    
    def get_formula_name(self) -> str:
        return "Enhanced 11-Parameter (100%)"
    
    def get_formula_description(self) -> str:
        return "Complete 11-parameter formula: Enhanced ELO(20%) + Advanced Form(15%) + Goals Analysis(20%) + Squad Analysis(15%) + Context(10%)"

class MarketSpecificFormula(CalculationFormula):
    """Market-specific formula optimized for betting markets"""
    
    def __init__(self, market_type: str = "match_outcome"):
        self.market_type = market_type
        
        # Different weights for different market types
        self.market_weights = {
            "match_outcome": {
                # Focus on overall strength
                'standard_elo': 0.20,
                'recent_form_elo': 0.15,
                'opponent_adjusted_form': 0.12,
                'overall_home_advantage': 0.10,
                'motivation_factor': 0.08,
                'total_squad_value': 0.15,
                'squad_depth_index': 0.05,
                'goals_per_game': 0.08,
                'goals_conceded_per_game': 0.07
            },
            "over_under": {
                # Focus on goals
                'goals_per_game': 0.25,
                'opponent_adjusted_offensive': 0.20,
                'goals_conceded_per_game': 0.20,
                'opponent_adjusted_defensive': 0.15,
                'recent_form_elo': 0.10,
                'form_consistency': 0.05,
                'fixture_density': 0.05
            },
            "clean_sheet": {
                # Focus on defensive strength
                'goals_conceded_per_game': 0.30,
                'opponent_adjusted_defensive': 0.25,
                'standard_elo': 0.15,
                'overall_home_advantage': 0.10,
                'motivation_factor': 0.10,
                'form_consistency': 0.10
            }
        }
        
        self.weights = self.market_weights.get(market_type, self.market_weights["match_outcome"])
    
    def calculate_overall_strength(self, team_data: Dict[str, Any]) -> float:
        """Calculate using market-specific formula"""
        total_score = 0.0
        total_possible_weight = 0.0
        
        for parameter, weight in self.weights.items():
            if parameter in team_data:
                value = team_data[parameter]
                normalized_value = self._normalize_parameter(parameter, value)
                total_score += normalized_value * weight
                total_possible_weight += weight
        
        # Scale to account for missing parameters
        if total_possible_weight > 0:
            total_score = (total_score / total_possible_weight) * sum(self.weights.values())
        
        return total_score
    
    def _normalize_parameter(self, parameter: str, value: Union[int, float]) -> float:
        """Normalize parameter value to 0-1 scale (same as EnhancedElevenParameterFormula)"""
        # Reuse normalization logic
        enhanced_formula = EnhancedElevenParameterFormula()
        return enhanced_formula._normalize_parameter(parameter, value)
    
    def get_formula_name(self) -> str:
        return f"Market-Specific ({self.market_type.replace('_', ' ').title()})"
    
    def get_formula_description(self) -> str:
        return f"Optimized formula for {self.market_type.replace('_', ' ')} betting markets"

class ModularCalculatorEngine:
    """
    Main calculator engine that supports multiple formulas and market types
    """
    
    def __init__(self):
        self.available_formulas = {
            'original': OriginalWeightedFormula(),
            'enhanced': EnhancedElevenParameterFormula(),
            'market_match': MarketSpecificFormula('match_outcome'),
            'market_goals': MarketSpecificFormula('over_under'),
            'market_defense': MarketSpecificFormula('clean_sheet')
        }
        
        self.validator = DataValidationFramework()
    
    def calculate_team_strength(self, team_data: Dict[str, Any], 
                              formula_name: str = 'enhanced') -> Dict[str, Any]:
        """
        Calculate team strength using specified formula
        
        Args:
            team_data: Dictionary containing team parameter data
            formula_name: Name of formula to use ('original', 'enhanced', 'market_match', etc.)
            
        Returns:
            Dictionary with calculation results
        """
        if formula_name not in self.available_formulas:
            raise ValueError(f"Unknown formula: {formula_name}. Available: {list(self.available_formulas.keys())}")
        
        formula = self.available_formulas[formula_name]
        
        calculation_result = {
            'team_data': team_data,
            'formula_used': formula.get_formula_name(),
            'formula_description': formula.get_formula_description(),
            'calculation_timestamp': datetime.now().isoformat(),
            'overall_strength': 0.0,
            'strength_percentage': 0.0,
            'data_completeness': 0.0,
            'missing_parameters': [],
            'calculation_breakdown': {}
        }
        
        try:
            # Validate input data
            validation_result = self._validate_team_data(team_data)
            calculation_result['data_completeness'] = validation_result['completeness']
            calculation_result['missing_parameters'] = validation_result['missing_parameters']
            
            # Calculate strength
            overall_strength = formula.calculate_overall_strength(team_data)
            calculation_result['overall_strength'] = overall_strength
            calculation_result['strength_percentage'] = overall_strength * 100
            
            # Create breakdown for transparency
            if hasattr(formula, 'weights'):
                breakdown = self._create_calculation_breakdown(team_data, formula.weights)
                calculation_result['calculation_breakdown'] = breakdown
            
        except Exception as e:
            calculation_result['error'] = str(e)
            calculation_result['overall_strength'] = 0.0
        
        return calculation_result
    
    def compare_team_strengths(self, team1_data: Dict[str, Any], team2_data: Dict[str, Any],
                              formula_name: str = 'enhanced') -> Dict[str, Any]:
        """
        Compare two teams using specified formula
        
        Args:
            team1_data: First team data
            team2_data: Second team data  
            formula_name: Formula to use for comparison
            
        Returns:
            Comparison results
        """
        team1_result = self.calculate_team_strength(team1_data, formula_name)
        team2_result = self.calculate_team_strength(team2_data, formula_name)
        
        team1_strength = team1_result['overall_strength']
        team2_strength = team2_result['overall_strength']
        
        comparison = {
            'team1_name': team1_data.get('team_name', 'Team 1'),
            'team2_name': team2_data.get('team_name', 'Team 2'),
            'formula_used': team1_result['formula_used'],
            'comparison_timestamp': datetime.now().isoformat(),
            
            'team1_strength': team1_strength,
            'team2_strength': team2_strength,
            'team1_percentage': team1_strength * 100,
            'team2_percentage': team2_strength * 100,
            
            'strength_difference': abs(team1_strength - team2_strength),
            'stronger_team': team1_data.get('team_name', 'Team 1') if team1_strength > team2_strength else team2_data.get('team_name', 'Team 2'),
            'win_probability_team1': self._calculate_win_probability(team1_strength, team2_strength),
            'win_probability_team2': self._calculate_win_probability(team2_strength, team1_strength),
            
            'team1_calculation': team1_result,
            'team2_calculation': team2_result
        }
        
        return comparison
    
    def a_b_test_formulas(self, team_data: Dict[str, Any], 
                         formula_names: List[str] = None) -> Dict[str, Any]:
        """
        Test multiple formulas on the same team data for A/B testing
        
        Args:
            team_data: Team data to test
            formula_names: List of formula names to test (default: all)
            
        Returns:
            A/B test results
        """
        if formula_names is None:
            formula_names = list(self.available_formulas.keys())
        
        ab_test_results = {
            'team_data': team_data,
            'test_timestamp': datetime.now().isoformat(),
            'formulas_tested': len(formula_names),
            'formula_results': {},
            'strength_rankings': [],
            'variance_analysis': {}
        }
        
        formula_strengths = {}
        
        # Test each formula
        for formula_name in formula_names:
            if formula_name in self.available_formulas:
                result = self.calculate_team_strength(team_data, formula_name)
                ab_test_results['formula_results'][formula_name] = result
                formula_strengths[formula_name] = result['overall_strength']
        
        # Create rankings
        sorted_formulas = sorted(formula_strengths.items(), key=lambda x: x[1], reverse=True)
        ab_test_results['strength_rankings'] = [
            {'formula': name, 'strength': strength, 'percentage': strength * 100}
            for name, strength in sorted_formulas
        ]
        
        # Variance analysis
        strengths = list(formula_strengths.values())
        if len(strengths) > 1:
            mean_strength = sum(strengths) / len(strengths)
            variance = sum((s - mean_strength) ** 2 for s in strengths) / len(strengths)
            ab_test_results['variance_analysis'] = {
                'mean_strength': mean_strength,
                'variance': variance,
                'standard_deviation': variance ** 0.5,
                'coefficient_of_variation': (variance ** 0.5) / mean_strength if mean_strength > 0 else 0,
                'range': max(strengths) - min(strengths)
            }
        
        return ab_test_results
    
    def _validate_team_data(self, team_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate team data completeness"""
        expected_parameters = self.validator.required_parameters
        
        available_parameters = [param for param in expected_parameters if param in team_data]
        missing_parameters = [param for param in expected_parameters if param not in team_data]
        
        completeness = len(available_parameters) / len(expected_parameters)
        
        return {
            'completeness': completeness,
            'available_parameters': available_parameters,
            'missing_parameters': missing_parameters,
            'total_expected': len(expected_parameters),
            'total_available': len(available_parameters)
        }
    
    def _create_calculation_breakdown(self, team_data: Dict[str, Any], 
                                    weights: Dict[str, float]) -> Dict[str, Any]:
        """Create transparent calculation breakdown"""
        breakdown = {}
        
        for parameter, weight in weights.items():
            if parameter in team_data:
                value = team_data[parameter]
                contribution = value * weight  # Simplified
                breakdown[parameter] = {
                    'raw_value': value,
                    'weight': weight,
                    'contribution': contribution,
                    'percentage_of_total': (contribution / sum(weights.values())) * 100 if sum(weights.values()) > 0 else 0
                }
        
        return breakdown
    
    def _calculate_win_probability(self, team1_strength: float, team2_strength: float) -> float:
        """Calculate win probability using Elo-style formula"""
        if team1_strength + team2_strength == 0:
            return 0.5
        
        # Simple strength ratio approach
        strength_ratio = team1_strength / (team1_strength + team2_strength)
        return max(0.0, min(1.0, strength_ratio))
    
    def get_available_formulas(self) -> Dict[str, str]:
        """Get list of available formulas with descriptions"""
        return {
            name: formula.get_formula_description()
            for name, formula in self.available_formulas.items()
        }


def main():
    """Test the Modular Calculator Engine"""
    calculator = ModularCalculatorEngine()
    
    print("🧮 TESTING MODULAR CALCULATOR ENGINE")
    print("="*60)
    
    # Sample team data (would come from data collection agents)
    sample_team_data = {
        'team_name': 'Manchester City',
        'standard_elo': 1586.8,
        'recent_form_elo': 1590.9,
        'elo_trend': 'improving',
        'raw_form_score': 2.5,
        'opponent_adjusted_form': 2.62,
        'form_consistency': 0.8,
        'goals_per_game': 1.89,
        'opponent_adjusted_offensive': 2.1,
        'goals_conceded_per_game': 0.85,
        'opponent_adjusted_defensive': 0.9,
        'total_squad_value': 1340.0,
        'squad_depth_index': 85.6,
        'starting_xi_avg_value': 95.2,
        'overall_home_advantage': 0.65,
        'motivation_factor': 0.75,
        'current_position': 3,
        'fixture_density': 1.2
    }
    
    print(f"\n📊 Testing calculations for {sample_team_data['team_name']}")
    
    # Test all available formulas
    formulas = calculator.get_available_formulas()
    print(f"\n🔢 Available formulas: {len(formulas)}")
    for name, description in formulas.items():
        print(f"   {name}: {description}")
    
    # A/B test all formulas
    print(f"\n🧪 A/B Testing all formulas...")
    ab_results = calculator.a_b_test_formulas(sample_team_data)
    
    print(f"\n📈 Strength Rankings:")
    for i, ranking in enumerate(ab_results['strength_rankings'], 1):
        print(f"   {i}. {ranking['formula']}: {ranking['percentage']:.1f}%")
    
    if 'variance_analysis' in ab_results:
        variance = ab_results['variance_analysis']
        print(f"\n📊 Variance Analysis:")
        print(f"   Mean Strength: {variance['mean_strength']:.3f}")
        print(f"   Standard Deviation: {variance['standard_deviation']:.3f}")
        print(f"   Range: {variance['range']:.3f}")
    
    print(f"\n✅ Modular Calculator Engine test completed!")


if __name__ == "__main__":
    main()