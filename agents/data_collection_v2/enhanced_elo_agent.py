#!/usr/bin/env python3
"""
Enhanced ELO Agent - Phase 1
Collects standard ELO plus recent form ELO with recency weighting
Replaces: agents/team_strength/competition_elo_agent.py
"""
import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from base_agent import BaseDataAgent, DataCollectionError

class EnhancedELOAgent(BaseDataAgent):
    """Enhanced ELO data collection with recency weighting and trend analysis"""
    
    def __init__(self):
        super().__init__("Enhanced ELO Agent")
        self.api_key = "53faec37f076f995841d30d0f7b2dd9d"
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {
            'x-rapidapi-host': 'v3.football.api-sports.io',
            'x-rapidapi-key': self.api_key
        }
        
        # Load team API mappings
        self.load_team_mappings()
    
    def load_team_mappings(self):
        """Load team name to API-Football ID mappings"""
        try:
            mapping_path = os.path.join(os.path.dirname(__file__), '..', 'shared', 'team_api_ids.json')
            with open(mapping_path, 'r') as f:
                self.team_mappings = json.load(f)
        except Exception as e:
            print(f"⚠️ Could not load team mappings: {e}")
            self.team_mappings = {}
    
    def get_api_team_id(self, team_name: str) -> Optional[int]:
        """Get API-Football team ID from team name"""
        return self.team_mappings.get(team_name)
    
    def get_current_elo(self, team_id: int) -> Optional[float]:
        """Get current ELO rating from API-Football"""
        try:
            # API-Football doesn't directly provide ELO, but we can use their team statistics
            # as a proxy or calculate from recent match performance
            url = f"{self.base_url}/teams/statistics"
            params = {
                'team': team_id,
                'season': 2024,
                'league': self.get_primary_league_for_team(team_id)
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                print(f"⚠️ API error {response.status_code} for team {team_id}")
                return None
                
            data = response.json()
            
            if not data.get('response'):
                return None
            
            stats = data['response']
            
            # Calculate ELO-like rating from team statistics
            # This is a simplified ELO calculation based on wins/draws/losses
            fixtures = stats['fixtures']
            wins = fixtures['wins']['total'] or 0
            draws = fixtures['draws']['total'] or 0
            losses = fixtures['loses']['total'] or 0
            total_games = wins + draws + losses
            
            if total_games == 0:
                return 1500.0  # Default ELO
            
            # Simple ELO-like calculation
            win_rate = wins / total_games
            draw_rate = draws / total_games
            
            # Base ELO of 1500, adjusted by performance
            elo_rating = 1500 + (win_rate * 300) + (draw_rate * 100) - 100
            
            return max(1000, min(2000, elo_rating))  # Clamp between 1000-2000
            
        except Exception as e:
            print(f"❌ Error getting ELO for team {team_id}: {e}")
            return None
    
    def get_primary_league_for_team(self, team_id: int) -> int:
        """Get the primary league ID for a team"""
        # This is a simplified mapping - in production we'd query this dynamically
        league_mappings = {
            # Premier League teams range (approximate)
            range(33, 53): 39,  # Premier League
            # La Liga teams range (approximate)  
            range(529, 549): 140,  # La Liga
            # Serie A teams range (approximate)
            range(489, 509): 135,  # Serie A
            # Bundesliga teams range (approximate)
            range(157, 175): 78,   # Bundesliga
            # Ligue 1 teams range (approximate)
            range(77, 95): 61      # Ligue 1
        }
        
        for team_range, league_id in league_mappings.items():
            if team_id in team_range:
                return league_id
        
        return 39  # Default to Premier League
    
    def get_recent_matches(self, team_id: int, count: int = 10) -> List[Dict]:
        """Get recent matches for trend analysis"""
        try:
            url = f"{self.base_url}/fixtures"
            params = {
                'team': team_id,
                'last': count,
                'status': 'FT'  # Only finished matches
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return []
                
            data = response.json()
            return data.get('response', [])
            
        except Exception as e:
            print(f"❌ Error getting recent matches for team {team_id}: {e}")
            return []
    
    def calculate_recent_form_elo(self, matches: List[Dict]) -> float:
        """Calculate ELO-like rating based on recent form with recency weighting"""
        if not matches:
            return 1500.0
        
        form_elo = 1500.0  # Starting point
        
        for i, match in enumerate(matches):
            # Recency weight: more recent matches have higher impact
            recency_weight = 1.0 - (i * 0.05)  # Decay by 5% per match back
            
            try:
                home_team = match['teams']['home']
                away_team = match['teams']['away']
                home_goals = match['goals']['home']
                away_goals = match['goals']['away']
                
                # Determine if our team was home or away
                if home_team['id'] == int(match['teams']['home']['id']):
                    # Our team was home
                    our_goals = home_goals
                    opponent_goals = away_goals
                else:
                    # Our team was away
                    our_goals = away_goals
                    opponent_goals = home_goals
                
                # Calculate result impact
                if our_goals > opponent_goals:
                    # Win
                    elo_change = 30 * recency_weight
                elif our_goals == opponent_goals:
                    # Draw
                    elo_change = 5 * recency_weight
                else:
                    # Loss
                    elo_change = -25 * recency_weight
                
                # Goal difference bonus/penalty
                goal_diff = abs(our_goals - opponent_goals)
                if goal_diff > 1:
                    goal_diff_multiplier = 1 + (goal_diff - 1) * 0.1
                    elo_change *= goal_diff_multiplier
                
                form_elo += elo_change
                
            except (KeyError, TypeError, ValueError) as e:
                continue  # Skip malformed match data
        
        return max(1000, min(2000, form_elo))
    
    def calculate_elo_trend(self, matches: List[Dict]) -> str:
        """Calculate trend direction from recent matches"""
        if len(matches) < 3:
            return "stable"
        
        recent_results = []
        for match in matches[:5]:  # Last 5 matches
            try:
                home_goals = match['goals']['home']
                away_goals = match['goals']['away']
                home_team_id = match['teams']['home']['id']
                
                # Determine result for our team
                if str(home_team_id) in str(match):  # Simplified check
                    if home_goals > away_goals:
                        recent_results.append(3)  # Win
                    elif home_goals == away_goals:
                        recent_results.append(1)  # Draw
                    else:
                        recent_results.append(0)  # Loss
            except:
                continue
        
        if len(recent_results) < 3:
            return "stable"
        
        # Calculate trend
        first_half = sum(recent_results[:len(recent_results)//2])
        second_half = sum(recent_results[len(recent_results)//2:])
        
        if second_half > first_half * 1.2:
            return "improving"
        elif second_half < first_half * 0.8:
            return "declining"
        else:
            return "stable"
    
    def collect_data(self, team_id: str, competition_id: str) -> Dict[str, Any]:
        """
        Collect enhanced ELO data for a team
        
        Args:
            team_id: Team identifier (name or ID)
            competition_id: Competition context
            
        Returns:
            Dictionary with ELO data and trends
        """
        # Convert team name to API ID if needed
        if isinstance(team_id, str) and not team_id.isdigit():
            api_team_id = self.get_api_team_id(team_id)
            if not api_team_id:
                raise DataCollectionError(f"Could not find API ID for team: {team_id}")
        else:
            api_team_id = int(team_id)
        
        # Get current ELO rating
        standard_elo = self.get_current_elo(api_team_id)
        if standard_elo is None:
            raise DataCollectionError(f"Could not get ELO rating for team {api_team_id}")
        
        # Get recent matches for form analysis
        recent_matches = self.get_recent_matches(api_team_id, count=10)
        
        # Calculate recent form ELO
        recent_elo = self.calculate_recent_form_elo(recent_matches)
        
        # Calculate trend
        elo_trend = self.calculate_elo_trend(recent_matches)
        
        return {
            'standard_elo': standard_elo,
            'recent_form_elo': recent_elo,
            'elo_trend': elo_trend,
            'matches_analyzed': len(recent_matches),
            'team_api_id': api_team_id,
            'collection_timestamp': datetime.now().isoformat()
        }
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate collected ELO data
        
        Args:
            data: Data to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['standard_elo', 'recent_form_elo', 'elo_trend']
        
        # Check all required fields exist
        for field in required_fields:
            if field not in data:
                print(f"❌ Missing required field: {field}")
                return False
        
        # Validate ELO ranges
        if not (1000 <= data['standard_elo'] <= 2000):
            print(f"❌ Standard ELO out of range: {data['standard_elo']}")
            return False
        
        if not (1000 <= data['recent_form_elo'] <= 2000):
            print(f"❌ Recent form ELO out of range: {data['recent_form_elo']}")
            return False
        
        # Validate trend values
        valid_trends = ['improving', 'stable', 'declining']
        if data['elo_trend'] not in valid_trends:
            print(f"❌ Invalid trend value: {data['elo_trend']}")
            return False
        
        return True


def main():
    """Test the Enhanced ELO Agent"""
    agent = EnhancedELOAgent()
    
    # Test with a known team
    test_teams = ["Manchester City", "Real Madrid", "Inter"]
    
    for team in test_teams:
        print(f"\n🧪 Testing Enhanced ELO Agent with {team}")
        try:
            result = agent.execute_collection(team, "Premier League")
            if result:
                print(f"✅ Success: {result}")
            else:
                print(f"❌ Failed to collect data for {team}")
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()