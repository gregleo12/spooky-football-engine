#!/usr/bin/env python3
"""
Database Interface Module for Fresh Football Web App
Purpose-built for 10-parameter Railway PostgreSQL system
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import os
import time
from typing import List, Dict, Optional, Tuple

class DatabaseInterface:
    def __init__(self):
        # Railway PostgreSQL connection string (fallback to local if unavailable)
        self.database_url = os.environ.get('DATABASE_URL', 
            "postgresql://postgres:WJFojeyIZjCfJlRscgARcdrFAqDXKJhT@ballast.proxy.rlwy.net:10971/railway")
        self.connection_pool = []
        self.max_pool_size = 5
        
    @contextmanager
    def get_connection(self):
        """Get database connection with proper error handling"""
        conn = None
        try:
            conn = psycopg2.connect(self.database_url)
            yield conn
        except psycopg2.Error as e:
            print(f"Database error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def test_connection(self) -> bool:
        """Test database connectivity"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                return result[0] == 1
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
    
    def get_all_teams(self) -> Dict[str, List[Dict]]:
        """Get all teams organized by league"""
        query = """
            SELECT 
                cts.team_name,
                c.name as league,
                cts.elo_score,
                cts.squad_value_score
            FROM competition_team_strength cts
            JOIN competitions c ON cts.competition_id = c.id
            WHERE cts.season = '2024'
            ORDER BY c.name, cts.team_name
        """
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute(query)
                results = cursor.fetchall()
                
                # Organize by league
                teams_by_league = {}
                for row in results:
                    league = row['league']
                    if league not in teams_by_league:
                        teams_by_league[league] = []
                    teams_by_league[league].append({
                        'name': row['team_name'],
                        'elo_score': row['elo_score'],
                        'squad_value': row['squad_value_score']
                    })
                
                return teams_by_league
        except Exception as e:
            print(f"Error fetching teams: {e}")
            return {}
    
    def get_team_data(self, team_name: str) -> Optional[Dict]:
        """Get complete data for a specific team with all 10 parameters"""
        query = """
            SELECT 
                cts.*,
                c.name as league_name
            FROM competition_team_strength cts
            JOIN competitions c ON cts.competition_id = c.id
            WHERE cts.team_name = %s
            AND cts.season = '2024'
        """
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute(query, (team_name,))
                result = cursor.fetchone()
                
                if result:
                    # Extract all 10 parameters
                    return {
                        'team_name': result['team_name'],
                        'league': result['league_name'],
                        'parameters': {
                            'elo_score': result['elo_score'],
                            'form_score': result['form_score'],
                            'squad_value_score': result['squad_value_score'],
                            'squad_depth_score': result['squad_depth_score'],
                            'key_player_availability_score': result['key_player_availability_score'],
                            'motivation_factor_score': result['motivation_factor_score'],
                            'tactical_matchup_score': result['tactical_matchup_score'],
                            'offensive_rating': result['offensive_rating'],
                            'defensive_rating': result['defensive_rating'],
                            'h2h_performance_score': result['h2h_performance_score']
                        },
                        'normalized': {
                            'elo_normalized': result.get('elo_normalized'),
                            'form_normalized': result.get('form_normalized'),
                            'squad_value_normalized': result.get('squad_value_normalized'),
                            'squad_depth_normalized': result.get('squad_depth_normalized'),
                            'key_player_availability_normalized': result.get('key_player_availability_normalized'),
                            'motivation_factor_normalized': result.get('motivation_factor_normalized'),
                            'tactical_matchup_normalized': result.get('tactical_matchup_normalized'),
                            'offensive_normalized': result.get('offensive_normalized'),
                            'defensive_normalized': result.get('defensive_normalized'),
                            'h2h_performance_normalized': result.get('h2h_performance_normalized')
                        }
                    }
                return None
        except Exception as e:
            print(f"Error fetching team data: {e}")
            return None
    
    def get_system_stats(self) -> Dict:
        """Get system coverage statistics"""
        query = """
            WITH stats AS (
                SELECT 
                    COUNT(DISTINCT team_name) as total_teams,
                    COUNT(DISTINCT competition_id) as total_leagues,
                    COUNT(*) as total_records
                FROM competition_team_strength 
                WHERE season = '2024'
            ),
            parameter_coverage AS (
                SELECT 
                    COUNT(CASE WHEN elo_score IS NOT NULL THEN 1 END) as elo_coverage,
                    COUNT(CASE WHEN form_score IS NOT NULL THEN 1 END) as form_coverage,
                    COUNT(CASE WHEN squad_value_score IS NOT NULL THEN 1 END) as squad_value_coverage,
                    COUNT(CASE WHEN squad_depth_score IS NOT NULL THEN 1 END) as squad_depth_coverage,
                    COUNT(CASE WHEN key_player_availability_score IS NOT NULL THEN 1 END) as key_player_coverage,
                    COUNT(CASE WHEN motivation_factor_score IS NOT NULL THEN 1 END) as motivation_coverage,
                    COUNT(CASE WHEN tactical_matchup_score IS NOT NULL THEN 1 END) as tactical_coverage,
                    COUNT(CASE WHEN offensive_rating IS NOT NULL THEN 1 END) as offensive_coverage,
                    COUNT(CASE WHEN defensive_rating IS NOT NULL THEN 1 END) as defensive_coverage,
                    COUNT(CASE WHEN h2h_performance_score IS NOT NULL THEN 1 END) as h2h_coverage,
                    COUNT(*) as total_count
                FROM competition_team_strength
                WHERE season = '2024'
            )
            SELECT 
                s.total_teams,
                s.total_leagues,
                s.total_records,
                ROUND(p.elo_coverage * 100.0 / p.total_count, 1) as elo_coverage_pct,
                ROUND(p.form_coverage * 100.0 / p.total_count, 1) as form_coverage_pct,
                ROUND(p.squad_value_coverage * 100.0 / p.total_count, 1) as squad_value_coverage_pct,
                ROUND(p.squad_depth_coverage * 100.0 / p.total_count, 1) as squad_depth_coverage_pct,
                ROUND(p.key_player_coverage * 100.0 / p.total_count, 1) as key_player_coverage_pct,
                ROUND(p.motivation_coverage * 100.0 / p.total_count, 1) as motivation_coverage_pct,
                ROUND(p.tactical_coverage * 100.0 / p.total_count, 1) as tactical_coverage_pct,
                ROUND(p.offensive_coverage * 100.0 / p.total_count, 1) as offensive_coverage_pct,
                ROUND(p.defensive_coverage * 100.0 / p.total_count, 1) as defensive_coverage_pct,
                ROUND(p.h2h_coverage * 100.0 / p.total_count, 1) as h2h_coverage_pct
            FROM stats s, parameter_coverage p
        """
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute(query)
                return cursor.fetchone()
        except Exception as e:
            print(f"Error fetching system stats: {e}")
            return {}
    
    def compare_teams(self, team1: str, team2: str) -> Optional[Dict]:
        """Compare two teams head-to-head"""
        team1_data = self.get_team_data(team1)
        team2_data = self.get_team_data(team2)
        
        if not team1_data or not team2_data:
            return None
        
        # Calculate weighted strength scores
        weights = {
            'elo_score': 0.18,
            'squad_value_score': 0.15,
            'form_score': 0.05,
            'squad_depth_score': 0.02,
            'key_player_availability_score': 0.10,
            'motivation_factor_score': 0.10,
            'tactical_matchup_score': 0.10,
            'offensive_rating': 0.10,
            'defensive_rating': 0.10,
            'h2h_performance_score': 0.10
        }
        
        team1_strength = sum(
            float(team1_data['parameters'].get(param, 0) or 0) * weight 
            for param, weight in weights.items()
        )
        team2_strength = sum(
            float(team2_data['parameters'].get(param, 0) or 0) * weight 
            for param, weight in weights.items()
        )
        
        return {
            'team1': team1_data,
            'team2': team2_data,
            'team1_strength': team1_strength,
            'team2_strength': team2_strength,
            'same_league': team1_data['league'] == team2_data['league']
        }
    
    def execute_query(self, query: str, params: Tuple = None) -> List[Dict]:
        """Execute a custom query"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            print(f"Query execution error: {e}")
            return []

# Global instance
db = DatabaseInterface()