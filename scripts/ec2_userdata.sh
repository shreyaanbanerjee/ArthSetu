#!/bin/bash
set -ex

# Redirect stdout and stderr to user-data.log
exec > >(tee -a /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

echo "=========================================="
echo "Starting ArthSetu Production Provisioning"
echo "Date: $(date)"
echo "=========================================="

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y git python3-pip python3-venv nginx curl htop jq unzip

# Install Node.js 20 LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs

# Verify versions
python3 --version
node -v
npm -v

# Clone the repository
mkdir -p /opt
cd /opt
if [ -d "/opt/arthsetu" ]; then
    cd /opt/arthsetu
    git fetch origin
    git checkout feature/aws-cedar-production
    git pull origin feature/aws-cedar-production
else
    git clone https://github.com/shreyaanbanerjee/ArthSetu.git /opt/arthsetu
    cd /opt/arthsetu
    git checkout feature/aws-cedar-production
fi

# Set up Python virtual environment
python3 -m venv /opt/arthsetu/.venv
/opt/arthsetu/.venv/bin/pip install --upgrade pip
/opt/arthsetu/.venv/bin/pip install -r /opt/arthsetu/requirements.txt

# Write production .env file
cat << 'EOF' > /opt/arthsetu/.env
APP_ENV=production
DEMO_MODE=false
DEFAULT_LANGUAGE=hi
SCAM_CONFIDENCE_THRESHOLD=0.72
APR_WARNING_THRESHOLD=36.0
MAX_WHATSAPP_REPLY_CHARS=1500

GROQ_API_KEY=${GROQ_API_KEY:-""}
GEMINI_API_KEY=${GEMINI_API_KEY:-"your_gemini_api_key_here"}
SUTRADHAR_MODEL=gemini-2.5-flash
PRAHARI_MODEL=gemini-2.5-flash
BODHAK_MODEL=gemini-2.5-flash
SHILPI_MODEL=gemini-2.5-flash
VIVEK_MODEL=gemini-2.5-flash

DPI_MODE=simulation
NPCI_MERCHANT_ID=ARTHSETU-DEMO
RBI_SACHET_URL=https://sachet.rbi.org.in

FRONTEND_ORIGIN=*
NEXT_PUBLIC_API_BASE_URL=
EOF

# Install cloudflared for public HTTPS access (essential for browser mic permissions)
curl -L --output /usr/local/bin/cloudflared https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
chmod +x /usr/local/bin/cloudflared

# Build Next.js frontend
cd /opt/arthsetu/frontend
npm install
npm run build

# Configure Nginx reverse proxy on port 80
cat << 'EOF' > /etc/nginx/sites-available/default
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    client_max_body_size 50M;

    # API endpoints
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Server-Sent Events (SSE) streaming support
        proxy_set_header Connection '';
        proxy_buffering off;
        proxy_cache off;
        chunked_transfer_encoding off;
        proxy_read_timeout 600s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_set_header Host $host;
    }

    # Next.js web application
    location / {
        proxy_pass http://127.0.0.1:3000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
EOF

nginx -t
systemctl restart nginx

# Create Systemd service for FastAPI backend
cat << 'EOF' > /etc/systemd/system/arthsetu-backend.service
[Unit]
Description=ArthSetu FastAPI Backend Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/arthsetu
ExecStart=/opt/arthsetu/.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=3
EnvironmentFile=/opt/arthsetu/.env

[Install]
WantedBy=multi-user.target
EOF

# Create Systemd service for Next.js frontend
cat << 'EOF' > /etc/systemd/system/arthsetu-frontend.service
[Unit]
Description=ArthSetu Next.js Frontend Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/arthsetu/frontend
ExecStart=/usr/bin/npm start -- -p 3000 -H 127.0.0.1
Restart=always
RestartSec=3
Environment=NODE_ENV=production
EnvironmentFile=/opt/arthsetu/.env

[Install]
WantedBy=multi-user.target
EOF

# Create Systemd service for Cloudflare Tunnel (provides immediate HTTPS with valid SSL)
cat << 'EOF' > /etc/systemd/system/arthsetu-tunnel.service
[Unit]
Description=Cloudflare Tunnel for ArthSetu Public HTTPS
After=network.target nginx.service

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/cloudflared tunnel --url http://127.0.0.1:80 --logfile /var/log/cloudflared.log
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Start and enable all services
systemctl daemon-reload

systemctl enable arthsetu-backend
systemctl start arthsetu-backend

systemctl enable arthsetu-frontend
systemctl start arthsetu-frontend

systemctl enable arthsetu-tunnel
systemctl start arthsetu-tunnel

echo "=========================================="
echo "ArthSetu deployment setup finished!"
echo "Date: $(date)"
echo "=========================================="

