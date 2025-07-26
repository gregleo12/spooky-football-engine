#!/usr/bin/env python3
"""
Advanced Form Agent - Phase 1
Enhanced form analysis with opponent quality weighting and tactical context
Replaces: agents/team_strength/competition_form_agent.py
"""
import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from base_agent import BaseDataAgent, DataCollectionError

class AdvancedFormAgent(BaseDataAgent):
    """Advanced form analysis with opponent quality weighting"""
    
    def __init__(self):
        super().__init__("Advanced Form Agent")
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
    
    def get_recent_matches(self, team_id: int, count: int = 10) -> List[Dict]:
        """Get recent finished matches for form analysis"""
        try:
            url = f"{self.base_url}/fixtures"
            params = {
                'team': team_id,
                'last': count,
                'status': 'FT'  # Only finished matches
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                print(f"⚠️ API error {response.status_code} for team {team_id}")
                return []
                
            data = response.json()
            return data.get('response', [])
            
        except Exception as e:
            print(f"❌ Error getting recent matches for team {team_id}: {e}")
            return []
    
    def get_opponent_strength(self, opponent_id: int) -> float:
        """
        Get opponent strength rating (simplified ELO-like calculation)
        In production, this would use cached ELO ratings
        """
        try:
            # For now, use a simplified strength calculation
            # In full implementation, this would query cached team strengths
            url = f"{self.base_url}/teams/statistics"
            params = {
                'team': opponent_id,
                'season': 2024,
                'league': self.get_primary_league_for_team(opponent_id)
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return 1500.0  # Default strength
                
            data = response.json()
            
            if not data.get('response'):
                return 1500.0
            
            stats = data['response']
            fixtures = stats['fixtures']
            
            wins = fixtures['wins']['total'] or 0
            draws = fixtures['draws']['total'] or 0
            losses = fixtures['loses']['total'] or 0
            total_games = wins + draws + losses
            
            if total_games == 0:
                return 1500.0
            
            # Simple strength calculation
            win_rate = wins / total_games
            draw_rate = draws / total_games
            
            strength = 1500 + (win_rate * 300) + (draw_rate * 100) - 100
            return max(1000, min(2000, strength))
            
        except Exception as e:
            print(f"⚠️ Could not get opponent strength for {opponent_id}: {e}")
            return 1500.0  # Default strength
    
    def get_primary_league_for_team(self, team_id: int) -> int:
        """Get the primary league ID for a team"""
        # Simplified mapping - in production we'd query this dynamically
        league_mappings = {
            # Premier League teams
            range(33, 53): 39,
            # La Liga teams
            range(529, 549): 140,
            # Serie A teams
            range(489, 509): 135,
            # Bundesliga teams
            range(157, 175): 78,
            # Ligue 1 teams
            range(77, 95): 61
        }
        
        for team_range, league_id in league_mappings.items():
            if team_id in team_range:
                return league_id
        
        return 39  # Default to Premier League
    
    def analyze_match_performance(self, match: Dict, our_team_id: int) -> Tuple[int, float, Dict]:
        """
        Analyze individual match performance
        
        Returns:
            (points_earned, performance_rating, match_context)
        """
        try:
            home_team = match['teams']['home']
            away_team = match['teams']['away']
            home_goals = match['goals']['home']
            away_goals = match['goals']['away']
            
            # Determine if we were home or away
            is_home = (home_team['id'] == our_team_id)
            our_goals = home_goals if is_home else away_goals
            opponent_goals = away_goals if is_home else home_goals
            opponent_id = away_team['id'] if is_home else home_team['id']
            
            # Basic points
            if our_goals > opponent_goals:
                points = 3  # Win
                result = 'W'
            elif our_goals == opponent_goals:
                points = 1  # Draw
                result = 'D'
            else:
                points = 0  # Loss
                result = 'L'
            
            # Performance rating (0-10 scale)
            goal_difference = our_goals - opponent_goals
            
            if result == 'W':
                performance = 7.0 + min(goal_difference, 3)  # 7-10 for wins
            elif result == 'D':
                performance = 5.0 + min(our_goals, 2) * 0.5  # 5-6 for draws
            else:
                performance = max(1.0, 4.0 + goal_difference)  # 1-4 for losses
            
            # Match context
            match_context = {
                'result': result,
                'goals_for': our_goals,
                'goals_against': opponent_goals,
                'goal_difference': goal_difference,
                'is_home': is_home,
                'opponent_id': opponent_id,
                'competition': match['league']['name'],
                'date': match['fixture']['date']
            }
            
            return points, performance, match_context
            
        except (KeyError, TypeError, ValueError) as e:
            print(f"⚠️ Error analyzing match: {e}")
            return 0, 1.0, {}
    
    def calculate_opponent_adjusted_form(self, matches: List[Dict], our_team_id: int) -> Dict[str, float]:
        """
        Calculate form score adjusted for opponent quality
        
        Args:
            matches: List of recent matches
            our_team_id: Our team's API ID
            
        Returns:
            Dictionary with various form metrics
        """
        if not matches:
            return {
                'raw_form_score': 0.0,
                'opponent_adjusted_form': 0.0,
                'performance_rating': 5.0,
                'consistency_score': 0.0
            }
        
        total_points = 0
        weighted_points = 0
        performance_ratings = []
        results = []
        
        for i, match in enumerate(matches):
            # Time decay: more recent matches weighted more heavily
            time_weight = 1.0 - (i * 0.05)  # 5% decay per match back
            
            # Analyze match performance
            points, performance, context = self.analyze_match_performance(match, our_team_id)
            
            # Get opponent strength for quality adjustment
            opponent_strength = self.get_opponent_strength(context.get('opponent_id', 0))
            
            # Opponent quality weight (stronger opponents = higher weight)
            # Normalize opponent strength to 0.5-1.5 range
            opponent_weight = 0.5 + (opponent_strength - 1000) / 1000
            opponent_weight = max(0.5, min(1.5, opponent_weight))
            
            # Combined weight
            combined_weight = time_weight * opponent_weight
            
            # Accumulate scores
            total_points += points
            weighted_points += points * combined_weight
            performance_ratings.append(performance)
            results.append(context.get('result', 'L'))
        
        # Calculate metrics
        matches_count = len(matches)
        raw_form_score = total_points / matches_count if matches_count > 0 else 0
        opponent_adjusted_form = weighted_points / sum([1.0 - (i * 0.05) for i in range(matches_count)]) if matches_count > 0 else 0
        avg_performance = sum(performance_ratings) / len(performance_ratings) if performance_ratings else 5.0
        
        # Consistency score (lower variance = higher consistency)
        if len(performance_ratings) > 1:
            variance = sum([(p - avg_performance) ** 2 for p in performance_ratings]) / len(performance_ratings)
            consistency_score = max(0, 10 - variance)  # 0-10 scale, higher = more consistent
        else:
            consistency_score = 5.0
        
        return {
            'raw_form_score': raw_form_score,
            'opponent_adjusted_form': opponent_adjusted_form,
            'performance_rating': avg_performance,
            'consistency_score': consistency_score,
            'matches_analyzed': matches_count,
            'recent_results': ''.join(results[:5])  # Last 5 results as string
        }
    
    def calculate_form_trend(self, matches: List[Dict], our_team_id: int) -> str:
        """Calculate trend direction from recent matches"""
        if len(matches) < 4:
            return "insufficient_data"
        
        # Split matches into two halves
        mid_point = len(matches) // 2
        recent_half = matches[:mid_point]  # More recent matches
        older_half = matches[mid_point:]   # Older matches
        
        # Calculate average performance for each half
        recent_performance = 0
        older_performance = 0
        
        for match in recent_half:
            points, _, _ = self.analyze_match_performance(match, our_team_id)
            recent_performance += points
        
        for match in older_half:
            points, _, _ = self.analyze_match_performance(match, our_team_id)
            older_performance += points
        
        recent_avg = recent_performance / len(recent_half) if recent_half else 0
        older_avg = older_performance / len(older_half) if older_half else 0
        
        # Determine trend
        if recent_avg > older_avg * 1.3:
            return "strongly_improving"
        elif recent_avg > older_avg * 1.1:
            return "improving"
        elif recent_avg < older_avg * 0.7:
            return "strongly_declining"
        elif recent_avg < older_avg * 0.9:
            return "declining"
        else:
            return "stable"
    
    def collect_data(self, team_id: str, competition_id: str) -> Dict[str, Any]:
        """
        Collect advanced form data for a team
        
        Args:
            team_id: Team identifier
            competition_id: Competition context
            
        Returns:
            Dictionary with comprehensive form analysis
        """
        # Convert team name to API ID if needed
        if isinstance(team_id, str) and not team_id.isdigit():
            api_team_id = self.get_api_team_id(team_id)
            if not api_team_id:
                raise DataCollectionError(f"Could not find API ID for team: {team_id}")
        else:
            api_team_id = int(team_id)
        
        # Get recent matches
        recent_matches = self.get_recent_matches(api_team_id, count=10)
        
        if not recent_matches:
            raise DataCollectionError(f"No recent matches found for team {api_team_id}")
        
        # Calculate opponent-adjusted form metrics
        form_metrics = self.calculate_opponent_adjusted_form(recent_matches, api_team_id)
        
        # Calculate trend
        form_trend = self.calculate_form_trend(recent_matches, api_team_id)
        
        # Additional analysis
        last_5_matches = recent_matches[:5]
        last_5_form = self.calculate_opponent_adjusted_form(last_5_matches, api_team_id)
        
        return {
            **form_metrics,
            'form_trend': form_trend,
            'last_5_form': last_5_form['raw_form_score'],
            'last_5_opponent_adjusted': last_5_form['opponent_adjusted_form'],
            'team_api_id': api_team_id,
            'collection_timestamp': datetime.now().isoformat()
        }
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate collected form data
        
        Args:
            data: Data to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = [
            'raw_form_score', 'opponent_adjusted_form', 
            'performance_rating', 'form_trend'
        ]
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                print(f"❌ Missing required field: {field}")
                return False
        
        # Validate ranges
        if not (0 <= data['raw_form_score'] <= 3):
            print(f"❌ Raw form score out of range: {data['raw_form_score']}")
            return False
        
        if not (0 <= data['performance_rating'] <= 10):
            print(f"❌ Performance rating out of range: {data['performance_rating']}")
            return False
        
        # Validate trend values
        valid_trends = [
            'strongly_improving', 'improving', 'stable', 
            'declining', 'strongly_declining', 'insufficient_data'
        ]
        if data['form_trend'] not in valid_trends:
            print(f"❌ Invalid trend value: {data['form_trend']}")
            return False
        
        return True


def main():
    """Test the Advanced Form Agent"""
    agent = AdvancedFormAgent()
    
    # Test with known teams
    test_teams = ["Manchester City", "Real Madrid", "Inter"]
    
    for team in test_teams:
        print(f"\n🧪 Testing Advanced Form Agent with {team}")
        try:
            result = agent.execute_collection(team, "Premier League")
            if result:
                data = result['data']
                print(f"✅ Raw Form Score: {data['raw_form_score']:.2f}")
                print(f"✅ Opponent Adjusted: {data['opponent_adjusted_form']:.2f}")
                print(f"✅ Performance Rating: {data['performance_rating']:.2f}")
                print(f"✅ Form Trend: {data['form_trend']}")
                print(f"✅ Recent Results: {data.get('recent_results', 'N/A')}")
            else:
                print(f"❌ Failed to collect data for {team}")
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()