# deployment_script.sh
#!/bin/bash
"""
Automated deployment script
"""

echo "🚀 Starting IPO Tracker deployment..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
fi

# Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Create project directory
mkdir -p /opt/ipo-tracker
cd /opt/ipo-tracker

# Clone repository (replace with your repo)
git clone <your-repo-url> .

# Create necessary directories
mkdir -p logs backups cache ssl

# Set permissions
chmod 755 logs backups cache

# Generate SSL certificate (self-signed for dev)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/key.pem \
    -out ssl/cert.pem \
    -subj "/C=IN/ST=Maharashtra/L=Mumbai/O=IPOTracker/CN=localhost"

# Create environment file
cat > .env << EOF
DATABASE_URL=postgresql://user:password@postgres:5432/ipo_tracker
REDIS_URL=redis://redis:6379
LOG_LEVEL=INFO
ENABLE_MONITORING=true
ADMIN_PASSWORD=your-secure-password
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EOF

# Build and start services
echo "Building and starting services..."
docker-compose -f docker-compose.prod.yml up -d --build

# Wait for services to start
echo "Waiting for services to start..."
sleep 30

# Check health
if curl -f http://localhost:8000/health; then
    echo "✅ IPO Tracker deployed successfully!"
    echo "🌐 Access your app at: http://localhost:8000"
    echo "📊 Admin panel: http://localhost:8000/admin"
    echo "📈 Monitoring: http://localhost:9090"
else
    echo "❌ Deployment failed. Check logs:"
    docker-compose -f docker-compose.prod.yml logs
fi

print("Complete monitoring and deployment setup ready!")
print("\n🎯 Key Features:")
print("✅ API Health Monitoring")
print("✅ Automated Alerts")
print("✅ Data Backup System")
print("✅ Admin Dashboard")
print("✅ Production Docker Setup")
print("✅ Nginx Load Balancer")
print("✅ SSL/HTTPS Support")
print("✅ Rate Limiting")
print("✅ Automated Deployment")
print("\n🚀 Ready for production!")