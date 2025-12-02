#!/bin/bash

# Quick Nginx Setup Script for bunker.zelma4.me
# Run this script on your server after deploying the application

set -e

DOMAIN="bunker.zelma4.me"
APP_PORT="8765"

echo "🌐 Setting up Nginx for ${DOMAIN}..."

# Check if nginx is installed
if ! command -v nginx &> /dev/null; then
    echo "📦 Installing Nginx..."
    sudo apt update
    sudo apt install nginx -y
else
    echo "✓ Nginx already installed"
fi

# Create nginx config
echo "📝 Creating Nginx configuration..."
sudo tee /etc/nginx/sites-available/${DOMAIN} > /dev/null <<EOF
# Bunker Game - ${DOMAIN}
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN};

    # Logs
    access_log /var/log/nginx/bunker_access.log;
    error_log /var/log/nginx/bunker_error.log;

    # Max upload size
    client_max_body_size 10M;

    # Proxy to FastAPI application
    location / {
        proxy_pass http://127.0.0.1:${APP_PORT};
        proxy_http_version 1.1;
        
        # WebSocket support
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Standard proxy headers
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket timeouts
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }
}
EOF

# Enable site
echo "🔗 Enabling site..."
sudo ln -sf /etc/nginx/sites-available/${DOMAIN} /etc/nginx/sites-enabled/

# Test nginx config
echo "🧪 Testing Nginx configuration..."
sudo nginx -t

# Restart nginx
echo "🔄 Restarting Nginx..."
sudo systemctl restart nginx

echo ""
echo "✅ Nginx configured successfully!"
echo ""
echo "📋 Next steps:"
echo "   1. Make sure your DNS A record points to this server's IP"
echo "   2. Make sure the application is running on port ${APP_PORT}"
echo "   3. Check: http://${DOMAIN}"
echo ""
echo "🔒 To add SSL (HTTPS), run:"
echo "   sudo apt install certbot python3-certbot-nginx -y"
echo "   sudo certbot --nginx -d ${DOMAIN}"
echo ""
echo "📊 Useful commands:"
echo "   sudo nginx -t                           # Test config"
echo "   sudo systemctl restart nginx            # Restart Nginx"
echo "   sudo tail -f /var/log/nginx/bunker_*.log  # View logs"
