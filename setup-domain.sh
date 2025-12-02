#!/bin/bash

# Auto-setup script for bunker.zelma4.me domain
# Run this script on your server after DNS is configured

set -e

DOMAIN="bunker.zelma4.me"
EMAIL="your-email@example.com"  # CHANGE THIS!

echo "🌐 Setting up bunker.zelma4.me domain..."
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root or with sudo"
    exit 1
fi

# Get email for SSL certificate
read -p "Enter your email for SSL certificate: " EMAIL

if [ -z "$EMAIL" ]; then
    echo "❌ Email is required!"
    exit 1
fi

echo ""
echo "📋 Configuration:"
echo "   Domain: $DOMAIN"
echo "   Email: $EMAIL"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Install Nginx
echo "📦 Installing Nginx..."
apt update
apt install -y nginx

# Install Certbot
echo "📦 Installing Certbot..."
apt install -y certbot python3-certbot-nginx

# Copy nginx config (HTTP only first, SSL will be added by certbot)
echo "📝 Creating Nginx configuration..."
cat > /etc/nginx/sites-available/$DOMAIN << 'EOF'
# Bunker Game - HTTP (SSL will be configured by certbot)
server {
    listen 80;
    listen [::]:80;
    server_name bunker.zelma4.me;

    # Logs
    access_log /var/log/nginx/bunker.zelma4.me.access.log;
    error_log /var/log/nginx/bunker.zelma4.me.error.log;

    # Max upload size
    client_max_body_size 10M;

    # Proxy to FastAPI backend
    location / {
        proxy_pass http://127.0.0.1:8765;
        proxy_http_version 1.1;
        
        # WebSocket support
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for WebSocket
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }
}
EOF

# Enable site
echo "🔗 Enabling site..."
ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/

# Remove default if exists
rm -f /etc/nginx/sites-enabled/default

# Test nginx config
echo "🧪 Testing Nginx configuration..."
nginx -t

# Restart nginx
echo "🔄 Restarting Nginx..."
systemctl restart nginx

# Configure firewall
echo "🔥 Configuring firewall..."
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Get SSL certificate
echo "🔒 Obtaining SSL certificate..."
echo ""
echo "⚠️  Make sure DNS is configured and pointing to this server!"
echo ""
read -p "Continue with SSL setup? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email $EMAIL --redirect
    
    if [ $? -eq 0 ]; then
        echo "✅ SSL certificate obtained successfully!"
    else
        echo "⚠️  SSL certificate failed. You can try again later with:"
        echo "   sudo certbot --nginx -d $DOMAIN"
    fi
else
    echo "⚠️  Skipping SSL setup. Run later with:"
    echo "   sudo certbot --nginx -d $DOMAIN"
fi

echo ""
echo "✅ Domain setup complete!"
echo ""
echo "📊 Next steps:"
echo "   1. Deploy your app: ./deploy-server.sh"
echo "   2. Check logs: sudo tail -f /var/log/nginx/bunker.zelma4.me.error.log"
echo "   3. Visit: https://bunker.zelma4.me"
echo ""
echo "🔧 Useful commands:"
echo "   - Restart Nginx: sudo systemctl restart nginx"
echo "   - Renew SSL: sudo certbot renew"
echo "   - Check app: curl http://localhost:8765"
echo ""
