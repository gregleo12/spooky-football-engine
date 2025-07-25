#!/bin/bash

echo "🚀 Starting Football Strength Analyzer sharing..."
echo "================================================"

# Kill any existing ngrok processes
pkill -f ngrok || true

# Start ngrok in background
ngrok http 5001 > /dev/null 2>&1 &
NGROK_PID=$!

# Wait for ngrok to start
sleep 3

# Get the public URL
PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys, json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])" 2>/dev/null)

if [ -z "$PUBLIC_URL" ]; then
    echo "❌ Failed to get public URL. Trying alternative method..."
    # Try to get URL from ngrok output
    ngrok http 5001 &
    sleep 5
    echo ""
    echo "Look for the 'Forwarding' line above for your public URL"
else
    echo ""
    echo "✅ Your app is now publicly accessible!"
    echo ""
    echo "🌐 Public URL: $PUBLIC_URL"
    echo ""
    echo "📤 Share this link with anyone: $PUBLIC_URL"
    echo ""
    echo "⚠️  Notes:"
    echo "   - This URL will change each time you restart"
    echo "   - Keep this terminal open to maintain the connection"
    echo "   - Press Ctrl+C to stop sharing"
fi

echo ""
echo "📊 ngrok dashboard: http://localhost:4040"
echo ""

# Keep script running
wait $NGROK_PID