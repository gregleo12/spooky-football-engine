#!/usr/bin/env python3
"""
Data Validation Framework - Phase 1
Comprehensive validation system for ensuring 100% data coverage and quality
"""
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import sqlite3

# Add shared utilities to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

# Import all our data collection agents
from enhanced_elo_agent import EnhancedELOAgent
from advanced_form_agent import AdvancedFormAgent
from goals_data_agent import GoalsDataAgent
from enhanced_squad_value_agent import EnhancedSquadValueAgent
from context_data_agent import ContextDataAgent

class DataValidationFramework:
    """Comprehensive data validation and quality assurance system"""
    
    def __init__(self):
        self.required_parameters = [
            'standard_elo', 'recent_form_elo', 'elo_trend',
            'raw_form_score', 'opponent_adjusted_form', 'form_trend',
            'goals_per_game', 'opponent_adjusted_offensive', 'goals_conceded_per_game',
            'total_squad_value', 'squad_depth_index', 'starting_xi_avg_value',
            'overall_home_advantage', 'motivation_factor', 'current_position'
        ]
        
        self.parameter_ranges = {
            'standard_elo': (1000, 2000),
            'recent_form_elo': (1000, 2000),
            'raw_form_score': (0, 3),
            'opponent_adjusted_form': (0, 5),
            'goals_per_game': (0, 5),
            'goals_conceded_per_game': (0, 5),
            'total_squad_value': (10, 2000),  # €10M to €2B
            'squad_depth_index': (0, 200),
            'starting_xi_avg_value': (0, 200),
            'overall_home_advantage': (0, 1),
            'motivation_factor': (0, 1),
            'current_position': (1, 25)
        }
        
        self.agents = {
            'elo': EnhancedELOAgent(),
            'form': AdvancedFormAgent(),
            'goals': GoalsDataAgent(),
            'squad': EnhancedSquadValueAgent(),
            'context': ContextDataAgent()
        }
    
    def get_test_teams(self) -> List[str]:
        """Get list of teams for validation testing"""
        return [
            # Premier League
            "Manchester City", "Arsenal", "Liverpool", "Chelsea",
            # La Liga
            "Real Madrid", "Barcelona", "Atletico Madrid",
            # Serie A
            "Inter", "Juventus", "AC Milan",
            # Bundesliga
            "Bayern München", "Borussia Dortmund",
            # Ligue 1
            "Paris Saint Germain", "Monaco"
        ]
    
    def validate_single_team_data(self, team_name: str, competition: str = "Premier League") -> Dict[str, Any]:
        """
        Validate data collection for a single team across all agents
        
        Args:
            team_name: Team to validate
            competition: Competition context
            
        Returns:
            Validation results dictionary
        """
        print(f"🔍 Validating data for {team_name}...")
        
        validation_results = {
            'team_name': team_name,
            'overall_success': True,
            'agent_results': {},
            'missing_parameters': [],
            'invalid_ranges': [],
            'data_quality_score': 0.0,
            'collection_timestamp': datetime.now().isoformat()
        }
        
        successful_agents = 0
        total_agents = len(self.agents)
        
        # Test each agent
        for agent_name, agent in self.agents.items():
            print(f"  📊 Testing {agent_name} agent...")
            
            try:
                # Collect data from agent
                result = agent.execute_collection(team_name, competition)
                
                if result is None:
                    validation_results['agent_results'][agent_name] = {
                        'success': False,
                        'error': 'Agent returned None',
                        'data_quality': 0.0
                    }
                    validation_results['overall_success'] = False
                    continue
                
                data = result['data']
                agent_validation = self.validate_agent_data(agent_name, data)
                
                validation_results['agent_results'][agent_name] = agent_validation
                
                if agent_validation['success']:
                    successful_agents += 1
                else:
                    validation_results['overall_success'] = False
                    validation_results['missing_parameters'].extend(agent_validation.get('missing_fields', []))
                    validation_results['invalid_ranges'].extend(agent_validation.get('invalid_ranges', []))
                
            except Exception as e:
                validation_results['agent_results'][agent_name] = {
                    'success': False,
                    'error': str(e),
                    'data_quality': 0.0
                }
                validation_results['overall_success'] = False
        
        # Calculate overall data quality score
        validation_results['data_quality_score'] = (successful_agents / total_agents) * 100
        
        return validation_results
    
    def validate_agent_data(self, agent_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data from a specific agent"""
        validation = {
            'success': True,
            'missing_fields': [],
            'invalid_ranges': [],
            'data_quality': 100.0,
            'warnings': []
        }
        
        # Define expected fields for each agent
        expected_fields = {
            'elo': ['standard_elo', 'recent_form_elo', 'elo_trend'],
            'form': ['raw_form_score', 'opponent_adjusted_form', 'form_trend'],
            'goals': ['goals_per_game', 'opponent_adjusted_offensive', 'goals_conceded_per_game'],
            'squad': ['total_squad_value', 'squad_depth_index', 'starting_xi_avg_value'],
            'context': ['overall_home_advantage', 'motivation_factor', 'current_position']
        }
        
        # Check for missing fields
        required_fields = expected_fields.get(agent_name, [])
        for field in required_fields:
            if field not in data:
                validation['missing_fields'].append(field)
                validation['success'] = False
        
        # Check value ranges
        for field, value in data.items():
            if field in self.parameter_ranges:
                min_val, max_val = self.parameter_ranges[field]
                if not isinstance(value, (int, float)):
                    continue
                
                if not (min_val <= value <= max_val):
                    validation['invalid_ranges'].append(f"{field}: {value} not in range [{min_val}, {max_val}]")
                    validation['success'] = False
        
        # Calculate data quality score
        total_checks = len(required_fields) + len([f for f in data.keys() if f in self.parameter_ranges])
        failed_checks = len(validation['missing_fields']) + len(validation['invalid_ranges'])
        
        if total_checks > 0:
            validation['data_quality'] = ((total_checks - failed_checks) / total_checks) * 100
        
        return validation


def main():
    """Test the Data Validation Framework"""
    validator = DataValidationFramework()
    
    print("🧪 Testing Data Validation Framework")
    print("=" * 50)
    
    # Test with a smaller set for demonstration
    test_teams = ["Manchester City", "Real Madrid", "Inter"]
    
    for team in test_teams:
        result = validator.validate_single_team_data(team)
        if result['overall_success']:
            print(f"✅ {team}: PASSED ({result['data_quality_score']:.1f}% quality)")
        else:
            print(f"❌ {team}: FAILED ({result['data_quality_score']:.1f}% quality)")


if __name__ == "__main__":
    main()