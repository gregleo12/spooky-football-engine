#!/usr/bin/env python3
"""
Database Query Optimizations for Spooky Football Engine

This module contains optimized versions of the main database queries
with performance improvements including:
- Reduced JOIN operations
- Cached results
- Indexed field usage
- Batch operations
"""

from database_config import db_config
from functools import lru_cache
import time

class OptimizedQueries:
    def __init__(self):
        self._team_cache = {}
        self._cache_timestamp = 0
        self._cache_duration = 300  # 5 minutes
    
    def _is_cache_valid(self):
        """Check if cache is still valid"""
        return time.time() - self._cache_timestamp < self._cache_duration
    
    def _clear_cache(self):
        """Clear internal cache"""
        self._team_cache = {}
        self._cache_timestamp = 0
    
    def get_all_teams_optimized(self):
        """
        Optimized version of get_all_teams with caching and reduced complexity
        
        Optimizations:
        1. Cache results for 5 minutes
        2. Use direct league mapping instead of CASE statement
        3. Fetch only required columns
        4. Single-pass processing
        """
        if self._is_cache_valid() and 'all_teams' in self._team_cache:
            return self._team_cache['all_teams']
        
        # League order mapping
        league_order = {
            'Premier League': 1,
            'La Liga': 2, 
            'Serie A': 3,
            'Bundesliga': 4,
            'Ligue 1': 5,
            'International': 6
        }
        
        query = """
            SELECT 
                c.name as league,
                cts.team_name,
                cts.local_league_strength,
                cts.european_strength
            FROM competition_team_strength cts
            JOIN competitions c ON cts.competition_id = c.id
            WHERE c.name IN ('Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1', 'International')
            AND (cts.season = '2024' OR c.name = 'International')
            AND cts.local_league_strength IS NOT NULL
        """
        
        results = db_config.execute_query(query)
        
        # Process results in single pass
        teams_by_league = {league: [] for league in league_order.keys()}
        all_teams = []
        seen_teams = set()
        
        # Sort results by league order and team name
        sorted_results = sorted(results, key=lambda x: (league_order.get(x[0], 99), x[1]))
        
        for row in sorted_results:
            league, team, local, european = row
            team_key = f"{team}_{league}"
            
            if team_key not in seen_teams:
                seen_teams.add(team_key)
                team_data = {
                    'name': team,
                    'league': league,
                    'local_strength': local,
                    'european_strength': european
                }
                teams_by_league[league].append(team_data)
                all_teams.append(team_data)
        
        # Cache results
        self._team_cache['all_teams'] = (teams_by_league, all_teams)
        self._cache_timestamp = time.time()
        
        return teams_by_league, all_teams
    
    def get_team_data_optimized(self, team_name):
        """
        Optimized team data lookup with caching
        
        Optimizations:
        1. Cache individual team lookups
        2. Use parameterized query with database abstraction
        3. Single query with all needed fields
        """
        if self._is_cache_valid() and team_name in self._team_cache:
            return self._team_cache[team_name]
        
        query = """
            SELECT 
                c.name as league,
                cts.team_name,
                cts.local_league_strength,
                cts.european_strength,
                cts.elo_score,
                cts.squad_value_score
            FROM competition_team_strength cts
            JOIN competitions c ON cts.competition_id = c.id
            WHERE cts.team_name = %s
        """
        
        results = db_config.execute_query(query, (team_name,))
        
        if results:
            result = results[0]
            team_data = {
                'league': result[0],
                'name': result[1],
                'local_strength': result[2],
                'european_strength': result[3],
                'elo': result[4],
                'squad_value': result[5]
            }
            
            # Cache result
            self._team_cache[team_name] = team_data
            return team_data
        
        return None
    
    def get_teams_ranking_optimized(self):
        """
        Optimized teams ranking with pre-calculated strength scores
        
        Optimizations:
        1. Use COALESCE for better null handling
        2. Calculate strength in database instead of Python
        3. Direct ORDER BY for better performance
        4. Fetch only required columns
        """
        query = """
            SELECT 
                cts.team_name,
                c.name as league,
                COALESCE(cts.overall_strength, 
                    (COALESCE(cts.elo_score, 0) * 0.18 + 
                     COALESCE(cts.squad_value_score, 0) * 0.15 + 
                     COALESCE(cts.form_score, 0) * 0.05 + 
                     COALESCE(cts.squad_depth_score, 0) * 0.02 + 
                     COALESCE(cts.h2h_performance, 0) * 0.04 + 
                     COALESCE(cts.scoring_patterns, 0) * 0.03)) as calculated_strength,
                cts.elo_score,
                cts.squad_value_score,
                cts.form_score,
                cts.confederation
            FROM competition_team_strength cts
            JOIN competitions c ON cts.competition_id = c.id
            WHERE c.name IN ('Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1', 'International')
            AND (cts.season = '2024' OR c.name = 'International')
            AND (cts.overall_strength IS NOT NULL OR c.name = 'International')
            ORDER BY calculated_strength DESC
        """
        
        return db_config.execute_query(query)
    
    @lru_cache(maxsize=100)
    def get_head_to_head_cached(self, team1, team2):
        """
        Cached head-to-head lookup using LRU cache
        
        Optimizations:
        1. LRU cache for frequently requested matchups
        2. Normalized team name order for cache efficiency
        """
        # Normalize order for better cache hits
        if team1 > team2:
            team1, team2 = team2, team1
        
        # This would connect to actual H2H data when available
        # For now, return empty result
        return []
    
    def bulk_update_team_strength(self, team_updates):
        """
        Bulk update team strength scores
        
        Optimizations:
        1. Use executemany for batch operations
        2. Single transaction for all updates
        3. Parameterized queries for security
        """
        if not team_updates:
            return
        
        query = """
            UPDATE competition_team_strength 
            SET local_league_strength = %s, 
                european_strength = %s,
                elo_score = %s,
                squad_value_score = %s,
                form_score = %s,
                squad_depth_score = %s
            WHERE team_name = %s AND competition_id = (
                SELECT id FROM competitions WHERE name = %s
            )
        """
        
        params_list = [
            (
                update['local_strength'], 
                update['european_strength'],
                update['elo_score'],
                update['squad_value_score'], 
                update['form_score'],
                update['squad_depth_score'],
                update['team_name'],
                update['league']
            ) 
            for update in team_updates
        ]
        
        db_config.execute_many(query, params_list)
        
        # Clear cache after updates
        self._clear_cache()
    
    def get_database_stats(self):
        """
        Get database statistics with single query
        
        Optimizations:
        1. Use CTEs for complex calculations
        2. Single query instead of multiple round trips
        """
        query = """
            WITH stats AS (
                SELECT 
                    (SELECT COUNT(DISTINCT name) FROM teams) as total_teams,
                    (SELECT COUNT(DISTINCT name) FROM competitions) as total_competitions,
                    (SELECT COUNT(*) FROM competition_team_strength) as total_strength_records,
                    (SELECT COUNT(DISTINCT team_name) FROM competition_team_strength WHERE local_league_strength IS NOT NULL) as teams_with_data
            )
            SELECT 
                total_teams,
                total_competitions, 
                total_strength_records,
                teams_with_data,
                ROUND(teams_with_data * 100.0 / total_teams, 1) as data_coverage_percent
            FROM stats
        """
        
        results = db_config.execute_query(query)
        if results:
            row = results[0]
            return {
                'total_teams': row[0],
                'total_competitions': row[1],
                'total_strength_records': row[2],
                'teams_with_data': row[3],
                'data_coverage_percent': row[4]
            }
        return {}

# Global instance
optimized_queries = OptimizedQueries()