#!/usr/bin/env python3
"""
Simple validation test to check our agents
"""
import sys
import os

# Add current directory to path
sys.path.append('.')

from enhanced_elo_agent import EnhancedELOAgent
from advanced_form_agent import AdvancedFormAgent
from goals_data_agent import GoalsDataAgent

def test_agents():
    """Test all our agents with a simple validation"""
    print("🧪 PHASE 1 AGENT VALIDATION TEST")
    print("=" * 50)
    
    agents = {
        'Enhanced ELO': EnhancedELOAgent(),
        'Advanced Form': AdvancedFormAgent(), 
        'Goals Data': GoalsDataAgent()
    }
    
    test_teams = ["Manchester City", "Real Madrid"]
    
    results = {}
    
    for agent_name, agent in agents.items():
        print(f"\n🔍 Testing {agent_name} Agent:")
        agent_results = []
        
        for team in test_teams:
            try:
                result = agent.execute_collection(team, "Premier League")
                if result:
                    print(f"  ✅ {team}: SUCCESS")
                    agent_results.append(True)
                else:
                    print(f"  ❌ {team}: FAILED")
                    agent_results.append(False)
            except Exception as e:
                print(f"  ❌ {team}: ERROR - {e}")
                agent_results.append(False)
        
        success_rate = (sum(agent_results) / len(agent_results)) * 100
        results[agent_name] = success_rate
        print(f"  📊 Success Rate: {success_rate:.1f}%")
    
    print(f"\n🎯 OVERALL RESULTS:")
    print("=" * 30)
    total_success = sum(results.values()) / len(results)
    
    for agent_name, success_rate in results.items():
        status = "✅" if success_rate >= 50 else "❌"
        print(f"{status} {agent_name}: {success_rate:.1f}%")
    
    print(f"\n📈 Average Success Rate: {total_success:.1f}%")
    
    if total_success >= 80:
        print("🎉 EXCELLENT: Phase 1 agents are working well!")
    elif total_success >= 60:
        print("⚠️ GOOD: Minor issues but agents are functional")
    else:
        print("🚨 NEEDS WORK: Significant issues with agents")
    
    return results

if __name__ == "__main__":
    test_agents()