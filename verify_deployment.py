#!/usr/bin/env python3
"""
Deployment Verification Script for Spooky Football Engine

This script verifies that the system is ready for deployment to Railway
by checking all production requirements.
"""

import sys
import os
import json

def check_required_files():
    """Check that all required files exist"""
    print("📁 Checking required files...")
    
    required_files = [
        'demo_app.py',
        'requirements.txt', 
        'Procfile',
        'database_config.py',
        'environment_config.py',
        'optimized_queries.py',
        'templates/index.html',
        'agents/shared/team_api_ids.json'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path}")
            missing_files.append(file_path)
    
    return len(missing_files) == 0

def check_requirements_txt():
    """Check requirements.txt contains necessary packages"""
    print("\n📦 Checking requirements.txt...")
    
    try:
        with open('requirements.txt', 'r') as f:
            requirements = f.read().lower()
        
        required_packages = ['flask', 'psycopg2', 'requests', 'beautifulsoup4']
        missing_packages = []
        
        for package in required_packages:
            if package in requirements:
                print(f"  ✅ {package}")
            else:
                print(f"  ❌ {package}")
                missing_packages.append(package)
        
        return len(missing_packages) == 0
    except FileNotFoundError:
        print("  ❌ requirements.txt not found")
        return False

def check_procfile():
    """Check Procfile is correct"""
    print("\n🚀 Checking Procfile...")
    
    try:
        with open('Procfile', 'r') as f:
            procfile_content = f.read().strip()
        
        if 'web:' in procfile_content and 'demo_app:app' in procfile_content:
            print(f"  ✅ Procfile: {procfile_content}")
            return True
        else:
            print(f"  ❌ Procfile content: {procfile_content}")
            return False
    except FileNotFoundError:
        print("  ❌ Procfile not found")
        return False

def check_environment_config():
    """Check environment configuration works"""
    print("\n🔧 Checking environment configuration...")
    
    try:
        from environment_config import env_config
        
        print(f"  ✅ Environment: {env_config.environment.value}")
        print(f"  ✅ Database type: {env_config.database_type}")
        
        return True
    except Exception as e:
        print(f"  ❌ Environment config error: {e}")
        return False

def check_database_structure():
    """Check database structure and data"""
    print("\n🗄️ Checking database structure...")
    
    try:
        from optimized_queries import optimized_queries
        
        # Test database stats
        stats = optimized_queries.get_database_stats()
        
        if stats:
            print(f"  ✅ Teams: {stats.get('total_teams', 'N/A')}")
            print(f"  ✅ Competitions: {stats.get('total_competitions', 'N/A')}")
            print(f"  ✅ Data coverage: {stats.get('data_coverage_percent', 'N/A')}%")
            
            # Check minimum data requirements
            if stats.get('total_teams', 0) >= 90:  # Expect ~96 teams
                return True
            else:
                print(f"  ❌ Insufficient teams: {stats.get('total_teams', 0)}")
                return False
        else:
            print("  ❌ Unable to retrieve database stats")
            return False
    except Exception as e:
        print(f"  ❌ Database check error: {e}")
        return False

def check_team_api_ids():
    """Check team API IDs file"""
    print("\n🆔 Checking team API IDs...")
    
    try:
        with open('agents/shared/team_api_ids.json', 'r') as f:
            api_ids = json.load(f)
        
        if len(api_ids) >= 50:  # Should have many team mappings
            print(f"  ✅ API IDs loaded: {len(api_ids)} teams")
            return True
        else:
            print(f"  ❌ Insufficient API IDs: {len(api_ids)}")
            return False
    except Exception as e:
        print(f"  ❌ API IDs error: {e}")
        return False

def check_syntax():
    """Check Python syntax of main files"""
    print("\n🐍 Checking Python syntax...")
    
    main_files = ['demo_app.py', 'database_config.py', 'environment_config.py', 'optimized_queries.py']
    
    import py_compile
    
    for file_path in main_files:
        try:
            py_compile.compile(file_path, doraise=True)
            print(f"  ✅ {file_path}")
        except py_compile.PyCompileError as e:
            print(f"  ❌ {file_path}: {e}")
            return False
    
    return True

def generate_deployment_checklist():
    """Generate deployment checklist"""
    print("\n📋 DEPLOYMENT CHECKLIST")
    print("=" * 50)
    
    checklist = [
        "✅ Create GitHub repository: spooky-football-engine",
        "✅ Push all code to GitHub",
        "✅ Create Railway account and link GitHub",
        "✅ Deploy from GitHub repository",
        "✅ Add PostgreSQL service in Railway",
        "✅ Wait for initial deployment",
        "✅ Check Railway logs for any errors",
        "✅ Test the deployed application URL",
        "✅ Verify database connection works",
        "✅ Test analyze function with sample teams"
    ]
    
    for item in checklist:
        print(item)

def main():
    """Run all deployment verification checks"""
    print("🔍 Spooky Football Engine - Deployment Verification")
    print("=" * 60)
    
    checks = [
        ("Required Files", check_required_files),
        ("Requirements.txt", check_requirements_txt),
        ("Procfile", check_procfile),
        ("Environment Config", check_environment_config),
        ("Database Structure", check_database_structure),
        ("Team API IDs", check_team_api_ids),
        ("Python Syntax", check_syntax)
    ]
    
    results = {}
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            results[check_name] = result
        except Exception as e:
            print(f"  🚨 {check_name} crashed: {e}")
            results[check_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 DEPLOYMENT READINESS SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for check_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name}: {status}")
    
    success_rate = (passed / total * 100) if total > 0 else 0
    print(f"\nReadiness Score: {success_rate:.1f}% ({passed}/{total})")
    
    if success_rate == 100:
        print("🚀 System is READY for deployment!")
        generate_deployment_checklist()
    elif success_rate >= 80:
        print("✅ System is mostly ready. Address the failed checks above.")
    else:
        print("⚠️ System is NOT ready for deployment. Fix the issues above.")
    
    return results

if __name__ == '__main__':
    main()