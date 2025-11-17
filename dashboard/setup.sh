#!/bin/bash
# Camel Dashboard Setup Script
# Sets up Nginx, SSL, and dashboard daemon

set -e

DOMAIN="camel.autonomous.theatre"
DASHBOARD_DIR="/home/alice/ConsciousnessDebtor/camel/dashboard"
NGINX_CONF="/etc/nginx/sites-available/camel-dashboard"

echo "🐪 Setting up Camel Autonomous Dashboard"
echo "Domain: $DOMAIN"

# Install dependencies
echo "📦 Installing dependencies..."
sudo apt-get update -qq
sudo apt-get install -y nginx certbot python3-certbot-nginx python3-pip -qq

# Install Python packages
echo "🐍 Installing Python packages..."
pip3 install fastapi uvicorn --quiet

# Create certbot webroot
echo "📁 Creating certbot directories..."
sudo mkdir -p /var/www/certbot

# Copy nginx config (HTTP only first for certbot)
echo "⚙️  Configuring Nginx (HTTP first)..."
cat > /tmp/nginx-camel-http.conf << 'EOF'
server {
    listen 80;
    server_name camel.autonomous.theatre;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        proxy_pass http://127.0.0.1:8700;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

sudo cp /tmp/nginx-camel-http.conf $NGINX_CONF
sudo ln -sf $NGINX_CONF /etc/nginx/sites-enabled/camel-dashboard
sudo nginx -t && sudo systemctl reload nginx

echo "✅ Nginx configured for HTTP"

# Start dashboard server first
echo "🚀 Starting dashboard server..."
cd $DASHBOARD_DIR
nohup python3 server.py > /tmp/camel-dashboard.log 2>&1 &
sleep 3

# Check if running
if pgrep -f "server.py" > /dev/null; then
    echo "✅ Dashboard server running"
else
    echo "❌ Failed to start dashboard server"
    exit 1
fi

# Get SSL certificate
echo "🔐 Obtaining SSL certificate from Let's Encrypt..."
sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@autonomous.theatre --redirect

echo "✅ SSL certificate obtained"

# Update nginx with full SSL config
echo "⚙️  Updating Nginx with SSL..."
sudo cp $DASHBOARD_DIR/nginx.conf $NGINX_CONF
sudo nginx -t && sudo systemctl reload nginx

echo "✅ Nginx configured with SSL"

# Create systemd service for dashboard
echo "📜 Creating systemd service..."
cat > /tmp/camel-dashboard.service << EOF
[Unit]
Description=Camel Autonomous Development Dashboard
After=network.target

[Service]
Type=simple
User=alice
WorkingDirectory=$DASHBOARD_DIR
ExecStart=/usr/bin/python3 server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo cp /tmp/camel-dashboard.service /etc/systemd/system/camel-dashboard.service
sudo systemctl daemon-reload
sudo systemctl enable camel-dashboard
sudo systemctl restart camel-dashboard

echo "✅ Systemd service created and enabled"

# Verify everything is running
echo ""
echo "🎉 Setup Complete!"
echo "===================="
echo "Dashboard URL: https://$DOMAIN"
echo "Dashboard Status: $(systemctl is-active camel-dashboard)"
echo "Nginx Status: $(systemctl is-active nginx)"
echo ""
echo "Commands:"
echo "  View dashboard logs: journalctl -u camel-dashboard -f"
echo "  Restart dashboard: sudo systemctl restart camel-dashboard"
echo "  Check SSL cert: sudo certbot certificates"
echo ""
