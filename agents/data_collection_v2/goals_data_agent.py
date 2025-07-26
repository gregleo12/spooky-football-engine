#!/usr/bin/env python3
"""
Goals Data Agent - Phase 1
Collects offensive and defensive ratings for over/under markets and clean sheet analysis
New agent for comprehensive goals analysis
"""
import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from base_agent import BaseDataAgent, DataCollectionError

class GoalsDataAgent(BaseDataAgent):
    """Collect offensive and defensive ratings with opponent adjustment"""
    
    def __init__(self):
        super().__init__("Goals Data Agent")
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
    
    def get_primary_league_for_team(self, team_id: int) -> int:
        """Get the primary league ID for a team"""
        league_mappings = {
            range(33, 53): 39,     # Premier League
            range(529, 549): 140,  # La Liga
            range(489, 509): 135,  # Serie A
            range(157, 175): 78,   # Bundesliga
            range(77, 95): 61      # Ligue 1
        }
        
        for team_range, league_id in league_mappings.items():
            if team_id in team_range:
                return league_id
        
        return 39  # Default to Premier League
    
    def get_season_matches(self, team_id: int, competition_id: str = None) -> List[Dict]:
        """Get all season matches for comprehensive analysis"""
        try:
            league_id = self.get_primary_league_for_team(team_id)
            
            url = f"{self.base_url}/fixtures"
            params = {
                'team': team_id,
                'season': 2024,
                'league': league_id,
                'status': 'FT'  # Only finished matches
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                print(f"⚠️ API error {response.status_code} for team {team_id}")
                return []
                
            data = response.json()
            return data.get('response', [])
            
        except Exception as e:
            print(f"❌ Error getting season matches for team {team_id}: {e}")
            return []
    
    def get_opponent_defensive_strength(self, opponent_id: int) -> float:
        """
        Get opponent's defensive strength (goals conceded per game)
        Lower values = stronger defense
        """
        try:
            league_id = self.get_primary_league_for_team(opponent_id)
            
            url = f"{self.base_url}/teams/statistics"
            params = {
                'team': opponent_id,
                'season': 2024,
                'league': league_id
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return 1.2  # Average defensive strength
                
            data = response.json()
            
            if not data.get('response'):
                return 1.2
            
            stats = data['response']
            goals_against = stats['goals']['against']['total']['total'] or 0
            matches_played = stats['fixtures']['played']['total'] or 1
            
            return goals_against / matches_played
            
        except Exception as e:
            return 1.2  # Default defensive strength
    
    def get_opponent_offensive_strength(self, opponent_id: int) -> float:
        """
        Get opponent's offensive strength (goals scored per game)
        Higher values = stronger offense
        """
        try:
            league_id = self.get_primary_league_for_team(opponent_id)
            
            url = f"{self.base_url}/teams/statistics"
            params = {
                'team': opponent_id,
                'season': 2024,
                'league': league_id
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return 1.3  # Average offensive strength
                
            data = response.json()
            
            if not data.get('response'):
                return 1.3
            
            stats = data['response']
            goals_for = stats['goals']['for']['total']['total'] or 0
            matches_played = stats['fixtures']['played']['total'] or 1
            
            return goals_for / matches_played
            
        except Exception as e:
            return 1.3  # Default offensive strength
    
    def analyze_match_goals(self, match: Dict, our_team_id: int) -> Dict[str, Any]:
        """Analyze goals data from a single match"""
        try:
            home_team = match['teams']['home']
            away_team = match['teams']['away']
            home_goals = match['goals']['home'] or 0
            away_goals = match['goals']['away'] or 0
            
            is_home = (home_team['id'] == our_team_id)
            our_goals = home_goals if is_home else away_goals
            opponent_goals = away_goals if is_home else home_goals
            opponent_id = away_team['id'] if is_home else home_team['id']
            
            return {
                'our_goals': our_goals,
                'opponent_goals': opponent_goals,
                'total_goals': our_goals + opponent_goals,
                'clean_sheet': opponent_goals == 0,
                'failed_to_score': our_goals == 0,
                'is_home': is_home,
                'opponent_id': opponent_id,
                'date': match['fixture']['date']
            }
            
        except (KeyError, TypeError, ValueError):
            return {
                'our_goals': 0,
                'opponent_goals': 0,
                'total_goals': 0,
                'clean_sheet': False,
                'failed_to_score': True,
                'is_home': False,
                'opponent_id': 0,
                'date': None
            }
    
    def calculate_offensive_rating(self, matches: List[Dict], our_team_id: int) -> Dict[str, float]:
        """Calculate opponent-adjusted offensive rating"""
        if not matches:
            return {
                'goals_per_game': 0.0,
                'opponent_adjusted_offensive': 0.0,
                'scoring_consistency': 0.0,
                'big_chance_conversion': 0.0
            }
        
        total_goals = 0
        adjusted_goals = 0
        scoring_games = 0
        goal_counts = []
        
        for match in matches:
            match_analysis = self.analyze_match_goals(match, our_team_id)
            our_goals = match_analysis['our_goals']
            opponent_id = match_analysis['opponent_id']
            
            # Get opponent defensive strength
            opp_def_strength = self.get_opponent_defensive_strength(opponent_id)
            
            # Adjust for opponent quality
            # If opponent has strong defense (low goals conceded), our goals are worth more
            defensive_adjustment = 1.2 / (opp_def_strength + 0.1)  # Avoid division by zero
            defensive_adjustment = max(0.5, min(2.0, defensive_adjustment))  # Clamp
            
            total_goals += our_goals
            adjusted_goals += our_goals * defensive_adjustment
            goal_counts.append(our_goals)
            
            if our_goals > 0:
                scoring_games += 1
        
        matches_count = len(matches)
        goals_per_game = total_goals / matches_count
        adjusted_offensive = adjusted_goals / matches_count
        
        # Scoring consistency (percentage of games where team scored)
        scoring_consistency = (scoring_games / matches_count) * 100
        
        # Big chance conversion (simplified - games with 2+ goals)
        big_scoring_games = sum(1 for goals in goal_counts if goals >= 2)
        big_chance_conversion = (big_scoring_games / matches_count) * 100
        
        return {
            'goals_per_game': goals_per_game,
            'opponent_adjusted_offensive': adjusted_offensive,
            'scoring_consistency': scoring_consistency,
            'big_chance_conversion': big_chance_conversion,
            'total_goals_scored': total_goals,
            'matches_analyzed': matches_count
        }
    
    def calculate_defensive_rating(self, matches: List[Dict], our_team_id: int) -> Dict[str, float]:
        """Calculate opponent-adjusted defensive rating"""
        if not matches:
            return {
                'goals_conceded_per_game': 0.0,
                'opponent_adjusted_defensive': 0.0,
                'clean_sheet_percentage': 0.0,
                'defensive_consistency': 0.0
            }
        
        total_conceded = 0
        adjusted_conceded = 0
        clean_sheets = 0
        goals_conceded_counts = []
        
        for match in matches:
            match_analysis = self.analyze_match_goals(match, our_team_id)
            opponent_goals = match_analysis['opponent_goals']
            opponent_id = match_analysis['opponent_id']
            
            # Get opponent offensive strength
            opp_off_strength = self.get_opponent_offensive_strength(opponent_id)
            
            # Adjust for opponent quality
            # If opponent has strong offense, conceding is more "expected"
            offensive_adjustment = opp_off_strength / 1.3  # Normalize around average
            offensive_adjustment = max(0.5, min(2.0, offensive_adjustment))
            
            total_conceded += opponent_goals
            adjusted_conceded += opponent_goals * offensive_adjustment
            goals_conceded_counts.append(opponent_goals)
            
            if opponent_goals == 0:
                clean_sheets += 1
        
        matches_count = len(matches)
        goals_conceded_per_game = total_conceded / matches_count
        adjusted_defensive = adjusted_conceded / matches_count
        
        # Clean sheet percentage
        clean_sheet_percentage = (clean_sheets / matches_count) * 100
        
        # Defensive consistency (percentage of games conceding ≤1 goal)
        solid_defensive_games = sum(1 for goals in goals_conceded_counts if goals <= 1)
        defensive_consistency = (solid_defensive_games / matches_count) * 100
        
        return {
            'goals_conceded_per_game': goals_conceded_per_game,
            'opponent_adjusted_defensive': adjusted_defensive,
            'clean_sheet_percentage': clean_sheet_percentage,
            'defensive_consistency': defensive_consistency,
            'total_goals_conceded': total_conceded,
            'clean_sheets': clean_sheets
        }
    
    def calculate_over_under_indicators(self, matches: List[Dict], our_team_id: int) -> Dict[str, float]:
        """Calculate over/under market indicators"""
        if not matches:
            return {
                'avg_total_goals': 0.0,
                'over_2_5_percentage': 0.0,
                'over_1_5_percentage': 0.0,
                'btts_percentage': 0.0
            }
        
        total_goals_list = []
        over_2_5_count = 0
        over_1_5_count = 0
        btts_count = 0
        
        for match in matches:
            match_analysis = self.analyze_match_goals(match, our_team_id)
            total_goals = match_analysis['total_goals']
            our_goals = match_analysis['our_goals']
            opponent_goals = match_analysis['opponent_goals']
            
            total_goals_list.append(total_goals)
            
            if total_goals > 2.5:
                over_2_5_count += 1
            if total_goals > 1.5:
                over_1_5_count += 1
            if our_goals > 0 and opponent_goals > 0:
                btts_count += 1
        
        matches_count = len(matches)
        
        return {
            'avg_total_goals': sum(total_goals_list) / matches_count,
            'over_2_5_percentage': (over_2_5_count / matches_count) * 100,
            'over_1_5_percentage': (over_1_5_count / matches_count) * 100,
            'btts_percentage': (btts_count / matches_count) * 100,
            'goal_variance': self.calculate_variance(total_goals_list)
        }
    
    def calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of goals scored"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance
    
    def collect_data(self, team_id: str, competition_id: str) -> Dict[str, Any]:
        """
        Collect comprehensive goals data for a team
        
        Args:
            team_id: Team identifier
            competition_id: Competition context
            
        Returns:
            Dictionary with offensive/defensive ratings and over/under indicators
        """
        # Convert team name to API ID if needed
        if isinstance(team_id, str) and not team_id.isdigit():
            api_team_id = self.get_api_team_id(team_id)
            if not api_team_id:
                raise DataCollectionError(f"Could not find API ID for team: {team_id}")
        else:
            api_team_id = int(team_id)
        
        # Get season matches
        season_matches = self.get_season_matches(api_team_id, competition_id)
        
        if not season_matches:
            raise DataCollectionError(f"No season matches found for team {api_team_id}")
        
        # Calculate offensive metrics
        offensive_metrics = self.calculate_offensive_rating(season_matches, api_team_id)
        
        # Calculate defensive metrics
        defensive_metrics = self.calculate_defensive_rating(season_matches, api_team_id)
        
        # Calculate over/under indicators
        over_under_metrics = self.calculate_over_under_indicators(season_matches, api_team_id)
        
        # Recent form (last 8 games for goals)
        recent_matches = season_matches[:8] if len(season_matches) >= 8 else season_matches
        recent_offensive = self.calculate_offensive_rating(recent_matches, api_team_id)
        recent_defensive = self.calculate_defensive_rating(recent_matches, api_team_id)
        
        return {
            # Offensive metrics
            **offensive_metrics,
            
            # Defensive metrics  
            **defensive_metrics,
            
            # Over/under indicators
            **over_under_metrics,
            
            # Recent form
            'recent_goals_per_game': recent_offensive['goals_per_game'],
            'recent_goals_conceded_per_game': recent_defensive['goals_conceded_per_game'],
            'recent_clean_sheet_percentage': recent_defensive['clean_sheet_percentage'],
            
            # Metadata
            'team_api_id': api_team_id,
            'total_matches_analyzed': len(season_matches),
            'recent_matches_analyzed': len(recent_matches),
            'collection_timestamp': datetime.now().isoformat()
        }
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate collected goals data
        
        Args:
            data: Data to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = [
            'goals_per_game', 'opponent_adjusted_offensive',
            'goals_conceded_per_game', 'opponent_adjusted_defensive',
            'clean_sheet_percentage', 'avg_total_goals'
        ]
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                print(f"❌ Missing required field: {field}")
                return False
        
        # Validate ranges
        if not (0 <= data['goals_per_game'] <= 10):
            print(f"❌ Goals per game out of range: {data['goals_per_game']}")
            return False
        
        if not (0 <= data['goals_conceded_per_game'] <= 10):
            print(f"❌ Goals conceded per game out of range: {data['goals_conceded_per_game']}")
            return False
        
        if not (0 <= data['clean_sheet_percentage'] <= 100):
            print(f"❌ Clean sheet percentage out of range: {data['clean_sheet_percentage']}")
            return False
        
        return True


def main():
    """Test the Goals Data Agent"""
    agent = GoalsDataAgent()
    
    # Test with known teams
    test_teams = ["Manchester City", "Real Madrid", "Inter"]
    
    for team in test_teams:
        print(f"\n🧪 Testing Goals Data Agent with {team}")
        try:
            result = agent.execute_collection(team, "Premier League")
            if result:
                data = result['data']
                print(f"✅ Goals per game: {data['goals_per_game']:.2f}")
                print(f"✅ Opponent adjusted offensive: {data['opponent_adjusted_offensive']:.2f}")
                print(f"✅ Goals conceded per game: {data['goals_conceded_per_game']:.2f}")
                print(f"✅ Clean sheet %: {data['clean_sheet_percentage']:.1f}%")
                print(f"✅ Over 2.5 %: {data['over_2_5_percentage']:.1f}%")
                print(f"✅ BTTS %: {data['btts_percentage']:.1f}%")
            else:
                print(f"❌ Failed to collect data for {team}")
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()