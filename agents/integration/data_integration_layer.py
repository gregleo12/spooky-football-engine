#!/usr/bin/env python3
"""
Data Integration Layer - Phase 2
Connects Phase 1 data collection agents to the enhanced database schema
Handles data flow from agents to dedicated parameter tables
"""
import sys
import os
import sqlite3
import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

# Add data collection agents to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'data_collection_v2'))

from enhanced_elo_agent import EnhancedELOAgent
from advanced_form_agent import AdvancedFormAgent
from goals_data_agent import GoalsDataAgent
from enhanced_squad_value_agent import EnhancedSquadValueAgent
from context_data_agent import ContextDataAgent
from data_validation_framework_clean import DataValidationFramework

class DataIntegrationLayer:
    """
    Integration layer that connects Phase 1 data collection agents 
    to the Phase 2 enhanced database schema
    """
    
    def __init__(self, db_path: str = "db/football_strength.db"):
        self.db_path = db_path
        self.agents = {
            'elo': EnhancedELOAgent(),
            'form': AdvancedFormAgent(),
            'goals': GoalsDataAgent(),
            'squad': EnhancedSquadValueAgent(),
            'context': ContextDataAgent()
        }
        self.validator = DataValidationFramework()
        
    def get_database_connection(self) -> sqlite3.Connection:
        """Get database connection with foreign keys enabled"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def get_team_competition_info(self, team_name: str, competition_name: str = None) -> Optional[Tuple[str, str]]:
        """
        Get team_id and competition_id from database
        
        Args:
            team_name: Name of the team
            competition_name: Optional competition name (defaults to team's primary competition)
            
        Returns:
            Tuple of (team_id, competition_id) or None if not found
        """
        conn = self.get_database_connection()
        c = conn.cursor()
        
        try:
            if competition_name:
                # Get specific competition
                c.execute("""
                    SELECT ct.team_id, ct.competition_id 
                    FROM competition_teams ct
                    JOIN competitions comp ON ct.competition_id = comp.id
                    WHERE ct.team_name = ? AND comp.name = ?
                """, (team_name, competition_name))
            else:
                # Get team's primary competition (first found)
                c.execute("""
                    SELECT team_id, competition_id 
                    FROM competition_teams 
                    WHERE team_name = ? 
                    LIMIT 1
                """, (team_name,))
            
            result = c.fetchone()
            return result if result else None
            
        finally:
            conn.close()
    
    def collect_and_integrate_team_data(self, team_name: str, competition_name: str = None) -> Dict[str, Any]:
        """
        Collect data from all agents and integrate into database
        
        Args:
            team_name: Team to collect data for
            competition_name: Competition context (optional)
            
        Returns:
            Integration results summary
        """
        print(f"🔄 INTEGRATING DATA FOR {team_name}")
        print("="*60)
        
        # Get team and competition IDs
        team_comp_info = self.get_team_competition_info(team_name, competition_name)
        if not team_comp_info:
            return {'error': f'Team {team_name} not found in database'}
        
        team_id, competition_id = team_comp_info
        
        integration_results = {
            'team_name': team_name,
            'team_id': team_id,
            'competition_id': competition_id,
            'timestamp': datetime.now().isoformat(),
            'agent_results': {},
            'database_updates': {},
            'validation_results': {},
            'overall_success': True
        }
        
        # Process each agent
        for agent_name, agent in self.agents.items():
            print(f"\n📊 Processing {agent_name.capitalize()} Agent...")
            
            try:
                # Collect data from agent
                result = agent.execute_collection(team_name, competition_name or "Premier League")
                
                if result is None:
                    integration_results['agent_results'][agent_name] = {
                        'success': False,
                        'error': 'Agent returned None'
                    }
                    integration_results['overall_success'] = False
                    continue
                
                # Validate data
                validation_result = self.validator.validate_agent_data(agent_name, result['data'])
                integration_results['validation_results'][agent_name] = validation_result
                
                if not validation_result['success']:
                    integration_results['agent_results'][agent_name] = {
                        'success': False,
                        'error': 'Data validation failed',
                        'validation_issues': validation_result
                    }
                    integration_results['overall_success'] = False
                    continue
                
                # Integrate data into database
                db_result = self.integrate_agent_data(
                    agent_name, team_id, competition_id, result
                )
                
                integration_results['agent_results'][agent_name] = {
                    'success': True,
                    'data_quality': validation_result['data_quality'],
                    'records_updated': db_result['records_updated']
                }
                integration_results['database_updates'][agent_name] = db_result
                
                print(f"  ✅ {agent_name.capitalize()}: SUCCESS (Quality: {validation_result['data_quality']:.1f}%)")
                
            except Exception as e:
                integration_results['agent_results'][agent_name] = {
                    'success': False,
                    'error': str(e)
                }
                integration_results['overall_success'] = False
                print(f"  ❌ {agent_name.capitalize()}: ERROR - {e}")
        
        # Update main competition_team_strength table
        self.update_main_strength_table(team_id, competition_id, integration_results)
        
        return integration_results
    
    def integrate_agent_data(self, agent_name: str, team_id: str, competition_id: str, 
                           agent_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Integrate specific agent data into appropriate database table
        
        Args:
            agent_name: Name of the agent (elo, form, goals, squad, context)
            team_id: Team UUID
            competition_id: Competition UUID  
            agent_result: Result from agent execution
            
        Returns:
            Database integration results
        """
        data = agent_result['data']
        metadata = agent_result['metadata']
        
        conn = self.get_database_connection()
        c = conn.cursor()
        
        try:
            if agent_name == 'elo':
                return self._integrate_elo_data(c, team_id, competition_id, data, metadata)
            elif agent_name == 'form':
                return self._integrate_form_data(c, team_id, competition_id, data, metadata)
            elif agent_name == 'goals':
                return self._integrate_goals_data(c, team_id, competition_id, data, metadata)
            elif agent_name == 'squad':
                return self._integrate_squad_data(c, team_id, competition_id, data, metadata)
            elif agent_name == 'context':
                return self._integrate_context_data(c, team_id, competition_id, data, metadata)
            else:
                raise ValueError(f"Unknown agent: {agent_name}")
                
        finally:
            conn.commit()
            conn.close()
    
    def _integrate_elo_data(self, cursor, team_id: str, competition_id: str, 
                           data: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate ELO agent data into team_elo_data table"""
        
        # Calculate additional metrics
        elo_change = data.get('recent_form_elo', 1500) - data.get('standard_elo', 1500)
        
        cursor.execute("""
            INSERT OR REPLACE INTO team_elo_data (
                id, team_id, competition_id, season,
                standard_elo, recent_form_elo, elo_trend,
                elo_change_last_5, matches_analyzed, recent_matches_weighted,
                last_updated, data_confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()), team_id, competition_id, "2024",
            data.get('standard_elo'),
            data.get('recent_form_elo'),
            data.get('elo_trend'),
            elo_change,
            data.get('matches_analyzed', 0),
            data.get('recent_matches_count', 5),
            datetime.now().isoformat(),
            metadata.get('confidence_level', 1.0)
        ))
        
        self._log_data_collection_audit(cursor, team_id, competition_id, 'enhanced_elo', metadata)
        
        return {'records_updated': 1, 'table': 'team_elo_data'}
    
    def _integrate_form_data(self, cursor, team_id: str, competition_id: str,
                            data: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate Form agent data into team_form_data table"""
        
        # Serialize last 5 results if available
        last_5_results = json.dumps(data.get('last_5_results', []))
        
        cursor.execute("""
            INSERT OR REPLACE INTO team_form_data (
                id, team_id, competition_id, season,
                raw_form_score, opponent_adjusted_form, form_trend, form_consistency,
                performance_variance, last_5_results, matches_analyzed, avg_opponent_strength,
                last_updated, data_confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()), team_id, competition_id, "2024",
            data.get('raw_form_score'),
            data.get('opponent_adjusted_form'),
            data.get('form_trend'),
            data.get('form_consistency'),
            data.get('performance_variance', 0.0),
            last_5_results,
            data.get('matches_analyzed', 0),
            data.get('avg_opponent_strength', 0.0),
            datetime.now().isoformat(),
            metadata.get('confidence_level', 1.0)
        ))
        
        self._log_data_collection_audit(cursor, team_id, competition_id, 'advanced_form', metadata)
        
        return {'records_updated': 1, 'table': 'team_form_data'}
    
    def _integrate_goals_data(self, cursor, team_id: str, competition_id: str,
                             data: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate Goals agent data into team_goals_data table"""
        
        cursor.execute("""
            INSERT OR REPLACE INTO team_goals_data (
                id, team_id, competition_id, season,
                goals_per_game, opponent_adjusted_offensive, goals_conceded_per_game, opponent_adjusted_defensive,
                clean_sheet_percentage, over_2_5_percentage, over_1_5_percentage, btts_percentage,
                under_2_5_percentage, home_goals_per_game, away_goals_per_game,
                home_goals_conceded_per_game, away_goals_conceded_per_game, matches_analyzed,
                last_updated, data_confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()), team_id, competition_id, "2024",
            data.get('goals_per_game'),
            data.get('opponent_adjusted_offensive'),
            data.get('goals_conceded_per_game'),
            data.get('opponent_adjusted_defensive'),
            data.get('clean_sheet_percentage'),
            data.get('over_2_5_percentage'),
            data.get('over_1_5_percentage'),
            data.get('btts_percentage'),
            data.get('under_2_5_percentage', 100 - data.get('over_2_5_percentage', 0)),
            data.get('home_goals_per_game', 0.0),
            data.get('away_goals_per_game', 0.0),
            data.get('home_goals_conceded_per_game', 0.0),
            data.get('away_goals_conceded_per_game', 0.0),
            data.get('matches_analyzed', 0),
            datetime.now().isoformat(),
            metadata.get('confidence_level', 1.0)
        ))
        
        self._log_data_collection_audit(cursor, team_id, competition_id, 'goals_data', metadata)
        
        return {'records_updated': 1, 'table': 'team_goals_data'}
    
    def _integrate_squad_data(self, cursor, team_id: str, competition_id: str,
                             data: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate Squad agent data into team_squad_data table"""
        
        cursor.execute("""
            INSERT OR REPLACE INTO team_squad_data (
                id, team_id, competition_id, season,
                total_squad_value, squad_depth_index, starting_xi_avg_value, second_xi_avg_value,
                total_players, goalkeepers, defenders, midfielders, forwards, position_balance_score,
                average_age, international_players, most_valuable_player_value,
                market_value_currency, last_transfermarkt_update,
                last_updated, data_confidence, data_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()), team_id, competition_id, "2024",
            data.get('total_squad_value'),
            data.get('squad_depth_index'),
            data.get('starting_xi_avg_value'),
            data.get('second_xi_avg_value'),
            data.get('total_players', 0),
            data.get('goalkeepers', 0),
            data.get('defenders', 0),
            data.get('midfielders', 0),
            data.get('forwards', 0),
            data.get('position_balance_score', 0.0),
            data.get('average_age', 25.0),
            data.get('international_players', 0),
            data.get('most_valuable_player_value', 0.0),
            'EUR',
            data.get('last_update_timestamp'),
            datetime.now().isoformat(),
            metadata.get('confidence_level', 1.0),
            metadata.get('data_source', 'transfermarkt')
        ))
        
        self._log_data_collection_audit(cursor, team_id, competition_id, 'enhanced_squad_value', metadata)
        
        return {'records_updated': 1, 'table': 'team_squad_data'}
    
    def _integrate_context_data(self, cursor, team_id: str, competition_id: str,
                               data: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate Context agent data into team_context_data table"""
        
        cursor.execute("""
            INSERT OR REPLACE INTO team_context_data (
                id, team_id, competition_id, season,
                overall_home_advantage, home_advantage_points, home_advantage_goals, home_advantage_defensive,
                home_win_rate, away_win_rate, current_position, motivation_factor,
                title_race_motivation, relegation_motivation, european_motivation,
                fixture_density, days_since_last_match, matches_last_30_days,
                home_matches_played, away_matches_played, home_points_per_game, away_points_per_game,
                last_updated, data_confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()), team_id, competition_id, "2024",
            data.get('overall_home_advantage'),
            data.get('home_advantage_points'),
            data.get('home_advantage_goals'),
            data.get('home_advantage_defensive'),
            data.get('home_win_rate', 0.0),
            data.get('away_win_rate', 0.0),
            data.get('current_position'),
            data.get('motivation_factor'),
            data.get('title_race_motivation', 0.0),
            data.get('relegation_motivation', 0.0),
            data.get('european_motivation', 0.0),
            data.get('fixture_density'),
            data.get('days_since_last_match'),
            data.get('matches_last_30_days', 0),
            data.get('home_matches_played', 0),
            data.get('away_matches_played', 0),
            data.get('home_points_per_game', 0.0),
            data.get('away_points_per_game', 0.0),
            datetime.now().isoformat(),
            metadata.get('confidence_level', 1.0)
        ))
        
        self._log_data_collection_audit(cursor, team_id, competition_id, 'context_data', metadata)
        
        return {'records_updated': 1, 'table': 'team_context_data'}
    
    def _log_data_collection_audit(self, cursor, team_id: str, competition_id: str, 
                                  agent_name: str, metadata: Dict[str, Any]):
        """Log data collection audit entry"""
        cursor.execute("""
            INSERT INTO data_collection_audit (
                id, team_id, competition_id, agent_name, collection_timestamp,
                execution_time_seconds, success, data_quality_score, confidence_level, records_collected
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()), team_id, competition_id, agent_name,
            metadata.get('collection_timestamp', datetime.now().isoformat()),
            metadata.get('execution_time', 0.0),
            True,  # If we got here, it was successful
            100.0,  # Data quality calculated elsewhere
            metadata.get('confidence_level', 1.0),
            1  # One record collected per agent
        ))
    
    def update_main_strength_table(self, team_id: str, competition_id: str, 
                                  integration_results: Dict[str, Any]):
        """
        Update the main competition_team_strength table with aggregated data
        from all dedicated parameter tables
        """
        conn = self.get_database_connection()
        c = conn.cursor()
        
        try:
            # Get team name
            c.execute("SELECT team_name FROM competition_team_strength WHERE team_id = ? AND competition_id = ?", 
                     (team_id, competition_id))
            result = c.fetchone()
            if not result:
                print(f"⚠️ Team not found in competition_team_strength table")
                return
            
            team_name = result[0]
            
            # Collect data from dedicated tables
            elo_data = self._get_latest_elo_data(c, team_id, competition_id)
            form_data = self._get_latest_form_data(c, team_id, competition_id)
            goals_data = self._get_latest_goals_data(c, team_id, competition_id)
            squad_data = self._get_latest_squad_data(c, team_id, competition_id)
            context_data = self._get_latest_context_data(c, team_id, competition_id)
            
            # Prepare update values
            update_values = {
                # ELO data
                'standard_elo': elo_data.get('standard_elo'),
                'recent_form_elo': elo_data.get('recent_form_elo'),
                'elo_trend': elo_data.get('elo_trend'),
                
                # Form data
                'raw_form_score': form_data.get('raw_form_score'),
                'opponent_adjusted_form': form_data.get('opponent_adjusted_form'),
                'form_trend': form_data.get('form_trend'),
                'form_consistency': form_data.get('form_consistency'),
                
                # Goals data
                'goals_per_game': goals_data.get('goals_per_game'),
                'opponent_adjusted_offensive': goals_data.get('opponent_adjusted_offensive'),
                'goals_conceded_per_game': goals_data.get('goals_conceded_per_game'),
                'opponent_adjusted_defensive': goals_data.get('opponent_adjusted_defensive'),
                'clean_sheet_percentage': goals_data.get('clean_sheet_percentage'),
                'over_2_5_percentage': goals_data.get('over_2_5_percentage'),
                'over_1_5_percentage': goals_data.get('over_1_5_percentage'),
                'btts_percentage': goals_data.get('btts_percentage'),
                
                # Squad data
                'total_squad_value': squad_data.get('total_squad_value'),
                'squad_depth_index': squad_data.get('squad_depth_index'),
                'starting_xi_avg_value': squad_data.get('starting_xi_avg_value'),
                'second_xi_avg_value': squad_data.get('second_xi_avg_value'),
                'position_balance_score': squad_data.get('position_balance_score'),
                
                # Context data
                'overall_home_advantage': context_data.get('overall_home_advantage'),
                'home_advantage_points': context_data.get('home_advantage_points'),
                'home_advantage_goals': context_data.get('home_advantage_goals'),
                'home_advantage_defensive': context_data.get('home_advantage_defensive'),
                'motivation_factor': context_data.get('motivation_factor'),
                'current_position': context_data.get('current_position'),
                'title_race_motivation': context_data.get('title_race_motivation'),
                'relegation_motivation': context_data.get('relegation_motivation'),
                'european_motivation': context_data.get('european_motivation'),
                'fixture_density': context_data.get('fixture_density'),
                'days_since_last_match': context_data.get('days_since_last_match'),
                
                # Metadata
                'last_updated': datetime.now().isoformat(),
                'validation_status': 'passed' if integration_results['overall_success'] else 'failed'
            }
            
            # Build dynamic UPDATE query
            set_clause = ", ".join([f"{key} = ?" for key in update_values.keys()])
            values = list(update_values.values()) + [team_id, competition_id]
            
            c.execute(f"""
                UPDATE competition_team_strength 
                SET {set_clause}
                WHERE team_id = ? AND competition_id = ?
            """, values)
            
            print(f"✅ Updated main strength table for {team_name}")
            
        finally:
            conn.commit()
            conn.close()
    
    def _get_latest_elo_data(self, cursor, team_id: str, competition_id: str) -> Dict[str, Any]:
        """Get latest ELO data for team"""
        cursor.execute("""
            SELECT standard_elo, recent_form_elo, elo_trend
            FROM team_elo_data 
            WHERE team_id = ? AND competition_id = ?
            ORDER BY last_updated DESC LIMIT 1
        """, (team_id, competition_id))
        
        result = cursor.fetchone()
        if result:
            return {
                'standard_elo': result[0],
                'recent_form_elo': result[1],
                'elo_trend': result[2]
            }
        return {}
    
    def _get_latest_form_data(self, cursor, team_id: str, competition_id: str) -> Dict[str, Any]:
        """Get latest form data for team"""
        cursor.execute("""
            SELECT raw_form_score, opponent_adjusted_form, form_trend, form_consistency
            FROM team_form_data 
            WHERE team_id = ? AND competition_id = ?
            ORDER BY last_updated DESC LIMIT 1
        """, (team_id, competition_id))
        
        result = cursor.fetchone()
        if result:
            return {
                'raw_form_score': result[0],
                'opponent_adjusted_form': result[1],
                'form_trend': result[2],
                'form_consistency': result[3]
            }
        return {}
    
    def _get_latest_goals_data(self, cursor, team_id: str, competition_id: str) -> Dict[str, Any]:
        """Get latest goals data for team"""
        cursor.execute("""
            SELECT goals_per_game, opponent_adjusted_offensive, goals_conceded_per_game, 
                   opponent_adjusted_defensive, clean_sheet_percentage, over_2_5_percentage,
                   over_1_5_percentage, btts_percentage
            FROM team_goals_data 
            WHERE team_id = ? AND competition_id = ?
            ORDER BY last_updated DESC LIMIT 1
        """, (team_id, competition_id))
        
        result = cursor.fetchone()
        if result:
            return {
                'goals_per_game': result[0],
                'opponent_adjusted_offensive': result[1],
                'goals_conceded_per_game': result[2],
                'opponent_adjusted_defensive': result[3],
                'clean_sheet_percentage': result[4],
                'over_2_5_percentage': result[5],
                'over_1_5_percentage': result[6],
                'btts_percentage': result[7]
            }
        return {}
    
    def _get_latest_squad_data(self, cursor, team_id: str, competition_id: str) -> Dict[str, Any]:
        """Get latest squad data for team"""
        cursor.execute("""
            SELECT total_squad_value, squad_depth_index, starting_xi_avg_value, 
                   second_xi_avg_value, position_balance_score
            FROM team_squad_data 
            WHERE team_id = ? AND competition_id = ?
            ORDER BY last_updated DESC LIMIT 1
        """, (team_id, competition_id))
        
        result = cursor.fetchone()
        if result:
            return {
                'total_squad_value': result[0],
                'squad_depth_index': result[1],
                'starting_xi_avg_value': result[2],
                'second_xi_avg_value': result[3],
                'position_balance_score': result[4]
            }
        return {}
    
    def _get_latest_context_data(self, cursor, team_id: str, competition_id: str) -> Dict[str, Any]:
        """Get latest context data for team"""
        cursor.execute("""
            SELECT overall_home_advantage, home_advantage_points, home_advantage_goals,
                   home_advantage_defensive, motivation_factor, current_position,
                   title_race_motivation, relegation_motivation, european_motivation,
                   fixture_density, days_since_last_match
            FROM team_context_data 
            WHERE team_id = ? AND competition_id = ?
            ORDER BY last_updated DESC LIMIT 1
        """, (team_id, competition_id))
        
        result = cursor.fetchone()
        if result:
            return {
                'overall_home_advantage': result[0],
                'home_advantage_points': result[1],
                'home_advantage_goals': result[2],
                'home_advantage_defensive': result[3],
                'motivation_factor': result[4],
                'current_position': result[5],
                'title_race_motivation': result[6],
                'relegation_motivation': result[7],
                'european_motivation': result[8],
                'fixture_density': result[9],
                'days_since_last_match': result[10]
            }
        return {}
    
    def bulk_integrate_teams(self, team_list: List[str], competition_name: str = None) -> Dict[str, Any]:
        """
        Bulk integrate data for multiple teams
        
        Args:
            team_list: List of team names to process
            competition_name: Competition context
            
        Returns:
            Bulk integration results
        """
        print(f"🔄 BULK INTEGRATION: {len(team_list)} teams")
        print("="*60)
        
        bulk_results = {
            'total_teams': len(team_list),
            'successful_teams': 0,
            'failed_teams': 0,
            'team_results': {},
            'start_time': datetime.now().isoformat()
        }
        
        for i, team_name in enumerate(team_list, 1):
            print(f"\n[{i}/{len(team_list)}] Processing {team_name}...")
            
            try:
                result = self.collect_and_integrate_team_data(team_name, competition_name)
                bulk_results['team_results'][team_name] = result
                
                if result.get('overall_success'):
                    bulk_results['successful_teams'] += 1
                    print(f"  ✅ {team_name}: SUCCESS")
                else:
                    bulk_results['failed_teams'] += 1
                    print(f"  ❌ {team_name}: FAILED")
                    
            except Exception as e:
                bulk_results['team_results'][team_name] = {'error': str(e)}
                bulk_results['failed_teams'] += 1
                print(f"  ❌ {team_name}: ERROR - {e}")
        
        bulk_results['end_time'] = datetime.now().isoformat()
        bulk_results['success_rate'] = (bulk_results['successful_teams'] / bulk_results['total_teams']) * 100
        
        print(f"\n📊 BULK INTEGRATION SUMMARY:")
        print(f"   ✅ Successful: {bulk_results['successful_teams']}/{bulk_results['total_teams']}")
        print(f"   ❌ Failed: {bulk_results['failed_teams']}/{bulk_results['total_teams']}")
        print(f"   📈 Success Rate: {bulk_results['success_rate']:.1f}%")
        
        return bulk_results


def main():
    """Test the Data Integration Layer"""
    integration_layer = DataIntegrationLayer()
    
    # Test with a single team
    test_teams = ["Manchester City", "Real Madrid"]
    
    print("🧪 TESTING DATA INTEGRATION LAYER")
    print("="*60)
    
    for team in test_teams:
        print(f"\n🔍 Testing integration for {team}...")
        try:
            result = integration_layer.collect_and_integrate_team_data(team)
            if result.get('overall_success'):
                print(f"✅ {team}: Integration successful")
                print(f"   Agents processed: {len(result['agent_results'])}")
                print(f"   Database updates: {len(result['database_updates'])}")
            else:
                print(f"❌ {team}: Integration failed")
                for agent, agent_result in result['agent_results'].items():
                    if not agent_result.get('success'):
                        print(f"      {agent}: {agent_result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"❌ {team}: ERROR - {e}")

if __name__ == "__main__":
    main()