#!/bin/bash

# Bunker Game Run Script

echo "🎮 Starting Гра бункер..."
echo ""

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
pip install -r backend/requirements.txt --quiet

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file..."
    cp .env.example .env
fi

# Run the application
echo ""
echo "🚀 Starting server..."
echo "🌐 Access the game at: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop"
echo ""

cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
