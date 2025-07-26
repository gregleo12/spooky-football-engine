#!/usr/bin/env python3
"""
Context Data Agent - Phase 1
Collects contextual factors: home advantage, motivation, fixture congestion
New agent for match context analysis
"""
import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from base_agent import BaseDataAgent, DataCollectionError

class ContextDataAgent(BaseDataAgent):
    """Collect contextual match factors for enhanced predictions"""
    
    def __init__(self):
        super().__init__("Context Data Agent")
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
    
    def get_home_away_records(self, team_id: int, competition_id: str = None) -> Tuple[Dict, Dict]:
        """Get separate home and away records for home advantage calculation"""
        try:
            league_id = self.get_primary_league_for_team(team_id)
            
            # Get home matches
            home_url = f"{self.base_url}/fixtures"
            home_params = {
                'team': team_id,
                'season': 2024,
                'league': league_id,
                'venue': 'home',
                'status': 'FT'
            }
            
            home_response = requests.get(home_url, headers=self.headers, params=home_params)
            home_matches = []
            if home_response.status_code == 200:
                home_data = home_response.json()
                home_matches = home_data.get('response', [])
            
            # Get away matches
            away_url = f"{self.base_url}/fixtures"
            away_params = {
                'team': team_id,
                'season': 2024,
                'league': league_id,
                'venue': 'away',
                'status': 'FT'
            }
            
            away_response = requests.get(away_url, headers=self.headers, params=away_params)
            away_matches = []
            if away_response.status_code == 200:
                away_data = away_response.json()
                away_matches = away_data.get('response', [])
            
            # Analyze records
            home_record = self.analyze_venue_record(home_matches, team_id, is_home=True)
            away_record = self.analyze_venue_record(away_matches, team_id, is_home=False)
            
            return home_record, away_record
            
        except Exception as e:
            print(f"❌ Error getting venue records for team {team_id}: {e}")
            return {}, {}
    
    def analyze_venue_record(self, matches: List[Dict], team_id: int, is_home: bool) -> Dict[str, Any]:
        """Analyze performance at home or away"""
        if not matches:
            return {
                'matches_played': 0,
                'wins': 0,
                'draws': 0,
                'losses': 0,
                'goals_for': 0,
                'goals_against': 0,
                'win_rate': 0.0,
                'points_per_game': 0.0,
                'goals_per_game': 0.0,
                'goals_conceded_per_game': 0.0
            }
        
        wins = draws = losses = 0
        total_goals_for = total_goals_against = 0
        
        for match in matches:
            try:
                home_team = match['teams']['home']
                away_team = match['teams']['away']
                home_goals = match['goals']['home'] or 0
                away_goals = match['goals']['away'] or 0
                
                if is_home:
                    # Team is playing at home
                    our_goals = home_goals
                    opponent_goals = away_goals
                else:
                    # Team is playing away
                    our_goals = away_goals
                    opponent_goals = home_goals
                
                total_goals_for += our_goals
                total_goals_against += opponent_goals
                
                # Determine result
                if our_goals > opponent_goals:
                    wins += 1
                elif our_goals == opponent_goals:
                    draws += 1
                else:
                    losses += 1
                    
            except (KeyError, TypeError, ValueError):
                continue
        
        total_matches = wins + draws + losses
        if total_matches == 0:
            return {
                'matches_played': 0,
                'wins': 0, 'draws': 0, 'losses': 0,
                'goals_for': 0, 'goals_against': 0,
                'win_rate': 0.0, 'points_per_game': 0.0,
                'goals_per_game': 0.0, 'goals_conceded_per_game': 0.0
            }
        
        total_points = (wins * 3) + (draws * 1)
        
        return {
            'matches_played': total_matches,
            'wins': wins,
            'draws': draws,
            'losses': losses,
            'goals_for': total_goals_for,
            'goals_against': total_goals_against,
            'win_rate': wins / total_matches,
            'points_per_game': total_points / total_matches,
            'goals_per_game': total_goals_for / total_matches,
            'goals_conceded_per_game': total_goals_against / total_matches
        }
    
    def calculate_home_advantage(self, home_record: Dict, away_record: Dict) -> Dict[str, float]:
        """Calculate home advantage metrics"""
        if not home_record.get('matches_played') or not away_record.get('matches_played'):
            return {
                'home_advantage_points': 0.0,
                'home_advantage_goals': 0.0,
                'home_advantage_defensive': 0.0,
                'overall_home_advantage': 0.0
            }
        
        # Points advantage (home PPG - away PPG)
        points_advantage = home_record['points_per_game'] - away_record['points_per_game']
        
        # Offensive advantage (home goals - away goals per game)
        goals_advantage = home_record['goals_per_game'] - away_record['goals_per_game']
        
        # Defensive advantage (away goals conceded - home goals conceded per game)
        defensive_advantage = away_record['goals_conceded_per_game'] - home_record['goals_conceded_per_game']
        
        # Overall home advantage (0-1 scale)
        # Normalize based on typical ranges
        normalized_points = max(-1, min(1, points_advantage / 1.5))  # -1.5 to +1.5 PPG range
        normalized_goals = max(-1, min(1, goals_advantage / 1.0))    # -1 to +1 goals range
        normalized_defense = max(-1, min(1, defensive_advantage / 1.0))  # -1 to +1 goals range
        
        overall_advantage = (normalized_points * 0.5) + (normalized_goals * 0.25) + (normalized_defense * 0.25)
        overall_advantage = (overall_advantage + 1) / 2  # Convert to 0-1 scale
        
        return {
            'home_advantage_points': points_advantage,
            'home_advantage_goals': goals_advantage,
            'home_advantage_defensive': defensive_advantage,
            'overall_home_advantage': overall_advantage,
            'home_win_rate': home_record['win_rate'],
            'away_win_rate': away_record['win_rate']
        }
    
    def get_league_standings(self, team_id: int) -> Optional[Dict]:
        """Get current league standings for motivation calculation"""
        try:
            league_id = self.get_primary_league_for_team(team_id)
            
            url = f"{self.base_url}/standings"
            params = {
                'season': 2024,
                'league': league_id
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return None
                
            data = response.json()
            if not data.get('response'):
                return None
            
            standings = data['response'][0]['league']['standings'][0]  # Get main standings
            return standings
            
        except Exception as e:
            print(f"⚠️ Error getting standings: {e}")
            return None
    
    def calculate_motivation_factor(self, team_id: int, standings: List[Dict]) -> Dict[str, float]:
        """Calculate motivation based on league position and objectives"""
        if not standings:
            return {
                'current_position': 10,
                'points': 0,
                'motivation_factor': 0.5,
                'title_race_motivation': 0.0,
                'relegation_motivation': 0.0,
                'european_motivation': 0.0
            }
        
        # Find team in standings
        team_standing = None
        for team in standings:
            if team['team']['id'] == team_id:
                team_standing = team
                break
        
        if not team_standing:
            return {
                'current_position': 10,
                'points': 0,
                'motivation_factor': 0.5,
                'title_race_motivation': 0.0,
                'relegation_motivation': 0.0,
                'european_motivation': 0.0
            }
        
        position = team_standing['rank']
        points = team_standing['points']
        total_teams = len(standings)
        
        # Calculate different motivation factors
        
        # Title race motivation (top 4 positions)
        if position <= 4:
            title_race_motivation = 1.0 - ((position - 1) / 3)  # 1.0 for 1st, 0.67 for 2nd, etc.
        else:
            title_race_motivation = 0.0
        
        # European qualification motivation (positions 5-7)
        if 5 <= position <= 7:
            european_motivation = 0.8 - ((position - 5) * 0.2)
        elif position <= 4:
            european_motivation = 1.0  # Also motivated for European spots
        else:
            european_motivation = 0.0
        
        # Relegation battle motivation (bottom 6 positions)
        if position > total_teams - 6:
            relegation_motivation = 1.0 - ((total_teams - position) / 6)
        else:
            relegation_motivation = 0.0
        
        # Overall motivation (highest of the three factors)
        overall_motivation = max(title_race_motivation, european_motivation, relegation_motivation)
        
        # Add base motivation (mid-table teams still have some motivation)
        if overall_motivation < 0.3:
            overall_motivation = 0.3
        
        return {
            'current_position': position,
            'points': points,
            'motivation_factor': overall_motivation,
            'title_race_motivation': title_race_motivation,
            'relegation_motivation': relegation_motivation,
            'european_motivation': european_motivation,
            'total_teams_in_league': total_teams
        }
    
    def get_recent_fixture_congestion(self, team_id: int) -> Dict[str, float]:
        """Calculate fixture congestion and fatigue factors"""
        try:
            # Get fixtures from last 30 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            url = f"{self.base_url}/fixtures"
            params = {
                'team': team_id,
                'from': start_date.strftime('%Y-%m-%d'),
                'to': end_date.strftime('%Y-%m-%d'),
                'status': 'FT'
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return {'fixture_density': 0.0, 'days_since_last_match': 7}
            
            data = response.json()
            matches = data.get('response', [])
            
            if not matches:
                return {'fixture_density': 0.0, 'days_since_last_match': 7}
            
            # Calculate fixture density (matches per week)
            fixture_density = len(matches) / 4.3  # 30 days / 7 days per week
            
            # Days since last match
            latest_match = max(matches, key=lambda m: m['fixture']['date'])
            latest_date = datetime.fromisoformat(latest_match['fixture']['date'].replace('Z', '+00:00'))
            days_since_last = (datetime.now(latest_date.tzinfo) - latest_date).days
            
            return {
                'fixture_density': fixture_density,
                'days_since_last_match': days_since_last,
                'matches_last_30_days': len(matches)
            }
            
        except Exception as e:
            print(f"⚠️ Error getting fixture congestion for team {team_id}: {e}")
            return {'fixture_density': 1.0, 'days_since_last_match': 7}
    
    def collect_data(self, team_id: str, competition_id: str) -> Dict[str, Any]:
        """
        Collect contextual match factors for a team
        
        Args:
            team_id: Team identifier
            competition_id: Competition context
            
        Returns:
            Dictionary with home advantage, motivation, and fixture data
        """
        # Convert team name to API ID if needed
        if isinstance(team_id, str) and not team_id.isdigit():
            api_team_id = self.get_api_team_id(team_id)
            if not api_team_id:
                raise DataCollectionError(f"Could not find API ID for team: {team_id}")
        else:
            api_team_id = int(team_id)
        
        # Get home and away records
        home_record, away_record = self.get_home_away_records(api_team_id, competition_id)
        
        # Calculate home advantage
        home_advantage_metrics = self.calculate_home_advantage(home_record, away_record)
        
        # Get league standings for motivation
        standings = self.get_league_standings(api_team_id)
        motivation_metrics = self.calculate_motivation_factor(api_team_id, standings)
        
        # Get fixture congestion
        congestion_metrics = self.get_recent_fixture_congestion(api_team_id)
        
        return {
            # Home advantage metrics
            **home_advantage_metrics,
            
            # Home/away performance breakdown
            'home_matches_played': home_record.get('matches_played', 0),
            'away_matches_played': away_record.get('matches_played', 0),
            'home_points_per_game': home_record.get('points_per_game', 0.0),
            'away_points_per_game': away_record.get('points_per_game', 0.0),
            'home_goals_per_game': home_record.get('goals_per_game', 0.0),
            'away_goals_per_game': away_record.get('goals_per_game', 0.0),
            
            # Motivation and league position
            **motivation_metrics,
            
            # Fixture congestion and fatigue
            **congestion_metrics,
            
            # Metadata
            'team_api_id': api_team_id,
            'collection_timestamp': datetime.now().isoformat()
        }
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate collected context data
        
        Args:
            data: Data to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = [
            'overall_home_advantage', 'motivation_factor', 
            'current_position', 'fixture_density'
        ]
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                print(f"❌ Missing required field: {field}")
                return False
        
        # Validate ranges
        if not (0 <= data['overall_home_advantage'] <= 1):
            print(f"❌ Home advantage out of range: {data['overall_home_advantage']}")
            return False
        
        if not (0 <= data['motivation_factor'] <= 1):
            print(f"❌ Motivation factor out of range: {data['motivation_factor']}")
            return False
        
        if not (1 <= data['current_position'] <= 25):
            print(f"❌ League position out of range: {data['current_position']}")
            return False
        
        if not (0 <= data['fixture_density'] <= 5):
            print(f"❌ Fixture density out of range: {data['fixture_density']}")
            return False
        
        return True


def main():
    """Test the Context Data Agent"""
    agent = ContextDataAgent()
    
    # Test with known teams
    test_teams = ["Manchester City", "Real Madrid", "Inter"]
    
    for team in test_teams:
        print(f"\n🧪 Testing Context Data Agent with {team}")
        try:
            result = agent.execute_collection(team, "Premier League")
            if result:
                data = result['data']
                print(f"✅ Home advantage: {data['overall_home_advantage']:.2f}")
                print(f"✅ Motivation factor: {data['motivation_factor']:.2f}")
                print(f"✅ League position: {data['current_position']}")
                print(f"✅ Fixture density: {data['fixture_density']:.2f}")
                print(f"✅ Days since last match: {data['days_since_last_match']}")
                print(f"✅ Home PPG: {data['home_points_per_game']:.2f}")
                print(f"✅ Away PPG: {data['away_points_per_game']:.2f}")
            else:
                print(f"❌ Failed to collect data for {team}")
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()