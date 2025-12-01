#!/bin/bash

# ========================================
# Yoda Deployment Script with Ollama
# ========================================

set -e

echo "=========================================="
echo "Yoda Deployment with Ollama + Medgemma"
echo "=========================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

echo -e "${GREEN}Step 1: Updating system packages...${NC}"
apt-get update
apt-get upgrade -y

echo -e "${GREEN}Step 2: Installing Docker...${NC}"
# Install Docker if not present
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl enable docker
    systemctl start docker
    echo -e "${GREEN}Docker installed successfully${NC}"
else
    echo -e "${YELLOW}Docker already installed${NC}"
fi

echo -e "${GREEN}Step 3: Installing Docker Compose...${NC}"
# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}Docker Compose installed successfully${NC}"
else
    echo -e "${YELLOW}Docker Compose already installed${NC}"
fi

echo -e "${GREEN}Step 4: Cloning repository...${NC}"
cd /opt
if [ -d "yoda" ]; then
    echo -e "${YELLOW}Directory exists, pulling latest changes...${NC}"
    cd yoda
    git pull
else
    git clone https://github.com/Tharun2302/yoda.git
    cd yoda
fi

echo -e "${GREEN}Step 5: Setting up environment file...${NC}"
cp .env.ollama .env

echo -e "${GREEN}Step 6: Stopping existing containers...${NC}"
docker-compose -f docker-compose.ollama.yml down || true

echo -e "${GREEN}Step 7: Building Docker images...${NC}"
docker-compose -f docker-compose.ollama.yml build --no-cache

echo -e "${GREEN}Step 8: Starting services...${NC}"
docker-compose -f docker-compose.ollama.yml up -d

echo -e "${GREEN}Step 9: Waiting for Ollama to start...${NC}"
sleep 30

echo -e "${GREEN}Step 10: Pulling Medgemma model...${NC}"
docker exec yoda-ollama ollama pull alibayram/medgemma:4b

echo -e "${GREEN}Step 11: Checking service health...${NC}"
sleep 10

# Check Ollama
if docker exec yoda-ollama curl -f http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Ollama is running${NC}"
else
    echo -e "${RED}✗ Ollama is not responding${NC}"
fi

# Check Application
if curl -f http://localhost:8002/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Application is running${NC}"
else
    echo -e "${RED}✗ Application is not responding${NC}"
fi

# Check MongoDB
if docker exec yoda-mongodb mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ MongoDB is running${NC}"
else
    echo -e "${RED}✗ MongoDB is not responding${NC}"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Deployment Complete!${NC}"
echo "=========================================="
echo ""
echo "Access your application at:"
echo "  - Main App: http://68.183.88.5:8002"
echo "  - Ollama API: http://68.183.88.5:11434"
echo ""
echo "To view logs:"
echo "  docker-compose -f docker-compose.ollama.yml logs -f"
echo ""
echo "To stop services:"
echo "  docker-compose -f docker-compose.ollama.yml down"
echo ""

