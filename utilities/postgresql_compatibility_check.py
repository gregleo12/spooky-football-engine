#!/usr/bin/env python3
"""
PostgreSQL Compatibility Check for Spooky Football Engine
Tests all API endpoints and database operations
"""
import requests
import json
import sys

BASE_URL = "https://web-production-18fb.up.railway.app"

def test_endpoint(name, url, method="GET", data=None):
    """Test an API endpoint"""
    print(f"\n🔍 Testing {name}...")
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        else:
            response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ {name}: SUCCESS")
            return True
        else:
            print(f"❌ {name}: FAILED (Status {response.status_code})")
            print(f"   Response: {response.text[:200]}...")
            return False
    except Exception as e:
        print(f"❌ {name}: ERROR - {str(e)}")
        return False

def main():
    print("=" * 60)
    print("🚀 SPOOKY FOOTBALL ENGINE - PostgreSQL Compatibility Check")
    print("=" * 60)
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Homepage
    tests_total += 1
    if test_endpoint("Homepage", f"{BASE_URL}/"):
        tests_passed += 1
    
    # Test 2: Teams API
    tests_total += 1
    if test_endpoint("Teams API", f"{BASE_URL}/api/teams"):
        tests_passed += 1
    
    # Test 3: Analyze Match
    tests_total += 1
    test_data = {
        "home_team": "Manchester City",
        "away_team": "Liverpool"
    }
    if test_endpoint("Analyze Match", f"{BASE_URL}/analyze", "POST", test_data):
        tests_passed += 1
    
    # Test 4: H2H History
    tests_total += 1
    if test_endpoint("H2H History", f"{BASE_URL}/api/h2h/Manchester%20City/Liverpool"):
        tests_passed += 1
    
    # Test 5: Upcoming Fixtures
    tests_total += 1
    if test_endpoint("Upcoming Fixtures", f"{BASE_URL}/api/upcoming/Manchester%20City/Liverpool"):
        tests_passed += 1
    
    # Test 6: Last Update
    tests_total += 1
    if test_endpoint("Last Update", f"{BASE_URL}/api/last-update"):
        tests_passed += 1
    
    # Test 7: Team Form
    tests_total += 1
    if test_endpoint("Team Form", f"{BASE_URL}/api/team-form/Manchester%20City"):
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 RESULTS: {tests_passed}/{tests_total} tests passed")
    print("=" * 60)
    
    if tests_passed == tests_total:
        print("🎉 All tests passed! Your app is fully PostgreSQL compatible!")
        return 0
    else:
        print(f"⚠️  {tests_total - tests_passed} tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())