#!/usr/bin/env python3
"""
API Stress Test
Tests API endpoints under load to ensure stability
"""
import requests
import time
import concurrent.futures
import statistics
import sys

# Configuration
BASE_URL = "https://web-production-18fb.up.railway.app"
CONCURRENT_REQUESTS = 5
TOTAL_REQUESTS = 20

def time_request(endpoint, method="GET", data=None):
    """Time a single request"""
    start = time.time()
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=30)
        else:
            response = requests.post(f"{BASE_URL}{endpoint}", json=data, timeout=30)
        
        duration = time.time() - start
        return {
            'success': response.status_code == 200,
            'duration': duration,
            'status': response.status_code
        }
    except Exception as e:
        return {
            'success': False,
            'duration': time.time() - start,
            'error': str(e)
        }

def stress_test_endpoint(name, endpoint, method="GET", data=None):
    """Stress test a single endpoint"""
    print(f"\n🔥 Stress testing {name}...")
    print(f"   Endpoint: {endpoint}")
    print(f"   Requests: {TOTAL_REQUESTS} total, {CONCURRENT_REQUESTS} concurrent")
    
    results = []
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_REQUESTS) as executor:
        futures = []
        for i in range(TOTAL_REQUESTS):
            future = executor.submit(time_request, endpoint, method, data)
            futures.append(future)
        
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    
    total_time = time.time() - start_time
    
    # Analyze results
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    durations = [r['duration'] for r in successful]
    
    print(f"\n   Results:")
    print(f"   ✅ Successful: {len(successful)}/{TOTAL_REQUESTS}")
    print(f"   ❌ Failed: {len(failed)}/{TOTAL_REQUESTS}")
    
    if durations:
        print(f"   ⏱️  Response times:")
        print(f"      - Average: {statistics.mean(durations):.2f}s")
        print(f"      - Median: {statistics.median(durations):.2f}s")
        print(f"      - Min: {min(durations):.2f}s")
        print(f"      - Max: {max(durations):.2f}s")
    
    print(f"   🏁 Total test time: {total_time:.2f}s")
    
    if failed:
        print(f"\n   Failed requests:")
        for i, fail in enumerate(failed[:5]):  # Show first 5 failures
            if 'error' in fail:
                print(f"      - {fail['error']}")
            else:
                print(f"      - Status {fail.get('status', 'Unknown')}")
    
    return len(successful) == TOTAL_REQUESTS

def main():
    print("=" * 60)
    print("🚀 API STRESS TEST")
    print(f"   Target: {BASE_URL}")
    print(f"   Load: {CONCURRENT_REQUESTS} concurrent requests")
    print("=" * 60)
    
    tests = [
        ("Homepage", "/"),
        ("Teams API", "/api/teams"),
        ("Analyze Match", "/analyze", "POST", {
            "home_team": "Manchester City",
            "away_team": "Liverpool"
        }),
        ("Team Form", "/api/team-form/Chelsea"),
        ("Last Update", "/api/last-update")
    ]
    
    passed = 0
    for test in tests:
        if stress_test_endpoint(*test):
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 FINAL RESULTS: {passed}/{len(tests)} endpoints passed stress test")
    print("=" * 60)
    
    if passed == len(tests):
        print("🎉 All endpoints handled load successfully!")
        return 0
    else:
        print("⚠️  Some endpoints failed under load. Consider optimization.")
        return 1

if __name__ == "__main__":
    sys.exit(main())