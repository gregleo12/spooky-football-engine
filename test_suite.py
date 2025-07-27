#!/usr/bin/env python3
"""
Comprehensive Testing Suite for Spooky Football Engine

This test suite validates all core functionality including:
- Database operations
- Web application endpoints
- Data integrity
- Performance benchmarks
- Error handling
"""

import unittest
import json
import time
import os
import sys
from unittest.mock import patch, MagicMock

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import core modules
from database_config import db_config
from environment_config import env_config
from optimized_queries import optimized_queries

class TestDatabaseOperations(unittest.TestCase):
    """Test database connectivity and operations"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_team = "Liverpool"
        self.test_league = "Premier League"
    
    def test_database_connection(self):
        """Test database connectivity"""
        try:
            conn = db_config.get_connection()
            self.assertIsNotNone(conn, "Database connection should not be None")
            conn.close()
        except Exception as e:
            self.fail(f"Database connection failed: {e}")
    
    def test_database_tables_exist(self):
        """Test that required tables exist"""
        required_tables = ['teams', 'competitions', 'competition_team_strength']
        
        for table in required_tables:
            with self.subTest(table=table):
                if db_config.use_postgresql:
                    query = "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = %s"
                else:
                    query = "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name = ?"
                
                result = db_config.execute_query(query, (table,))
                self.assertGreater(result[0][0], 0, f"Table {table} should exist")
    
    def test_optimized_queries_performance(self):
        """Test optimized queries performance"""
        start_time = time.time()
        teams_by_league, all_teams = optimized_queries.get_all_teams_optimized()
        query_time = time.time() - start_time
        
        self.assertLess(query_time, 2.0, "Query should complete within 2 seconds")
        self.assertIsInstance(teams_by_league, dict, "Should return dictionary")
        self.assertIsInstance(all_teams, list, "Should return list")
        self.assertGreater(len(all_teams), 0, "Should return teams")
    
    def test_team_data_retrieval(self):
        """Test individual team data retrieval"""
        team_data = optimized_queries.get_team_data_optimized(self.test_team)
        
        if team_data:  # If team exists in database
            self.assertIsInstance(team_data, dict, "Should return dictionary")
            self.assertIn('name', team_data, "Should include team name")
            self.assertIn('league', team_data, "Should include league")
        else:
            # Test with a team that should exist
            teams_by_league, _ = optimized_queries.get_all_teams_optimized()
            if teams_by_league and any(teams_by_league.values()):
                # Get first available team
                first_league = next(iter(teams_by_league.keys()))
                if teams_by_league[first_league]:
                    test_team = teams_by_league[first_league][0]['name']
                    team_data = optimized_queries.get_team_data_optimized(test_team)
                    self.assertIsNotNone(team_data, f"Should find data for {test_team}")

class TestWebApplication(unittest.TestCase):
    """Test Flask web application endpoints"""
    
    @classmethod
    def setUpClass(cls):
        """Set up Flask test client"""
        try:
            import demo_app
            cls.app = demo_app.app
            cls.client = cls.app.test_client()
            cls.app.config['TESTING'] = True
        except ImportError as e:
            cls.skipTest(cls, f"Flask app import failed: {e}")
    
    def test_main_page_loads(self):
        """Test main page loads without errors"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200, "Main page should load successfully")
        self.assertIn(b'Match Predictor', response.data, "Should contain app title")
    
    def test_api_teams_endpoint(self):
        """Test teams API endpoint"""
        response = self.client.get('/api/teams')
        self.assertEqual(response.status_code, 200, "Teams API should respond")
        
        data = json.loads(response.data)
        self.assertIn('teams_by_league', data, "Should include teams by league")
        self.assertIn('all_teams', data, "Should include all teams")
    
    def test_analyze_endpoint(self):
        """Test match analysis endpoint"""
        # First get available teams
        teams_response = self.client.get('/api/teams')
        teams_data = json.loads(teams_response.data)
        
        if teams_data['all_teams'] and len(teams_data['all_teams']) >= 2:
            team1 = teams_data['all_teams'][0]['name']
            team2 = teams_data['all_teams'][1]['name']
            
            response = self.client.post('/analyze',
                data=json.dumps({'home_team': team1, 'away_team': team2}),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200, "Analysis should succeed")
            data = json.loads(response.data)
            
            if 'error' not in data:
                self.assertIn('favorite', data, "Should include prediction")
                self.assertIn('favorite_probability', data, "Should include probability")
    
    def test_teams_ranking_page(self):
        """Test teams ranking page"""
        response = self.client.get('/teams-ranking')
        self.assertEqual(response.status_code, 200, "Teams ranking page should load")
    
    def test_admin_dashboard(self):
        """Test admin dashboard"""
        response = self.client.get('/admin')
        self.assertEqual(response.status_code, 200, "Admin dashboard should load")
        self.assertIn(b'Admin Dashboard', response.data, "Should contain admin title")
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200, "Health check should respond")

class TestDataIntegrity(unittest.TestCase):
    """Test data integrity and consistency"""
    
    def test_team_count_consistency(self):
        """Test that team counts are consistent across queries"""
        teams_by_league, all_teams = optimized_queries.get_all_teams_optimized()
        
        # Count teams in leagues
        league_count = sum(len(teams) for teams in teams_by_league.values())
        self.assertEqual(league_count, len(all_teams), 
                        "Team count should be consistent between league grouping and all teams")
    
    def test_required_leagues_present(self):
        """Test that all required leagues are present"""
        teams_by_league, _ = optimized_queries.get_all_teams_optimized()
        required_leagues = ['Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1']
        
        for league in required_leagues:
            with self.subTest(league=league):
                self.assertIn(league, teams_by_league, f"{league} should be present")
    
    def test_team_data_completeness(self):
        """Test that teams have required data fields"""
        _, all_teams = optimized_queries.get_all_teams_optimized()
        
        if all_teams:
            sample_team = all_teams[0]
            required_fields = ['name', 'league', 'local_strength', 'european_strength']
            
            for field in required_fields:
                with self.subTest(field=field):
                    self.assertIn(field, sample_team, f"Team should have {field} field")
    
    def test_strength_values_valid(self):
        """Test that strength values are within valid ranges"""
        _, all_teams = optimized_queries.get_all_teams_optimized()
        
        for team in all_teams[:10]:  # Test first 10 teams
            with self.subTest(team=team['name']):
                if team['local_strength'] is not None:
                    self.assertGreaterEqual(team['local_strength'], 0, 
                                          "Local strength should be non-negative")
                    self.assertLessEqual(team['local_strength'], 1, 
                                       "Local strength should not exceed 1")

class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases"""
    
    def test_invalid_team_analysis(self):
        """Test analysis with invalid team names"""
        try:
            import demo_app
            client = demo_app.app.test_client()
            
            response = client.post('/analyze',
                data=json.dumps({'home_team': 'InvalidTeam1', 'away_team': 'InvalidTeam2'}),
                content_type='application/json'
            )
            
            data = json.loads(response.data)
            self.assertIn('error', data, "Should return error for invalid teams")
        except ImportError:
            self.skipTest("Flask app not available")
    
    def test_missing_parameters(self):
        """Test API with missing parameters"""
        try:
            import demo_app
            client = demo_app.app.test_client()
            
            response = client.post('/analyze',
                data=json.dumps({'home_team': 'Liverpool'}),  # Missing away_team
                content_type='application/json'
            )
            
            data = json.loads(response.data)
            self.assertIn('error', data, "Should return error for missing parameters")
        except ImportError:
            self.skipTest("Flask app not available")
    
    def test_database_error_handling(self):
        """Test handling of database errors"""
        with patch.object(db_config, 'execute_query', side_effect=Exception("Database error")):
            teams_data = optimized_queries.get_team_data_optimized("TestTeam")
            self.assertIsNone(teams_data, "Should handle database errors gracefully")

class TestPerformance(unittest.TestCase):
    """Test performance benchmarks"""
    
    def test_query_performance(self):
        """Test that queries complete within reasonable time"""
        # Test all teams query
        start_time = time.time()
        optimized_queries.get_all_teams_optimized()
        teams_query_time = time.time() - start_time
        
        self.assertLess(teams_query_time, 3.0, "All teams query should complete within 3 seconds")
        
        # Test stats query
        start_time = time.time()
        optimized_queries.get_database_stats()
        stats_query_time = time.time() - start_time
        
        self.assertLess(stats_query_time, 2.0, "Stats query should complete within 2 seconds")
    
    def test_cache_effectiveness(self):
        """Test that caching improves performance"""
        # Clear cache first
        optimized_queries._clear_cache()
        
        # First query (uncached)
        start_time = time.time()
        optimized_queries.get_all_teams_optimized()
        first_query_time = time.time() - start_time
        
        # Second query (cached)
        start_time = time.time()
        optimized_queries.get_all_teams_optimized()
        second_query_time = time.time() - start_time
        
        self.assertLess(second_query_time, first_query_time, 
                       "Cached query should be faster than uncached")

class TestEnvironmentConfiguration(unittest.TestCase):
    """Test environment configuration and detection"""
    
    def test_environment_detection(self):
        """Test environment detection logic"""
        self.assertIsNotNone(env_config.environment, "Environment should be detected")
        self.assertIn(env_config.database_type, ['SQLite', 'PostgreSQL'], 
                     "Database type should be valid")
    
    def test_database_config(self):
        """Test database configuration"""
        db_type = db_config.get_db_type()
        self.assertIn(db_type, ['SQLite', 'PostgreSQL'], "Database type should be valid")

def run_tests():
    """Run all tests and generate report"""
    print("🧪 Spooky Football Engine - Comprehensive Test Suite")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestDatabaseOperations,
        TestWebApplication, 
        TestDataIntegrity,
        TestErrorHandling,
        TestPerformance,
        TestEnvironmentConfiguration
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Generate summary report
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY REPORT")
    print("=" * 60)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\n🚨 ERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split('Exception:')[-1].strip()}")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
    print(f"\n✅ Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("🎉 System is functioning excellently!")
    elif success_rate >= 75:
        print("✅ System is functioning well with minor issues.")
    elif success_rate >= 50:
        print("⚠️ System has significant issues that need attention.")
    else:
        print("🚨 System has critical issues that require immediate attention.")
    
    return result

if __name__ == '__main__':
    run_tests()