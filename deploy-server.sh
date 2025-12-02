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
    
    # Try to get server IP
    SERVER_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "YOUR_SERVER_IP")
    
    # Check if we need to setup Nginx
    echo "🔍 Checking Nginx setup..."
    if ! command -v nginx &> /dev/null; then
        echo "⚠️  Nginx not installed - port 8765 will only be accessible if firewall allows it"
        echo ""
        echo "📋 Options:"
        echo "   1. Open port 8765 in firewall: ./fix-firewall.sh"
        echo "   2. Install Nginx (recommended): ./setup-nginx.sh"
        echo "   3. Setup with domain: ./setup-domain.sh (if you have a domain)"
    else
        # Check if our nginx config exists
        if [ ! -f /etc/nginx/sites-enabled/bunker-game ] && [ ! -f /etc/nginx/sites-enabled/bunker.zelma4.me ]; then
            echo "⚠️  Nginx installed but not configured for Bunker Game"
            echo ""
            read -p "Would you like to setup basic Nginx configuration now? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                echo "🔧 Setting up basic Nginx..."
                sudo ./setup-nginx.sh || echo "⚠️  Nginx setup failed, you can run it manually later"
            fi
        else
            echo "✅ Nginx is configured"
        fi
    fi
    
    echo ""
    echo "📡 Server Information:"
    echo "   Docker Port: 8765"
    
    if command -v nginx &> /dev/null && ([ -f /etc/nginx/sites-enabled/bunker-game ] || [ -f /etc/nginx/sites-enabled/bunker.zelma4.me ]); then
        echo "   Nginx: Configured ✓"
        if [ -f /etc/nginx/sites-enabled/bunker.zelma4.me ]; then
            echo "   🌐 Access: https://bunker.zelma4.me"
        else
            echo "   🌐 Access: http://${SERVER_IP}"
        fi
    else
        echo "   🌐 Direct access: http://${SERVER_IP}:8765"
        echo "   ⚠️  Make sure firewall allows port 8765!"
    fi
    
    echo ""
    echo "📊 To view logs: docker-compose logs -f"
    echo "🛑 To stop: docker-compose down"
    echo ""
else
    echo "❌ Failed to start containers. Check logs with: docker-compose logs"
    exit 1
fi
