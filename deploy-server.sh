#!/bin/bash

# Bunker Game - Server Deployment Script
# Run this script on your server to start the game on port 8765

set -e

echo "🚀 Deploying Bunker Game on port 8765..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down || true

# Build and start containers
echo "🔨 Building Docker image..."
docker-compose build

echo "▶️  Starting containers..."
docker-compose up -d

# Wait for the app to start
echo "⏳ Waiting for application to start..."
sleep 5

# Check if container is running
if docker-compose ps | grep -q "Up"; then
    echo "✅ Bunker Game is running!"
    echo ""
    echo "📡 Server Information:"
    echo "   Port: 8765"
    echo "   Access from any device: http://YOUR_SERVER_IP:8765"
    echo ""
    echo "📊 To view logs: docker-compose logs -f"
    echo "🛑 To stop: docker-compose down"
    echo ""
    
    # Try to get server IP
    SERVER_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "YOUR_SERVER_IP")
    if [ "$SERVER_IP" != "YOUR_SERVER_IP" ]; then
        echo "🌐 Local network access: http://${SERVER_IP}:8765"
    fi
else
    echo "❌ Failed to start containers. Check logs with: docker-compose logs"
    exit 1
fi
