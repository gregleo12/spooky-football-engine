#!/usr/bin/env python3
import subprocess
import time
import json
import requests

print("🚀 Starting ngrok tunnel...")

# Kill existing ngrok
subprocess.run(["pkill", "-f", "ngrok"], capture_output=True)
time.sleep(1)

# Start ngrok in background
process = subprocess.Popen(["ngrok", "http", "5001"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
time.sleep(3)

try:
    # Get tunnel info from ngrok API
    response = requests.get("http://localhost:4040/api/tunnels")
    data = response.json()
    
    if data["tunnels"]:
        public_url = data["tunnels"][0]["public_url"]
        print("\n✅ SUCCESS! Your app is now publicly accessible!\n")
        print(f"🌐 Public URL: {public_url}")
        print(f"\n📤 Share this link with anyone:")
        print(f"   {public_url}")
        print("\n📊 ngrok dashboard: http://localhost:4040")
        print("\n⚠️  Keep this terminal open to maintain the connection")
        print("⚠️  Press Ctrl+C to stop sharing\n")
    else:
        print("❌ No tunnels found. Make sure Flask app is running on port 5001")
        
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nTry running manually:")
    print("  ngrok http 5001")
    print("\nThen look for the 'Forwarding' URL in the output")

# Keep running
try:
    process.wait()
except KeyboardInterrupt:
    print("\n👋 Stopping ngrok tunnel...")
    process.terminate()