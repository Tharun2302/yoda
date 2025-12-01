#!/bin/bash

# ========================================
# Update Existing Yoda Deployment
# Server: 68.183.88.5
# ========================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Updating Yoda Deployment${NC}"
echo -e "${GREEN}========================================${NC}"

# Navigate to project directory
cd /opt/yoda

echo -e "${GREEN}Step 1: Pulling latest code from GitHub...${NC}"
git pull origin main

echo -e "${GREEN}Step 2: Stopping current services...${NC}"
docker-compose -f docker-compose.ollama.yml down

echo -e "${GREEN}Step 3: Rebuilding Docker images...${NC}"
docker-compose -f docker-compose.ollama.yml build --no-cache

echo -e "${GREEN}Step 4: Starting services...${NC}"
docker-compose -f docker-compose.ollama.yml up -d

echo -e "${GREEN}Step 5: Waiting for services to start...${NC}"
sleep 20

echo -e "${GREEN}Step 6: Checking service health...${NC}"

# Check Ollama
if curl -f http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Ollama is running${NC}"
else
    echo -e "${YELLOW}⚠ Ollama starting (may need more time)${NC}"
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
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Update Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Access your application at:"
echo "  - Main App: http://68.183.88.5:8002"
echo "  - Ollama API: http://68.183.88.5:11434"
echo ""
echo "To view logs:"
echo "  docker-compose -f docker-compose.ollama.yml logs -f"
echo ""

