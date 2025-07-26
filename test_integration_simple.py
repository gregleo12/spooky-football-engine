#!/usr/bin/env python3
"""
Simple test for Phase 2 Integration Layer
Tests data collection without database integration
"""
import sys
import os

# Add data collection agents to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents', 'data_collection_v2'))

from enhanced_elo_agent import EnhancedELOAgent
from advanced_form_agent import AdvancedFormAgent
from goals_data_agent import GoalsDataAgent
from context_data_agent import ContextDataAgent
from data_validation_framework_clean import DataValidationFramework

def test_data_collection():
    """Test data collection from all Phase 1 agents"""
    print("🧪 TESTING PHASE 2 DATA COLLECTION")
    print("="*60)
    
    agents = {
        'Enhanced ELO': EnhancedELOAgent(),
        'Advanced Form': AdvancedFormAgent(),
        'Goals Data': GoalsDataAgent(),
        'Context Data': ContextDataAgent()
    }
    
    validator = DataValidationFramework()
    test_teams = ["Manchester City", "Real Madrid"]
    
    for team in test_teams:
        print(f"\n🔍 Testing data collection for {team}")
        print("-" * 40)
        
        team_data = {}
        team_success = True
        
        for agent_name, agent in agents.items():
            try:
                print(f"  📊 {agent_name} Agent...")
                result = agent.execute_collection(team, "Premier League")
                
                if result:
                    data = result['data']
                    metadata = result['metadata']
                    
                    # Validate data
                    agent_key = agent_name.lower().split()[0]  # 'enhanced' -> 'elo'
                    if agent_key == 'enhanced':
                        agent_key = 'elo'
                    elif agent_key == 'advanced':
                        agent_key = 'form'
                    
                    validation = validator.validate_agent_data(agent_key, data)
                    
                    if validation['success']:
                        print(f"    ✅ SUCCESS (Quality: {validation['data_quality']:.1f}%)")
                        team_data[agent_name] = {
                            'data': data,
                            'metadata': metadata,
                            'validation': validation
                        }
                    else:
                        print(f"    ❌ VALIDATION FAILED")
                        print(f"       Missing: {validation['missing_fields']}")
                        print(f"       Invalid: {validation['invalid_ranges']}")
                        team_success = False
                else:
                    print(f"    ❌ NO DATA RETURNED")
                    team_success = False
                    
            except Exception as e:
                print(f"    ❌ ERROR: {e}")
                team_success = False
        
        # Summary for team
        if team_success:
            print(f"\n  🎉 {team}: ALL AGENTS SUCCESSFUL")
            print(f"     Data collected from {len(team_data)} agents")
            
            # Show sample data
            for agent_name, agent_info in team_data.items():
                data = agent_info['data']
                sample_keys = list(data.keys())[:3]  # Show first 3 keys
                print(f"     {agent_name}: {sample_keys}...")
                
        else:
            print(f"\n  ❌ {team}: SOME AGENTS FAILED")

if __name__ == "__main__":
    test_data_collection()