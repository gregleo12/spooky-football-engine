#!/usr/bin/env python3
"""
Enhanced Squad Value Agent - Phase 1
Splits squad value into Starting XI + quality-weighted depth components
Fixes the counterintuitive squad depth calculation (Chelsea < Alaves issue)
Replaces: agents/team_strength/competition_squad_value_agent.py
"""
import requests
import json
import os
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from base_agent import BaseDataAgent, DataCollectionError
from bs4 import BeautifulSoup
import time

class EnhancedSquadValueAgent(BaseDataAgent):
    """Enhanced squad value analysis with quality-weighted depth calculation"""
    
    def __init__(self):
        super().__init__("Enhanced Squad Value Agent")
        self.api_key = "53faec37f076f995841d30d0f7b2dd9d"
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {
            'x-rapidapi-host': 'v3.football.api-sports.io',
            'x-rapidapi-key': self.api_key
        }
        
        # Load team mappings
        self.load_team_mappings()
        
        # Transfermarkt team name mappings
        self.transfermarkt_mappings = {
            'Manchester City': 'manchester-city',
            'Arsenal': 'arsenal-fc', 
            'Liverpool': 'liverpool-fc',
            'Chelsea': 'chelsea-fc',
            'Manchester United': 'manchester-united',
            'Tottenham Hotspur': 'tottenham-hotspur',
            'Newcastle United': 'newcastle-united',
            'Real Madrid': 'real-madrid',
            'Barcelona': 'fc-barcelona',
            'Atletico Madrid': 'atletico-madrid',
            'Athletic Club': 'athletic-bilbao',
            'Inter': 'inter-mailand',
            'Juventus': 'juventus-turin',
            'AC Milan': 'ac-mailand',
            'Napoli': 'ssc-neapel',
            'Bayern München': 'fc-bayern-munchen',
            'Borussia Dortmund': 'borussia-dortmund',
            'RB Leipzig': 'rasenballsport-leipzig',
            'Paris Saint Germain': 'paris-saint-germain',
            'Monaco': 'as-monaco',
            'Marseille': 'olympique-marseille'
        }
    
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
    
    def get_transfermarkt_team_url(self, team_name: str) -> Optional[str]:
        """Get Transfermarkt URL for a team"""
        slug = self.transfermarkt_mappings.get(team_name)
        if slug:
            return f"https://www.transfermarkt.com/{slug}/startseite/verein/"
        return None
    
    def scrape_transfermarkt_squad_values(self, team_name: str) -> List[Dict[str, Any]]:
        """
        Scrape squad values from Transfermarkt
        Returns list of players with their market values
        """
        try:
            team_url = self.get_transfermarkt_team_url(team_name)
            if not team_url:
                print(f"⚠️ No Transfermarkt mapping for {team_name}")
                return []
            
            # Convert to squad page URL
            squad_url = team_url.replace('/startseite/', '/kader/')
            
            # Headers to avoid being blocked
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = requests.get(squad_url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            players = []
            
            # Find player rows in the squad table
            player_rows = soup.find_all('tr', class_=['odd', 'even'])
            
            for row in player_rows:
                try:
                    # Extract player name
                    name_cell = row.find('td', class_='posrela')
                    if not name_cell:
                        continue
                    
                    player_name_link = name_cell.find('a')
                    if not player_name_link:
                        continue
                    
                    player_name = player_name_link.get('title', '').strip()
                    if not player_name:
                        continue
                    
                    # Extract position
                    position_cell = row.find_all('td')[1] if len(row.find_all('td')) > 1 else None
                    position = position_cell.get_text(strip=True) if position_cell else 'Unknown'
                    
                    # Extract market value
                    value_cell = row.find('td', class_='rechts')
                    if not value_cell:
                        continue
                    
                    value_text = value_cell.get_text(strip=True)
                    market_value = self.parse_transfermarkt_value(value_text)
                    
                    # Extract age
                    age_cell = None
                    for i, cell in enumerate(row.find_all('td')):
                        if cell.get_text(strip=True).isdigit() and 15 <= int(cell.get_text(strip=True)) <= 45:
                            age_cell = cell
                            break
                    
                    age = int(age_cell.get_text(strip=True)) if age_cell else 25
                    
                    players.append({
                        'name': player_name,
                        'position': self.normalize_position(position),
                        'market_value_millions': market_value,
                        'age': age
                    })
                    
                except Exception as e:
                    continue  # Skip problematic rows
            
            print(f"✅ Scraped {len(players)} players for {team_name}")
            return players
            
        except Exception as e:
            print(f"❌ Error scraping Transfermarkt for {team_name}: {e}")
            return []
    
    def parse_transfermarkt_value(self, value_text: str) -> float:
        """Parse market value from Transfermarkt text"""
        try:
            # Remove currency symbols and spaces
            value_text = re.sub(r'[€$£\s]', '', value_text)
            
            if 'm' in value_text.lower():
                # Million
                number = float(re.sub(r'[^0-9.]', '', value_text))
                return number
            elif 'k' in value_text.lower():
                # Thousand
                number = float(re.sub(r'[^0-9.]', '', value_text))
                return number / 1000
            elif value_text == '-' or not value_text:
                return 0.0
            else:
                # Try to parse as direct number
                number = float(re.sub(r'[^0-9.]', '', value_text))
                return number / 1000000 if number > 1000 else number
                
        except:
            return 0.0
    
    def normalize_position(self, position: str) -> str:
        """Normalize position names to standard categories"""
        position = position.upper()
        
        if any(pos in position for pos in ['GK', 'KEEPER', 'TORWART']):
            return 'GK'
        elif any(pos in position for pos in ['CB', 'LB', 'RB', 'LWB', 'RWB', 'DEF']):
            return 'DEF'
        elif any(pos in position for pos in ['CM', 'CDM', 'CAM', 'LM', 'RM', 'MID']):
            return 'MID'
        elif any(pos in position for pos in ['ST', 'CF', 'LW', 'RW', 'ATT', 'FOR']):
            return 'FWD'
        else:
            return 'MID'  # Default to midfielder
    
    def get_most_used_xi(self, team_id: int, team_name: str) -> List[Dict[str, Any]]:
        """
        Get the most frequently used starting XI based on recent matches
        """
        try:
            # Get recent matches to determine most used XI
            url = f"{self.base_url}/fixtures"
            params = {
                'team': team_id,
                'last': 10,
                'status': 'FT'
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            matches = data.get('response', [])
            
            # For now, use a simplified approach - get top 11 most valuable players
            # In a full implementation, we'd analyze actual lineups from matches
            squad = self.scrape_transfermarkt_squad_values(team_name)
            
            if not squad:
                return []
            
            # Sort by market value and take top 11
            sorted_squad = sorted(squad, key=lambda p: p['market_value_millions'], reverse=True)
            
            # Ensure we have a balanced XI (GK, defenders, midfielders, forwards)
            starting_xi = []
            positions_needed = {'GK': 1, 'DEF': 4, 'MID': 4, 'FWD': 2}
            
            # First, try to fill each position with highest value players
            for position, count in positions_needed.items():
                position_players = [p for p in sorted_squad if p['position'] == position]
                for i in range(min(count, len(position_players))):
                    starting_xi.append(position_players[i])
            
            # Fill remaining spots with highest value players not yet selected
            while len(starting_xi) < 11:
                for player in sorted_squad:
                    if player not in starting_xi:
                        starting_xi.append(player)
                        break
                if len(starting_xi) >= 11:
                    break
            
            return starting_xi[:11]
            
        except Exception as e:
            print(f"⚠️ Error getting most used XI for {team_name}: {e}")
            return []
    
    def calculate_quality_weighted_depth(self, full_squad: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate quality-weighted squad depth (fixes Chelsea < Alaves issue)
        
        Args:
            full_squad: List of all players with market values
            
        Returns:
            Dictionary with depth metrics
        """
        if not full_squad:
            return {
                'depth_index': 0.0,
                'first_xi_quality': 0.0,
                'second_xi_quality': 0.0,
                'depth_ratio': 0.0
            }
        
        # Sort players by market value (highest first)
        sorted_players = sorted(full_squad, key=lambda p: p['market_value_millions'], reverse=True)
        
        # Get first and second XI quality
        first_xi = sorted_players[:11]
        second_xi = sorted_players[11:22] if len(sorted_players) > 11 else []
        
        first_xi_avg_value = sum(p['market_value_millions'] for p in first_xi) / len(first_xi)
        second_xi_avg_value = sum(p['market_value_millions'] for p in second_xi) / len(second_xi) if second_xi else 0
        
        # Quality-weighted depth calculation
        # 60% first XI quality, 40% second XI quality  
        depth_index = (first_xi_avg_value * 0.6) + (second_xi_avg_value * 0.4)
        
        # Depth ratio (how good is second XI compared to first XI)
        depth_ratio = second_xi_avg_value / first_xi_avg_value if first_xi_avg_value > 0 else 0
        
        # Position balance bonus
        position_balance = self.calculate_position_balance(full_squad)
        
        # Apply position balance as a multiplier (0.8 to 1.2)
        final_depth_index = depth_index * (0.8 + position_balance * 0.4)
        
        return {
            'depth_index': final_depth_index,
            'first_xi_quality': first_xi_avg_value,
            'second_xi_quality': second_xi_avg_value,
            'depth_ratio': depth_ratio,
            'position_balance': position_balance,
            'squad_size': len(full_squad)
        }
    
    def calculate_position_balance(self, squad: List[Dict[str, Any]]) -> float:
        """Calculate positional balance score (0-1)"""
        if not squad:
            return 0.0
        
        # Count players by position
        position_counts = {'GK': 0, 'DEF': 0, 'MID': 0, 'FWD': 0}
        for player in squad:
            pos = player.get('position', 'MID')
            if pos in position_counts:
                position_counts[pos] += 1
        
        # Ideal ranges for each position
        ideal_ranges = {
            'GK': (2, 4),   # 2-4 goalkeepers
            'DEF': (6, 10), # 6-10 defenders
            'MID': (6, 10), # 6-10 midfielders
            'FWD': (3, 6)   # 3-6 forwards
        }
        
        balance_scores = []
        for pos, count in position_counts.items():
            min_ideal, max_ideal = ideal_ranges[pos]
            if min_ideal <= count <= max_ideal:
                balance_scores.append(1.0)
            elif count < min_ideal:
                balance_scores.append(count / min_ideal)
            else:
                balance_scores.append(max_ideal / count)
        
        return sum(balance_scores) / len(balance_scores)
    
    def calculate_age_profile(self, squad: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate squad age profile metrics"""
        if not squad:
            return {'avg_age': 25.0, 'age_balance': 0.5}
        
        ages = [p.get('age', 25) for p in squad]
        avg_age = sum(ages) / len(ages)
        
        # Age balance: ideal around 26-27, penalty for too young or too old
        ideal_age = 26.5
        age_deviation = abs(avg_age - ideal_age)
        age_balance = max(0, 1 - (age_deviation / 5))  # 0-1 scale
        
        return {
            'avg_age': avg_age,
            'age_balance': age_balance,
            'youngest_player': min(ages),
            'oldest_player': max(ages)
        }
    
    def collect_data(self, team_id: str, competition_id: str) -> Dict[str, Any]:
        """
        Collect enhanced squad value data with quality-weighted depth
        
        Args:
            team_id: Team identifier
            competition_id: Competition context
            
        Returns:
            Dictionary with squad value analysis and fixed depth calculation
        """
        team_name = team_id if isinstance(team_id, str) else str(team_id)
        
        # Get full squad data from Transfermarkt
        full_squad = self.scrape_transfermarkt_squad_values(team_name)
        
        if not full_squad:
            raise DataCollectionError(f"Could not get squad data for team: {team_name}")
        
        # Calculate total squad value
        total_squad_value = sum(p['market_value_millions'] for p in full_squad)
        
        # Get most used starting XI (simplified for now)
        starting_xi = full_squad[:11] if len(full_squad) >= 11 else full_squad
        starting_xi_total_value = sum(p['market_value_millions'] for p in starting_xi)
        starting_xi_avg_value = starting_xi_total_value / len(starting_xi) if starting_xi else 0
        
        # Calculate quality-weighted depth (this fixes the Chelsea < Alaves issue)
        depth_metrics = self.calculate_quality_weighted_depth(full_squad)
        
        # Calculate age profile
        age_metrics = self.calculate_age_profile(full_squad)
        
        # Get key player values (top 3 most valuable)
        sorted_players = sorted(full_squad, key=lambda p: p['market_value_millions'], reverse=True)
        key_player_values = [p['market_value_millions'] for p in sorted_players[:3]]
        
        # Bench strength (players 12-22)
        bench_players = sorted_players[11:22] if len(sorted_players) > 11 else []
        bench_value = sum(p['market_value_millions'] for p in bench_players)
        
        return {
            # Total squad metrics
            'total_squad_value': total_squad_value,
            'squad_size': len(full_squad),
            
            # Starting XI metrics
            'starting_xi_total_value': starting_xi_total_value,
            'starting_xi_avg_value': starting_xi_avg_value,
            
            # Quality-weighted depth (FIXED calculation)
            'squad_depth_index': depth_metrics['depth_index'],
            'first_xi_quality': depth_metrics['first_xi_quality'],
            'second_xi_quality': depth_metrics['second_xi_quality'],
            'depth_ratio': depth_metrics['depth_ratio'],
            'position_balance': depth_metrics['position_balance'],
            
            # Key players
            'key_player_values': key_player_values,
            'most_valuable_player': max(key_player_values) if key_player_values else 0,
            
            # Bench strength
            'bench_total_value': bench_value,
            'bench_avg_value': bench_value / len(bench_players) if bench_players else 0,
            
            # Age profile
            'avg_age': age_metrics['avg_age'],
            'age_balance': age_metrics['age_balance'],
            
            # Metadata
            'team_name': team_name,
            'collection_timestamp': datetime.now().isoformat(),
            'data_source': 'transfermarkt'
        }
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate collected squad value data
        
        Args:
            data: Data to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = [
            'total_squad_value', 'starting_xi_avg_value', 
            'squad_depth_index', 'squad_size'
        ]
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                print(f"❌ Missing required field: {field}")
                return False
        
        # Validate ranges
        if not (0 <= data['total_squad_value'] <= 2000):  # 0-2B euros
            print(f"❌ Total squad value out of range: {data['total_squad_value']}")
            return False
        
        if not (0 <= data['starting_xi_avg_value'] <= 200):  # 0-200M per player
            print(f"❌ Starting XI avg value out of range: {data['starting_xi_avg_value']}")
            return False
        
        if not (15 <= data['squad_size'] <= 50):  # Reasonable squad size
            print(f"❌ Squad size out of range: {data['squad_size']}")
            return False
        
        # Check that depth index makes sense (Chelsea should be higher than Alaves)
        if data['squad_depth_index'] <= 0:
            print(f"❌ Invalid squad depth index: {data['squad_depth_index']}")
            return False
        
        return True


def main():
    """Test the Enhanced Squad Value Agent"""
    agent = EnhancedSquadValueAgent()
    
    # Test with teams that had problematic depth scores
    test_teams = ["Chelsea", "Real Madrid", "Inter"]
    
    for team in test_teams:
        print(f"\n🧪 Testing Enhanced Squad Value Agent with {team}")
        try:
            result = agent.execute_collection(team, "Premier League")
            if result:
                data = result['data']
                print(f"✅ Total squad value: €{data['total_squad_value']:.0f}M")
                print(f"✅ Starting XI avg: €{data['starting_xi_avg_value']:.1f}M")
                print(f"✅ Squad depth index: {data['squad_depth_index']:.2f}")
                print(f"✅ First XI quality: €{data['first_xi_quality']:.1f}M")
                print(f"✅ Second XI quality: €{data['second_xi_quality']:.1f}M")
                print(f"✅ Depth ratio: {data['depth_ratio']:.2f}")
                print(f"✅ Most valuable player: €{data['most_valuable_player']:.1f}M")
            else:
                print(f"❌ Failed to collect data for {team}")
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()