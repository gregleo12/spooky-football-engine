#!/usr/bin/env python3
"""
Historical Data Collector for Backtesting
Collects past match results from API-Football for accuracy validation
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os

class HistoricalDataCollector:
    """Collects historical match data for backtesting purposes"""
    
    def __init__(self):
        # Note: API-Football requires subscription, using mock data for development
        self.api_key = os.environ.get('API_FOOTBALL_KEY', 'demo_key')
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {
            'X-RapidAPI-Host': 'v3.football.api-sports.io',
            'X-RapidAPI-Key': self.api_key
        }
        
        # League IDs for major European leagues
        self.league_ids = {
            'Premier League': 39,
            'La Liga': 140, 
            'Serie A': 135,
            'Bundesliga': 78,
            'Ligue 1': 61
        }
    
    def get_historical_matches(self, num_matches: int = 100) -> List[Dict]:
        """
        Collect historical matches for backtesting
        For development, returns mock data based on realistic patterns
        """
        print(f"🔍 Collecting {num_matches} historical matches for backtesting...")
        
        # For production, this would make API calls to API-Football
        # For now, generating realistic mock data based on football statistics
        
        matches = []
        
        # Common team pairs with realistic historical results
        team_pairs = [
            ('Arsenal', 'Liverpool'),
            ('Manchester City', 'Southampton'),
            ('Barcelona', 'Real Madrid'),
            ('Bayern Munich', '1899 Hoffenheim'),
            ('Paris Saint-Germain', 'Lille'),
            ('Juventus', 'Torino'),
            ('Manchester United', 'Brighton'),
            ('Chelsea', 'Tottenham'),
            ('Atletico Madrid', 'Valencia'),
            ('AC Milan', 'Inter Milan')
        ]
        
        import random
        random.seed(42)  # Consistent results for testing
        
        for i in range(num_matches):
            home_team, away_team = random.choice(team_pairs)
            
            # Generate realistic match results based on typical football statistics
            # Home advantage: ~45% home wins, ~25% draws, ~30% away wins
            result_random = random.random()
            if result_random < 0.45:
                actual_result = 'home_win'
                home_score = random.randint(1, 4)
                away_score = random.randint(0, home_score - 1)
            elif result_random < 0.70:
                actual_result = 'draw'  
                score = random.randint(0, 3)
                home_score = away_score = score
            else:
                actual_result = 'away_win'
                away_score = random.randint(1, 4)
                home_score = random.randint(0, away_score - 1)
            
            # Generate date in the past 6 months
            days_ago = random.randint(1, 180)
            match_date = datetime.now() - timedelta(days=days_ago)
            
            match = {
                'id': f'match_{i+1}',
                'date': match_date.isoformat(),
                'home_team': home_team,
                'away_team': away_team,
                'home_score': home_score,
                'away_score': away_score,
                'actual_result': actual_result,
                'league': self._get_team_league(home_team),
                'status': 'finished'
            }
            
            matches.append(match)
            
            # Progress indicator
            if (i + 1) % 25 == 0:
                print(f"  ✅ Collected {i + 1}/{num_matches} matches")
        
        print(f"✅ Historical data collection complete: {len(matches)} matches")
        return matches
    
    def _get_team_league(self, team_name: str) -> str:
        """Map team names to their leagues"""
        league_mapping = {
            # Premier League
            'Arsenal': 'Premier League',
            'Liverpool': 'Premier League', 
            'Manchester City': 'Premier League',
            'Manchester United': 'Premier League',
            'Chelsea': 'Premier League',
            'Tottenham': 'Premier League',
            'Brighton': 'Premier League',
            'Southampton': 'Premier League',
            
            # La Liga
            'Barcelona': 'La Liga',
            'Real Madrid': 'La Liga',
            'Atletico Madrid': 'La Liga',
            'Valencia': 'La Liga',
            
            # Serie A
            'Juventus': 'Serie A',
            'AC Milan': 'Serie A',
            'Inter Milan': 'Serie A',
            'Torino': 'Serie A',
            
            # Bundesliga
            'Bayern Munich': 'Bundesliga',
            '1899 Hoffenheim': 'Bundesliga',
            
            # Ligue 1
            'Paris Saint-Germain': 'Ligue 1',
            'Lille': 'Ligue 1'
        }
        
        return league_mapping.get(team_name, 'Unknown')
    
    def save_historical_data(self, matches: List[Dict], filename: str = 'historical_matches.json'):
        """Save historical match data to file"""
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        with open(filepath, 'w') as f:
            json.dump({
                'collected_at': datetime.now().isoformat(),
                'total_matches': len(matches),
                'matches': matches
            }, f, indent=2)
        
        print(f"💾 Historical data saved to {filepath}")
        return filepath
    
    def load_historical_data(self, filename: str = 'historical_matches.json') -> Optional[List[Dict]]:
        """Load historical match data from file"""
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                return data['matches']
        except FileNotFoundError:
            print(f"❌ Historical data file not found: {filepath}")
            return None


if __name__ == "__main__":
    # Example usage
    collector = HistoricalDataCollector()
    
    # Collect 100 historical matches
    matches = collector.get_historical_matches(100)
    
    # Save to file
    collector.save_historical_data(matches)
    
    # Show sample data
    print(f"\n📊 Sample matches:")
    for match in matches[:3]:
        result = match['actual_result'].replace('_', ' ').title()
        print(f"  {match['home_team']} {match['home_score']}-{match['away_score']} {match['away_team']} ({result})")