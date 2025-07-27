#!/usr/bin/env python3
"""
Simple test runner for Spooky Football Engine

This script provides a simple way to run tests without requiring
external dependencies beyond Python standard library.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_imports():
    """Check if core modules can be imported"""
    print("🔍 Checking core module imports...")
    
    modules_to_test = [
        'database_config',
        'environment_config', 
        'optimized_queries'
    ]
    
    import_results = {}
    
    for module in modules_to_test:
        try:
            __import__(module)
            import_results[module] = True
            print(f"  ✅ {module}")
        except Exception as e:
            import_results[module] = False
            print(f"  ❌ {module}: {e}")
    
    return import_results

def test_database_connection():
    """Test basic database connectivity"""
    print("\n🗄️ Testing database connection...")
    
    try:
        from database_config import db_config
        conn = db_config.get_connection()
        if conn:
            print("  ✅ Database connection successful")
            conn.close()
            return True
        else:
            print("  ❌ Database connection failed")
            return False
    except Exception as e:
        print(f"  ❌ Database connection error: {e}")
        return False

def test_optimized_queries():
    """Test optimized queries functionality"""
    print("\n⚡ Testing optimized queries...")
    
    try:
        from optimized_queries import optimized_queries
        
        # Test team loading
        teams_by_league, all_teams = optimized_queries.get_all_teams_optimized()
        
        if teams_by_league and all_teams:
            print(f"  ✅ Loaded {len(all_teams)} teams across {len(teams_by_league)} leagues")
            return True
        else:
            print("  ❌ No teams loaded")
            return False
    except Exception as e:
        print(f"  ❌ Optimized queries error: {e}")
        return False

def test_flask_app():
    """Test Flask app can be imported and initialized"""
    print("\n🌐 Testing Flask application...")
    
    try:
        import demo_app
        app = demo_app.app
        
        if app:
            print("  ✅ Flask app imported successfully")
            
            # Test if app can create test client
            with app.test_client() as client:
                print("  ✅ Flask test client created")
                return True
        else:
            print("  ❌ Flask app initialization failed")
            return False
    except Exception as e:
        print(f"  ❌ Flask app error: {e}")
        return False

def run_basic_tests():
    """Run basic functionality tests"""
    print("🧪 Spooky Football Engine - Basic Test Suite")
    print("=" * 50)
    
    tests = [
        ("Import Tests", check_imports),
        ("Database Connection", test_database_connection),
        ("Optimized Queries", test_optimized_queries),
        ("Flask Application", test_flask_app)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"  🚨 {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 BASIC TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    success_rate = (passed / total * 100) if total > 0 else 0
    print(f"\nSuccess Rate: {success_rate:.1f}% ({passed}/{total})")
    
    if success_rate == 100:
        print("🎉 All basic tests passed! System is ready.")
    elif success_rate >= 75:
        print("✅ Most tests passed. System is functional.")
    else:
        print("⚠️ Several tests failed. Check the issues above.")
    
    return results

if __name__ == '__main__':
    run_basic_tests()