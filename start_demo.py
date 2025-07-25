#!/usr/bin/env python3
"""
Start demo with better error handling
"""
import sys
import traceback

try:
    from demo_app import app
    print("✅ Demo app imported successfully")
    print("🚀 Starting server on http://localhost:5001")
    print("📱 Open your browser to see the Football Strength Analyzer")
    print("\nPress Ctrl+C to stop the server\n")
    
    app.run(host='0.0.0.0', port=5001, debug=True)
    
except Exception as e:
    print(f"❌ Error starting demo: {e}")
    traceback.print_exc()
    sys.exit(1)