#!/bin/bash
# ========================================
# Complete Deployment Commands for Yoda
# Server: 68.183.88.5
# Model: alibayram/medgemma:4b via Ollama
# ========================================

# STEP 1: SSH into your server
# Run this command from your local machine:
# ssh root@68.183.88.5

# STEP 2: Once on the server, run the following commands:

# Update system
echo "Updating system..."
apt-get update && apt-get upgrade -y

# Install dependencies
echo "Installing dependencies..."
apt-get install -y curl git wget

# Install Docker
echo "Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh
systemctl enable docker
systemctl start docker

# Install Docker Compose
echo "Installing Docker Compose..."
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Verify installations
echo "Verifying installations..."
docker --version
docker-compose --version

# Clean up old containers (if any)
echo "Cleaning up old containers..."
docker stop $(docker ps -aq) 2>/dev/null || true
docker rm $(docker ps -aq) 2>/dev/null || true
docker system prune -af --volumes

# Clone repository
echo "Cloning repository..."
cd /opt
rm -rf yoda  # Remove if exists
git clone https://github.com/Tharun2302/yoda.git
cd yoda

# Setup environment
echo "Setting up environment..."
cp env.ollama.template .env

# Build and start services
echo "Building Docker images (this may take a few minutes)..."
docker-compose -f docker-compose.ollama.yml build --no-cache

echo "Starting services..."
docker-compose -f docker-compose.ollama.yml up -d

# Wait for services to be ready
echo "Waiting for services to start (30 seconds)..."
sleep 30

# Pull Medgemma model
echo "Pulling Medgemma model (this may take 5-10 minutes)..."
docker exec yoda-ollama ollama pull alibayram/medgemma:4b

# Verify model installation
echo "Verifying model installation..."
docker exec yoda-ollama ollama list

# Check service health
echo "Checking service health..."
sleep 10

echo "Checking Ollama..."
docker exec yoda-ollama curl -f http://localhost:11434/api/tags && echo "✓ Ollama OK" || echo "✗ Ollama FAILED"

echo "Checking Application..."
curl -f http://localhost:8002/health && echo "✓ Application OK" || echo "✗ Application FAILED"

echo "Checking MongoDB..."
docker exec yoda-mongodb mongosh --eval "db.adminCommand('ping')" && echo "✓ MongoDB OK" || echo "✗ MongoDB FAILED"

# Show container status
echo ""
echo "Container Status:"
docker-compose -f docker-compose.ollama.yml ps

# Show logs
echo ""
echo "Recent Logs:"
docker-compose -f docker-compose.ollama.yml logs --tail=20

echo ""
echo "=========================================="
echo "DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "Access your application:"
echo "  Main App: http://68.183.88.5:8002"
echo "  Ollama API: http://68.183.88.5:11434"
echo ""
echo "To view logs:"
echo "  cd /opt/yoda"
echo "  docker-compose -f docker-compose.ollama.yml logs -f"
echo ""
echo "To restart services:"
echo "  cd /opt/yoda"
echo "  docker-compose -f docker-compose.ollama.yml restart"
echo ""
echo "To stop services:"
echo "  cd /opt/yoda"
echo "  docker-compose -f docker-compose.ollama.yml down"
echo ""

