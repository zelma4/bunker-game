#!/bin/bash

# DNS Check Script for bunker.zelma4.me

echo "🔍 Checking DNS for bunker.zelma4.me..."
echo ""

# Check A record
echo "📡 DNS A Record:"
dig +short bunker.zelma4.me A
DIG_RESULT=$(dig +short bunker.zelma4.me A)

if [ -z "$DIG_RESULT" ]; then
    echo "❌ No A record found!"
    echo ""
    echo "📋 What to do:"
    echo "   1. Go to Namecheap.com"
    echo "   2. Domain List → zelma4.me → Manage"
    echo "   3. Advanced DNS → Add New Record"
    echo ""
    echo "   Add this record:"
    echo "   ┌──────────────────────────────┐"
    echo "   │ Type:  A Record              │"
    echo "   │ Host:  bunker                │"
    SERVER_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "YOUR_SERVER_IP")
    echo "   │ Value: $SERVER_IP       │"
    echo "   │ TTL:   Automatic             │"
    echo "   └──────────────────────────────┘"
    echo ""
    echo "   After adding, wait 5-30 minutes for DNS propagation."
else
    echo "✅ Found: $DIG_RESULT"
    SERVER_IP=$(hostname -I | awk '{print $1}' 2>/dev/null)
    
    if [ "$DIG_RESULT" == "$SERVER_IP" ]; then
        echo "✅ DNS points to this server correctly!"
        echo ""
        echo "🧪 Testing connection..."
        if curl -s http://bunker.zelma4.me > /dev/null; then
            echo "✅ HTTP works!"
        else
            echo "⚠️  HTTP not responding yet. Check:"
            echo "   - Nginx: systemctl status nginx"
            echo "   - App: docker-compose ps"
        fi
    else
        echo "⚠️  DNS points to: $DIG_RESULT"
        echo "   But this server is: $SERVER_IP"
        echo ""
        echo "   Update the A record to point to: $SERVER_IP"
    fi
fi

echo ""
echo "📊 Full DNS info:"
dig bunker.zelma4.me

echo ""
echo "🌍 Alternative DNS checks:"
echo "   Google DNS: $(dig @8.8.8.8 +short bunker.zelma4.me A)"
echo "   Cloudflare: $(dig @1.1.1.1 +short bunker.zelma4.me A)"
