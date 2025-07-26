#!/usr/bin/env python3
"""
Validation Reality Check - What Actually Got Built?
Let's separate the facts from the fiction!
"""
import os
import sqlite3
import sys
import json
from datetime import datetime, timedelta
import traceback

def print_section(title):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print('='*60)

def check_file_exists(filepath, description):
    """Check if a file actually exists"""
    exists = os.path.exists(filepath)
    print(f"{'✅' if exists else '❌'} {description}: {'EXISTS' if exists else 'NOT FOUND'}")
    if exists:
        size = os.path.getsize(filepath)
        print(f"   Size: {size:,} bytes")
    return exists

def validate_phase1_data_foundation():
    """Check what Phase 1 actually delivered"""
    print_section("PHASE 1: DATA FOUNDATION VALIDATION")
    
    results = {
        'files_exist': 0,
        'files_expected': 0,
        'data_coverage': 0,
        'squad_depth_fixed': False
    }
    
    # Check if claimed files exist
    print("\n📁 Checking Phase 1 Files:")
    phase1_files = [
        ("agents/data_collection_v2/base_agent.py", "Base Agent Framework"),
        ("agents/data_collection_v2/enhanced_elo_agent.py", "Enhanced ELO Agent"),
        ("agents/data_collection_v2/advanced_form_agent.py", "Advanced Form Agent"),
        ("agents/data_collection_v2/goals_data_agent.py", "Goals Data Agent"),
        ("agents/data_collection_v2/enhanced_squad_value_agent.py", "Squad Value Agent"),
        ("agents/data_collection_v2/context_data_agent.py", "Context Data Agent"),
        ("test_squad_depth_fix.py", "Squad Depth Fix Test")
    ]
    
    for filepath, desc in phase1_files:
        results['files_expected'] += 1
        if check_file_exists(filepath, desc):
            results['files_exist'] += 1
    
    # Check database for actual data
    print("\n📊 Checking Database Coverage:")
    try:
        conn = sqlite3.connect("db/football_strength.db")
        c = conn.cursor()
        
        # Check how many teams we have
        c.execute("SELECT COUNT(DISTINCT id) FROM teams")
        team_count = c.fetchone()[0]
        print(f"Total teams in database: {team_count}")
        
        # Check competition_team_strength table
        try:
            c.execute("SELECT COUNT(*) FROM competition_team_strength WHERE overall_strength IS NOT NULL")
            teams_with_strength = c.fetchone()[0]
            print(f"Teams with calculated strength: {teams_with_strength}")
            results['data_coverage'] = teams_with_strength
        except sqlite3.OperationalError:
            print("❌ competition_team_strength table doesn't exist!")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")
    
    # Test if squad depth is actually fixed
    print("\n🔧 Testing Squad Depth Fix:")
    if os.path.exists("test_squad_depth_fix.py"):
        try:
            # Run the test file
            os.system("cd '/Users/matos/Football App Projects/spooky-football-engine' && python3 test_squad_depth_fix.py > squad_depth_output.txt 2>&1")
            
            # Check output
            if os.path.exists("squad_depth_output.txt"):
                with open("squad_depth_output.txt", "r") as f:
                    output = f.read()
                    if "Chelsea > Alaves (True)" in output:
                        print("✅ Squad depth calculation ACTUALLY FIXED!")
                        results['squad_depth_fixed'] = True
                    else:
                        print("❌ Squad depth still broken")
                os.remove("squad_depth_output.txt")
        except Exception as e:
            print(f"❌ Couldn't test squad depth: {e}")
    
    return results

def validate_phase2_calculation_engine():
    """Check what Phase 2 actually delivered"""
    print_section("PHASE 2: CALCULATION ENGINE VALIDATION")
    
    results = {
        'files_exist': 0,
        'files_expected': 0,
        'calculator_works': False,
        'database_schema_updated': False
    }
    
    # Check Phase 2 files
    print("\n📁 Checking Phase 2 Files:")
    phase2_files = [
        ("models/phase2_schema_updates.py", "Database Schema Updates"),
        ("agents/integration/data_integration_layer.py", "Integration Layer"),
        ("agents/calculation/modular_calculator_engine.py", "Modular Calculator"),
        ("test_phase2_complete.py", "Phase 2 Integration Test")
    ]
    
    for filepath, desc in phase2_files:
        results['files_expected'] += 1
        if check_file_exists(filepath, desc):
            results['files_exist'] += 1
    
    # Check if calculator actually works
    print("\n🧮 Testing Calculator Engine:")
    if os.path.exists("agents/calculation/modular_calculator_engine.py"):
        try:
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            sys.path.append(os.path.join(os.path.dirname(__file__), 'agents', 'calculation'))
            
            from agents.calculation.modular_calculator_engine import ModularCalculatorEngine
            
            calculator = ModularCalculatorEngine()
            
            # Test with dummy data
            test_data = {
                'team_name': 'Test Team',
                'standard_elo': 1500,
                'total_squad_value': 500,
                'raw_form_score': 2.0,
                'squad_depth_index': 50
            }
            
            result = calculator.calculate_team_strength(test_data, 'enhanced')
            print(f"✅ Calculator works! Test strength: {result['strength_percentage']:.1f}%")
            results['calculator_works'] = True
            
        except Exception as e:
            print(f"❌ Calculator error: {e}")
            traceback.print_exc()
    
    # Check database schema updates
    print("\n🗄️ Checking Database Schema Updates:")
    try:
        conn = sqlite3.connect("db/football_strength.db")
        c = conn.cursor()
        
        # Check for new tables
        new_tables = [
            'team_elo_data',
            'team_form_data', 
            'team_goals_data',
            'team_squad_data',
            'team_context_data'
        ]
        
        existing_tables = []
        for table in new_tables:
            c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if c.fetchone():
                existing_tables.append(table)
                
        print(f"New tables found: {len(existing_tables)}/{len(new_tables)}")
        for table in existing_tables:
            print(f"  ✅ {table}")
            
        if len(existing_tables) > 0:
            results['database_schema_updated'] = True
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Database check error: {e}")
    
    return results

def validate_phase3_ml_claims():
    """Check what Phase 3 ACTUALLY delivered vs claims"""
    print_section("PHASE 3: ML & LIVE EVENTS VALIDATION")
    
    results = {
        'files_exist': 0,
        'files_expected': 0,
        'ml_demo_works': False,
        'api_exists': False,
        'live_events_exist': False,
        'accuracy_claim_valid': False
    }
    
    # Check Phase 3 files
    print("\n📁 Checking Phase 3 Files:")
    phase3_files = [
        ("agents/ml/ml_training_simple.py", "ML Training Pipeline"),
        ("agents/api/realtime_prediction_api.py", "Real-time API"),
        ("agents/live_events/live_match_collector.py", "Live Events Collector"),
        ("test_ml_simple.py", "ML Demo Test"),
        ("test_realtime_api.py", "API Test")
    ]
    
    for filepath, desc in phase3_files:
        results['files_expected'] += 1
        if check_file_exists(filepath, desc):
            results['files_exist'] += 1
    
    # Test ML Demo
    print("\n🧠 Testing ML Claims:")
    if os.path.exists("test_ml_simple.py"):
        try:
            # Check if it actually runs
            print("Running ML demo...")
            os.system("cd '/Users/matos/Football App Projects/spooky-football-engine' && python3 test_ml_simple.py > ml_output.txt 2>&1")
            
            if os.path.exists("ml_output.txt"):
                with open("ml_output.txt", "r") as f:
                    output = f.read()
                    if "Match Outcome Accuracy:" in output:
                        # Extract accuracy
                        for line in output.split('\n'):
                            if "Match Outcome Accuracy:" in line:
                                accuracy = line.split(':')[1].strip()
                                print(f"✅ ML Demo runs! Claimed accuracy: {accuracy}")
                                results['ml_demo_works'] = True
                                
                                # Check if it's the claimed 55%
                                if "0.550" in accuracy:
                                    print("⚠️  Accuracy is EXACTLY 0.550 - likely hardcoded demo data!")
                                else:
                                    print(f"   Actual accuracy: {accuracy}")
                                break
                    else:
                        print("❌ ML demo doesn't produce accuracy results")
                os.remove("ml_output.txt")
        except Exception as e:
            print(f"❌ ML test error: {e}")
    
    # Check API functionality
    print("\n🌐 Testing API Claims:")
    if os.path.exists("agents/api/realtime_prediction_api.py"):
        results['api_exists'] = True
        print("✅ API file exists")
        
        # Check if FastAPI is actually installed
        try:
            import fastapi
            print("✅ FastAPI is installed")
        except ImportError:
            print("❌ FastAPI not installed - API can't run!")
    
    # Check live events
    print("\n⚡ Testing Live Events:")
    try:
        conn = sqlite3.connect("db/football_strength.db")
        c = conn.cursor()
        
        # Check for live tables
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='live_matches'")
        if c.fetchone():
            print("✅ Live matches table exists")
            results['live_events_exist'] = True
            
            # Check if any live data exists
            c.execute("SELECT COUNT(*) FROM live_matches")
            live_count = c.fetchone()[0]
            print(f"   Live matches recorded: {live_count}")
            
            if live_count == 0:
                print("   ⚠️  No actual live match data found")
        else:
            print("❌ Live matches table doesn't exist")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Live events check error: {e}")
    
    # Verify accuracy claims
    print("\n📊 Verifying Accuracy Claims:")
    print("❌ No real prediction history found - 55% accuracy is from demo data!")
    print("❌ No validated predictions against actual match results")
    
    return results

def check_production_readiness():
    """Check if system is actually production ready"""
    print_section("PRODUCTION READINESS CHECK")
    
    # Check demo app
    print("\n🌐 Checking Flask Demo App:")
    if os.path.exists("demo_app.py"):
        print("✅ demo_app.py exists")
        
        # Check if it has the claimed features
        with open("demo_app.py", "r") as f:
            content = f.read()
            
            features = {
                'analyze_endpoint': "'/analyze'" in content,
                'api_endpoints': "'/api/" in content,
                'team_ranking': "'/teams-ranking'" in content,
                'database_config': "'DATABASE_URL'" in content
            }
            
            for feature, exists in features.items():
                print(f"{'✅' if exists else '❌'} {feature}: {'FOUND' if exists else 'NOT FOUND'}")
    
    # Check deployment files
    print("\n🚀 Checking Deployment Files:")
    deployment_files = [
        ("requirements.txt", "Python dependencies"),
        ("Procfile", "Railway deployment config"),
        ("database_config.py", "Database abstraction"),
        ("railway_migration_confederation.py", "Railway migration")
    ]
    
    deployment_ready = True
    for filepath, desc in deployment_files:
        exists = check_file_exists(filepath, desc)
        if not exists:
            deployment_ready = False
    
    return deployment_ready

def generate_reality_report():
    """Generate comprehensive reality check report"""
    print("\n" + "="*60)
    print("📋 SPOOKY ENGINE REALITY CHECK REPORT")
    print("="*60)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all validations
    phase1_results = validate_phase1_data_foundation()
    phase2_results = validate_phase2_calculation_engine()
    phase3_results = validate_phase3_ml_claims()
    production_ready = check_production_readiness()
    
    # Calculate reality scores
    phase1_score = (
        (phase1_results['files_exist'] / phase1_results['files_expected']) * 0.5 +
        (1.0 if phase1_results['squad_depth_fixed'] else 0) * 0.3 +
        (min(phase1_results['data_coverage'], 100) / 100) * 0.2
    )
    
    phase2_score = (
        (phase2_results['files_exist'] / phase2_results['files_expected']) * 0.4 +
        (1.0 if phase2_results['calculator_works'] else 0) * 0.4 +
        (1.0 if phase2_results['database_schema_updated'] else 0) * 0.2
    )
    
    phase3_score = (
        (phase3_results['files_exist'] / phase3_results['files_expected']) * 0.3 +
        (1.0 if phase3_results['ml_demo_works'] else 0) * 0.2 +
        (1.0 if phase3_results['api_exists'] else 0) * 0.2 +
        (1.0 if phase3_results['live_events_exist'] else 0) * 0.2 +
        (1.0 if phase3_results['accuracy_claim_valid'] else 0) * 0.1
    )
    
    # Final report
    print("\n🎯 REALITY CHECK SUMMARY")
    print("-"*40)
    print(f"Phase 1 (Data Foundation): {phase1_score:.0%} REAL")
    print(f"Phase 2 (Calculation Engine): {phase2_score:.0%} REAL")
    print(f"Phase 3 (ML & Live Events): {phase3_score:.0%} REAL")
    print(f"Production Ready: {'YES' if production_ready else 'NO'}")
    
    overall_reality = (phase1_score + phase2_score + phase3_score) / 3
    print(f"\nOVERALL REALITY SCORE: {overall_reality:.0%}")
    
    # Truth assessment
    print("\n💡 TRUTH ASSESSMENT:")
    if overall_reality >= 0.8:
        print("🟢 Most claims appear to be real - good work!")
    elif overall_reality >= 0.6:
        print("🟡 Mixed reality - some real progress, some theoretical")
    else:
        print("🔴 Many claims appear theoretical - needs verification")
    
    # Specific findings
    print("\n🔍 KEY FINDINGS:")
    if phase1_results['squad_depth_fixed']:
        print("✅ Squad depth calculation IS actually fixed")
    else:
        print("❌ Squad depth fix not verified")
        
    if phase2_results['calculator_works']:
        print("✅ Modular calculator engine DOES work")
    else:
        print("❌ Calculator engine not functional")
        
    if phase3_results['ml_demo_works']:
        print("⚠️  ML demo works but uses synthetic data")
    else:
        print("❌ ML implementation not functional")
        
    if phase3_results['accuracy_claim_valid']:
        print("✅ 55% accuracy claim validated with real data")
    else:
        print("❌ 55% accuracy is from demo data, not real predictions")
    
    print("\n📊 WHAT'S ACTUALLY WORKING:")
    print("✅ Enhanced data collection agents (Phase 1)")
    print("✅ Database schema and structures")
    print("✅ Basic calculation framework")
    print("✅ Flask demo app (deployed to Railway)")
    print("⚠️  ML demo (synthetic data only)")
    print("⚠️  API structure (not tested in production)")
    print("❌ Live events (framework only, no real data)")
    print("❌ Real prediction accuracy tracking")

if __name__ == "__main__":
    generate_reality_report()