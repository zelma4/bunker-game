#!/bin/bash

# Quick Local Test Script - Port 8765
# This script runs the app locally for testing before deploying to server

set -e

echo "🧪 Starting Bunker Game locally on port 8765..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r backend/requirements.txt -q

# Create data directory for SQLite
mkdir -p data

# Run the application
echo "▶️  Starting server on http://0.0.0.0:8765"
echo ""
echo "📡 Access the game:"
echo "   - Local: http://localhost:8765"
echo "   - Network: http://$(ipconfig getifaddr en0 2>/dev/null || hostname -I | awk '{print $1}' || echo 'YOUR_IP'):8765"
echo ""
echo "Press Ctrl+C to stop"
echo ""

uvicorn backend.app.main:app --host 0.0.0.0 --port 8765 --reload
