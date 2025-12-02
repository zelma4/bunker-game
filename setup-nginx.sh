#!/bin/bash

# Nginx Setup Script - Works with or without domain
# Run this script on your server after deploying the application

set -e

APP_PORT="8765"

echo "🌐 Setting up Nginx..."
echo ""

# Ask if user has a domain
read -p "Do you have a domain configured? (y/n) " -n 1 -r
echo
HAS_DOMAIN=$REPLY

if [[ $HAS_DOMAIN =~ ^[Yy]$ ]]; then
    read -p "Enter your domain (e.g., bunker.zelma4.me): " DOMAIN
    if [ -z "$DOMAIN" ]; then
        echo "❌ Domain cannot be empty!"
        exit 1
    fi
    CONFIG_NAME="$DOMAIN"
    SERVER_NAME="$DOMAIN"
else
    CONFIG_NAME="bunker-game"
    SERVER_NAME="_"
    echo "ℹ️  Will configure for IP access (no domain)"
fi

# Check if nginx is installed
if ! command -v nginx &> /dev/null; then
    echo "📦 Installing Nginx..."
    apt update
    apt install nginx -y
else
    echo "✓ Nginx already installed"
fi

# Create nginx config
echo "📝 Creating Nginx configuration..."
tee /etc/nginx/sites-available/${CONFIG_NAME} > /dev/null <<EOF
# Bunker Game - ${CONFIG_NAME}
server {
    listen 80;
    listen [::]:80;
    server_name ${SERVER_NAME};

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
ln -sf /etc/nginx/sites-available/${CONFIG_NAME} /etc/nginx/sites-enabled/

# Remove default if it exists and we're using IP
if [[ ! $HAS_DOMAIN =~ ^[Yy]$ ]]; then
    rm -f /etc/nginx/sites-enabled/default
fi

# Test nginx config
echo "🧪 Testing Nginx configuration..."
nginx -t

# Restart nginx
echo "🔄 Restarting Nginx..."
systemctl restart nginx

# Configure firewall
echo "🔥 Configuring firewall..."
ufw allow 80/tcp 2>/dev/null || true
ufw allow 443/tcp 2>/dev/null || true
ufw --force enable 2>/dev/null || true

echo ""
echo "✅ Nginx configured successfully!"
echo ""

# Get server IP
SERVER_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "YOUR_SERVER_IP")

if [[ $HAS_DOMAIN =~ ^[Yy]$ ]]; then
    echo "📋 Next steps:"
    echo "   1. Make sure DNS A record points to: $SERVER_IP"
    echo "   2. Check: http://${DOMAIN}"
    echo ""
    echo "🔒 To add SSL (HTTPS), run:"
    echo "   apt install certbot python3-certbot-nginx -y"
    echo "   certbot --nginx -d ${DOMAIN}"
else
    echo "📋 Access your application:"
    echo "   🌐 http://${SERVER_IP}"
    echo ""
    echo "ℹ️  Note: No SSL without domain. For HTTPS, you need a domain."
fi

echo ""
echo "📊 Useful commands:"
echo "   nginx -t                              # Test config"
echo "   systemctl restart nginx               # Restart Nginx"
echo "   tail -f /var/log/nginx/bunker_*.log   # View logs"
