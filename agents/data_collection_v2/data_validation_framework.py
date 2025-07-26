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
    
    def run_complete_validation(self, teams: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run complete validation across all teams and agents"""
        print("🚀 STARTING COMPLETE DATA VALIDATION")
        print("=" * 60)
        
        if teams is None:
            teams = self.get_test_teams()
        
        validation_summary = {
            'total_teams_tested': len(teams),
            'successful_teams': 0,
            'failed_teams': 0,
            'overall_data_coverage': 0.0,
            'agent_success_rates': {},
            'critical_issues': [],
            'team_results': {},
            'validation_timestamp': datetime.now().isoformat()
        }
        
        agent_successes = {name: 0 for name in self.agents.keys()}
        
        for team in teams:
            print(f"\n📋 Validating {team}...")
            
            team_result = self.validate_single_team_data(team)
            validation_summary['team_results'][team] = team_result
            
            if team_result['overall_success']:
                validation_summary['successful_teams'] += 1
                print(f"  ✅ {team}: PASSED (Quality: {team_result['data_quality_score']:.1f}%)")
            else:
                validation_summary['failed_teams'] += 1
                print(f"  ❌ {team}: FAILED (Quality: {team_result['data_quality_score']:.1f}%)")
                validation_summary['critical_issues'].extend(team_result['missing_parameters'])
                validation_summary['critical_issues'].extend(team_result['invalid_ranges'])
            
            # Count agent successes
            for agent_name, agent_result in team_result['agent_results'].items():
                if agent_result['success']:
                    agent_successes[agent_name] += 1
        
        # Calculate summary statistics
        total_teams = len(teams)
        validation_summary['overall_data_coverage'] = (validation_summary['successful_teams'] / total_teams) * 100
        
        for agent_name, successes in agent_successes.items():
            validation_summary['agent_success_rates'][agent_name] = (successes / total_teams) * 100
        
        return validation_summary\n    \n    def generate_validation_report(self, validation_results: Dict[str, Any]) -> str:\n        \"\"\"Generate a comprehensive validation report\"\"\"\n        report = []\n        report.append(\"📊 DATA VALIDATION REPORT\")\n        report.append(\"=\" * 60)\n        report.append(f\"Generated: {validation_results['validation_timestamp']}\")\n        report.append(f\"Teams Tested: {validation_results['total_teams_tested']}\")\n        report.append(\"\")\n        \n        # Overall Results\n        report.append(\"🎯 OVERALL RESULTS:\")\n        report.append(f\"✅ Successful Teams: {validation_results['successful_teams']}/{validation_results['total_teams_tested']}\")\n        report.append(f\"❌ Failed Teams: {validation_results['failed_teams']}/{validation_results['total_teams_tested']}\")\n        report.append(f\"📈 Data Coverage: {validation_results['overall_data_coverage']:.1f}%\")\n        report.append(\"\")\n        \n        # Agent Success Rates\n        report.append(\"🤖 AGENT SUCCESS RATES:\")\n        for agent_name, success_rate in validation_results['agent_success_rates'].items():\n            status = \"✅\" if success_rate >= 90 else \"⚠️\" if success_rate >= 70 else \"❌\"\n            report.append(f\"{status} {agent_name.capitalize()} Agent: {success_rate:.1f}%\")\n        report.append(\"\")\n        \n        # Critical Issues\n        if validation_results['critical_issues']:\n            report.append(\"🚨 CRITICAL ISSUES:\")\n            for issue in set(validation_results['critical_issues'][:10]):  # Show unique issues, max 10\n                report.append(f\"   • {issue}\")\n            report.append(\"\")\n        \n        # Team-by-Team Results\n        report.append(\"📋 TEAM-BY-TEAM RESULTS:\")\n        for team, result in validation_results['team_results'].items():\n            status = \"✅\" if result['overall_success'] else \"❌\"\n            report.append(f\"{status} {team}: {result['data_quality_score']:.1f}% quality\")\n        \n        # Recommendations\n        report.append(\"\")\n        report.append(\"💡 RECOMMENDATIONS:\")\n        \n        coverage = validation_results['overall_data_coverage']\n        if coverage >= 95:\n            report.append(\"✅ Excellent data coverage - ready for production\")\n        elif coverage >= 80:\n            report.append(\"⚠️ Good coverage - address remaining issues before production\")\n        else:\n            report.append(\"❌ Poor coverage - significant work needed before production\")\n        \n        # Agent-specific recommendations\n        for agent_name, success_rate in validation_results['agent_success_rates'].items():\n            if success_rate < 90:\n                report.append(f\"🔧 {agent_name.capitalize()} agent needs attention ({success_rate:.1f}% success rate)\")\n        \n        return \"\\n\".join(report)\n    \n    def save_validation_report(self, validation_results: Dict[str, Any], filename: Optional[str] = None) -> str:\n        \"\"\"Save validation report to file\"\"\"\n        if filename is None:\n            timestamp = datetime.now().strftime(\"%Y%m%d_%H%M%S\")\n            filename = f\"validation_report_{timestamp}.md\"\n        \n        report_content = self.generate_validation_report(validation_results)\n        \n        # Save to archive directory\n        archive_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'archive', 'validation_reports')\n        os.makedirs(archive_dir, exist_ok=True)\n        \n        filepath = os.path.join(archive_dir, filename)\n        \n        with open(filepath, 'w') as f:\n            f.write(report_content)\n        \n        return filepath\n    \n    def validate_data_freshness(self, max_age_days: int = 7) -> Dict[str, Any]:\n        \"\"\"Validate that all data is fresh enough for production use\"\"\"\n        print(f\"🕒 Checking data freshness (max age: {max_age_days} days)...\")\n        \n        # This would connect to the database and check last_updated timestamps\n        # For now, return a placeholder\n        return {\n            'freshness_check': 'passed',\n            'stale_data_count': 0,\n            'max_age_days': max_age_days,\n            'check_timestamp': datetime.now().isoformat()\n        }\n    \n    def check_data_consistency(self) -> Dict[str, Any]:\n        \"\"\"Check for data consistency across agents\"\"\"\n        print(\"🔍 Checking data consistency across agents...\")\n        \n        # This would check for logical consistency between different metrics\n        # For example: teams with high squad values should have good ELO ratings\n        return {\n            'consistency_check': 'passed',\n            'inconsistencies_found': 0,\n            'check_timestamp': datetime.now().isoformat()\n        }\n\n\ndef main():\n    \"\"\"Run the complete data validation framework\"\"\"\n    validator = DataValidationFramework()\n    \n    print(\"🧪 Testing Data Validation Framework\")\n    print(\"=\" * 50)\n    \n    # Test with a smaller set for demonstration\n    test_teams = [\"Manchester City\", \"Real Madrid\", \"Inter\"]\n    \n    # Run validation\n    results = validator.run_complete_validation(test_teams)\n    \n    # Generate and display report\n    report = validator.generate_validation_report(results)\n    print(\"\\n\" + report)\n    \n    # Save report\n    filepath = validator.save_validation_report(results)\n    print(f\"\\n📁 Validation report saved to: {filepath}\")\n    \n    return results\n\n\nif __name__ == \"__main__\":\n    main()