#!/bin/bash

# Quick fix script for port 8765 access issues
# Run this on your server to open the firewall

set -e

echo "🔥 Checking and fixing firewall settings..."
echo ""

# Check if ufw is installed
if command -v ufw &> /dev/null; then
    echo "📋 Current UFW status:"
    sudo ufw status
    echo ""
    
    echo "🔓 Opening port 8765..."
    sudo ufw allow 8765/tcp
    
    echo "🔓 Opening HTTP and HTTPS ports (for future domain setup)..."
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    
    echo "🔓 Opening SSH (just in case)..."
    sudo ufw allow 22/tcp
    
    echo "✅ Enabling firewall..."
    sudo ufw --force enable
    
    echo ""
    echo "📋 Updated UFW status:"
    sudo ufw status
    
elif command -v firewall-cmd &> /dev/null; then
    echo "📋 Using firewalld..."
    
    echo "🔓 Opening port 8765..."
    sudo firewall-cmd --permanent --add-port=8765/tcp
    
    echo "🔓 Opening HTTP and HTTPS..."
    sudo firewall-cmd --permanent --add-port=80/tcp
    sudo firewall-cmd --permanent --add-port=443/tcp
    
    echo "✅ Reloading firewall..."
    sudo firewall-cmd --reload
    
    echo ""
    echo "📋 Current firewall rules:"
    sudo firewall-cmd --list-all
    
else
    echo "⚠️  No firewall detected (ufw or firewalld)"
    echo "   Port should be accessible"
fi

echo ""
echo "🧪 Testing connection..."
echo ""

# Get server IP
SERVER_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "YOUR_SERVER_IP")

echo "Testing: http://localhost:8765"
if curl -s http://localhost:8765 > /dev/null; then
    echo "✅ Local connection works!"
else
    echo "❌ Local connection failed - app might not be running"
fi

echo ""
echo "📡 Your server IP: $SERVER_IP"
echo "🌐 Try accessing: http://$SERVER_IP:8765"
echo ""
echo "✅ Firewall configured!"
echo ""
echo "If still not working, check your cloud provider's security group settings:"
echo "   - AWS: Security Groups"
echo "   - DigitalOcean: Firewalls"
echo "   - Azure: Network Security Groups"
echo "   - Google Cloud: Firewall Rules"
