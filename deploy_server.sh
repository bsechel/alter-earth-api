#!/bin/bash

# FastAPI Deployment Script for EC2
# Run this script on your EC2 server as ubuntu user

set -e  # Exit on any error

echo "🚀 Starting FastAPI deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

APP_DIR="/niebosys/deploy/alter-earth-api"
APP_USER="altearth"
SERVICE_NAME="altearth-api"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please run this script as ubuntu user, not root!"
    exit 1
fi

print_status "Step 1: Installing system dependencies..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git curl

print_status "Step 2: Creating application user..."
if ! id "$APP_USER" &>/dev/null; then
    sudo adduser --system --group --disabled-password $APP_USER
    print_status "Created user: $APP_USER"
else
    print_warning "User $APP_USER already exists"
fi

print_status "Step 3: Setting up application directory..."
if [ ! -d "$APP_DIR" ]; then
    print_error "Application directory $APP_DIR not found!"
    print_error "Please make sure your code is deployed to $APP_DIR"
    exit 1
fi

# Change ownership to app user
sudo chown -R $APP_USER:$APP_USER $APP_DIR

print_status "Step 4: Setting up Python virtual environment..."
sudo -u $APP_USER python3 -m venv $APP_DIR/venv

print_status "Step 5: Installing Python dependencies..."
sudo -u $APP_USER $APP_DIR/venv/bin/pip install --upgrade pip
sudo -u $APP_USER $APP_DIR/venv/bin/pip install -r $APP_DIR/requirements.txt

print_status "Step 6: Creating environment file..."
if [ ! -f "$APP_DIR/.env" ]; then
    sudo -u $APP_USER tee $APP_DIR/.env > /dev/null << EOF
DATABASE_URL=postgresql://user:password@localhost/altearth_db
CLAUDE_API_KEY=your_claude_api_key_here
SECRET_KEY=$(openssl rand -hex 32)
ENVIRONMENT=production
HOST=0.0.0.0
PORT=8000
EOF
    print_warning "Created .env file with default values. Please update it with your actual credentials!"
else
    print_warning ".env file already exists. Skipping creation."
fi

print_status "Step 7: Creating systemd service..."
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null << EOF
[Unit]
Description=Alter Earth FastAPI application
After=network.target

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

print_status "Step 8: Enabling and starting the service..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

# Check service status
if sudo systemctl is-active --quiet $SERVICE_NAME; then
    print_status "✅ Service $SERVICE_NAME is running!"
else
    print_error "❌ Service failed to start. Check logs with:"
    print_error "sudo journalctl -u $SERVICE_NAME -f"
    exit 1
fi

print_status "Step 9: Configuring nginx for subdomain setup..."

# API configuration (api.alter.earth)
sudo tee /etc/nginx/sites-available/api-altearth > /dev/null << EOF
# API Server Configuration (api.alter.earth)
server {
    listen 80;
    server_name api.alter.earth;
    
    client_max_body_size 50M;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # API endpoints
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # CORS headers for API
        add_header 'Access-Control-Allow-Origin' 'https://alter.earth' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization' always;
        add_header 'Access-Control-Expose-Headers' 'Content-Length,Content-Range' always;
        
        # Handle preflight requests
        if (\$request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' 'https://alter.earth';
            add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS';
            add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization';
            add_header 'Access-Control-Max-Age' 1728000;
            add_header 'Content-Type' 'text/plain; charset=utf-8';
            add_header 'Content-Length' 0;
            return 204;
        }
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Health check endpoint (no CORS needed)
    location /health {
        access_log off;
        proxy_pass http://127.0.0.1:8000/health;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Frontend placeholder configuration (alter.earth)
sudo tee /etc/nginx/sites-available/frontend-altearth > /dev/null << EOF
# Frontend Server Configuration (alter.earth)
server {
    listen 80;
    server_name alter.earth www.alter.earth;
    
    # Temporary redirect to API docs until frontend is ready
    location / {
        return 302 https://api.alter.earth/docs;
    }
    
    # You can replace this with your frontend app later:
    # root /var/www/alter.earth;
    # index index.html index.htm;
    # try_files \$uri \$uri/ /index.html;
}
EOF

# Enable both nginx sites
sudo ln -sf /etc/nginx/sites-available/api-altearth /etc/nginx/sites-enabled/
sudo ln -sf /etc/nginx/sites-available/frontend-altearth /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
if sudo nginx -t; then
    print_status "✅ Nginx configuration is valid"
    sudo systemctl reload nginx
else
    print_error "❌ Nginx configuration is invalid!"
    exit 1
fi

print_status "Step 10: Setting up log rotation..."
sudo tee /etc/logrotate.d/$SERVICE_NAME > /dev/null << EOF
/var/log/$SERVICE_NAME/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 $APP_USER $APP_USER
}
EOF

print_status "Step 11: Creating log directory..."
sudo mkdir -p /var/log/$SERVICE_NAME
sudo chown $APP_USER:$APP_USER /var/log/$SERVICE_NAME

print_status "Step 12: Final checks..."
sleep 3

# Test the API
if curl -f http://127.0.0.1:8000/ > /dev/null 2>&1; then
    print_status "✅ API is responding locally"
else
    print_warning "⚠️  API might not be responding yet, check logs"
fi

# Get public IP
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "unknown")

echo ""
echo "🎉 Deployment completed!"
echo ""
echo "📋 Next steps:"
echo "   1. Set up DNS records:"
echo "      - A record: alter.earth → $PUBLIC_IP"
echo "      - A record: api.alter.earth → $PUBLIC_IP"
echo "      - A record: www.alter.earth → $PUBLIC_IP"
echo ""
echo "   2. Update your .env file with actual credentials:"
echo "      sudo nano $APP_DIR/.env"
echo ""
echo "   3. Restart the service after updating .env:"
echo "      sudo systemctl restart $SERVICE_NAME"
echo ""
echo "   4. Set up SSL certificates (after DNS propagation):"
echo "      sudo apt install certbot python3-certbot-nginx"
echo "      sudo certbot --nginx -d alter.earth -d www.alter.earth -d api.alter.earth"
echo ""
echo "   5. Test your setup:"
echo "      Local API: http://127.0.0.1:8000"
if [ "$PUBLIC_IP" != "unknown" ]; then
echo "      Public API: http://$PUBLIC_IP (temp, until DNS)"
echo "      Final API: https://api.alter.earth"
echo "      Frontend: https://alter.earth"
fi
echo "      API Docs: https://api.alter.earth/docs"
echo ""
echo "🔧 Useful commands:"
echo "   Check service status: sudo systemctl status $SERVICE_NAME"
echo "   View logs: sudo journalctl -u $SERVICE_NAME -f"
echo "   Restart service: sudo systemctl restart $SERVICE_NAME"
echo "   Reload nginx: sudo systemctl reload nginx"
echo "   Check SSL status: sudo certbot certificates"
echo ""
echo "🌍 Domain Setup:"
echo "   Frontend: https://alter.earth (redirects to API docs for now)"
echo "   API: https://api.alter.earth"
echo "   API Documentation: https://api.alter.earth/docs"
echo "   Health Check: https://api.alter.earth/health"
echo ""
echo "🔒 Security features included:"
echo "   ✅ Security headers configured"
echo "   ✅ CORS properly configured for alter.earth"
echo "   ✅ Service runs as non-root user"
echo "   ✅ Ready for SSL certificate installation"
echo "   ✅ Health monitoring endpoint"