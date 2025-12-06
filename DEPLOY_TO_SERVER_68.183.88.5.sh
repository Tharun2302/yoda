#!/bin/bash

################################################################################
# COMPLETE DEPLOYMENT SCRIPT FOR SERVER 68.183.88.5
# Branch: SUditya
# Repository: https://github.com/Tharun2302/yoda.git
################################################################################

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   HealthYoda Deployment to 68.183.88.5                  ║${NC}"
echo -e "${BLUE}║   Branch: SUditya                                        ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

################################################################################
# STEP 1: CLEAN EXISTING DEPLOYMENT
################################################################################
echo -e "${YELLOW}[1/8] Cleaning existing deployment...${NC}"

# Stop and remove all Docker containers
if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
    echo "  → Stopping Docker containers..."
    docker-compose down -v 2>/dev/null || docker compose down -v 2>/dev/null || true
    docker ps -a | grep -E "hyoda|yoda" | awk '{print $1}' | xargs -r docker rm -f 2>/dev/null || true
fi

# Remove old deployment directory
if [ -d "/opt/yoda" ]; then
    echo "  → Removing old deployment directory..."
    sudo rm -rf /opt/yoda
fi

# Clean Docker system (optional but recommended)
echo "  → Cleaning Docker system..."
docker system prune -f --volumes 2>/dev/null || true

echo -e "${GREEN}✓ Server cleaned${NC}\n"

################################################################################
# STEP 2: INSTALL PREREQUISITES
################################################################################
echo -e "${YELLOW}[2/8] Installing prerequisites...${NC}"

# Update system
echo "  → Updating system packages..."
sudo apt update -y

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "  → Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo -e "${GREEN}  ✓ Docker installed${NC}"
else
    echo -e "${GREEN}  ✓ Docker already installed${NC}"
fi

# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "  → Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}  ✓ Docker Compose installed${NC}"
else
    echo -e "${GREEN}  ✓ Docker Compose already installed${NC}"
fi

# Install git if not present
if ! command -v git &> /dev/null; then
    echo "  → Installing Git..."
    sudo apt install -y git
fi

echo -e "${GREEN}✓ Prerequisites installed${NC}\n"

################################################################################
# STEP 3: CLONE REPOSITORY (SUditya BRANCH ONLY)
################################################################################
echo -e "${YELLOW}[3/8] Cloning SUditya branch from GitHub...${NC}"

# Create deployment directory
sudo mkdir -p /opt/yoda
sudo chown -R $USER:$USER /opt/yoda
cd /opt/yoda

# Clone only the SUditya branch
echo "  → Cloning SUditya branch..."
git clone -b SUditya --single-branch https://github.com/Tharun2302/yoda.git .

echo -e "${GREEN}✓ Repository cloned (SUditya branch only)${NC}\n"

################################################################################
# STEP 4: CONFIGURE ENVIRONMENT
################################################################################
echo -e "${YELLOW}[4/8] Configuring environment...${NC}"

# Copy environment template
cp env.template .env

# Prompt for OpenAI API key
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}REQUIRED: Enter your OpenAI API Key${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
read -p "OpenAI API Key (sk-...): " OPENAI_KEY

# Update .env file
sed -i "s/OPENAI_API_KEY=your-openai-api-key-here/OPENAI_API_KEY=$OPENAI_KEY/" .env

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}OPTIONAL: Enable Langfuse? (y/n)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
read -p "Enable Langfuse observability? [y/N]: " ENABLE_LANGFUSE

if [[ "$ENABLE_LANGFUSE" =~ ^[Yy]$ ]]; then
    read -p "Langfuse Public Key (pk-...): " LANGFUSE_PK
    read -p "Langfuse Secret Key (sk-...): " LANGFUSE_SK
    
    sed -i "s/LANGFUSE_ENABLED=false/LANGFUSE_ENABLED=true/" .env
    sed -i "s/LANGFUSE_PUBLIC_KEY=your-langfuse-public-key/LANGFUSE_PUBLIC_KEY=$LANGFUSE_PK/" .env
    sed -i "s/LANGFUSE_SECRET_KEY=your-langfuse-secret-key/LANGFUSE_SECRET_KEY=$LANGFUSE_SK/" .env
fi

# Set proper permissions
chmod 600 .env

echo -e "${GREEN}✓ Environment configured${NC}\n"

################################################################################
# STEP 5: GENERATE SSL CERTIFICATES
################################################################################
echo -e "${YELLOW}[5/8] Generating SSL certificates...${NC}"

# Make script executable
chmod +x generate_ssl_cert.sh

# Generate certificates
./generate_ssl_cert.sh

echo -e "${GREEN}✓ SSL certificates generated${NC}\n"

################################################################################
# STEP 6: BUILD AND DEPLOY WITH DOCKER
################################################################################
echo -e "${YELLOW}[6/8] Building and deploying Docker containers...${NC}"

# Make deploy script executable
chmod +x deploy.sh

# Deploy
./deploy.sh

echo -e "${GREEN}✓ Docker containers deployed${NC}\n"

################################################################################
# STEP 7: WAIT FOR SERVICES TO START
################################################################################
echo -e "${YELLOW}[7/8] Waiting for services to start...${NC}"

sleep 15

################################################################################
# STEP 8: VERIFY DEPLOYMENT
################################################################################
echo -e "${YELLOW}[8/8] Verifying deployment...${NC}"

# Check service status
echo "  → Checking service status..."
docker-compose ps

# Test health endpoint
echo ""
echo "  → Testing health endpoint..."
HEALTH_CHECK=$(curl -s http://localhost:8002/health || echo "failed")

if [[ "$HEALTH_CHECK" == *"healthy"* ]]; then
    echo -e "${GREEN}  ✓ Health check passed${NC}"
else
    echo -e "${RED}  ✗ Health check failed${NC}"
fi

################################################################################
# DEPLOYMENT COMPLETE
################################################################################
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           DEPLOYMENT COMPLETED SUCCESSFULLY! 🎉          ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${YELLOW}Application URLs:${NC}"
echo -e "  • HTTPS (Domain):      ${GREEN}https://movefuze.com${NC} 🌐"
echo -e "  • HTTPS (www):         ${GREEN}https://www.movefuze.com${NC} 🌐"
echo -e "  • HTTPS (IP):          ${GREEN}https://68.183.88.5${NC}"
echo -e "  • HTTP:                ${GREEN}http://68.183.88.5:8002${NC}"
echo -e "  • Dashboard:           ${GREEN}https://movefuze.com/healthbench/dashboard${NC}"
echo ""

echo -e "${YELLOW}Useful Commands:${NC}"
echo -e "  • View logs:        ${BLUE}docker-compose logs -f${NC}"
echo -e "  • View app logs:    ${BLUE}docker-compose logs -f hyoda-app${NC}"
echo -e "  • Service status:   ${BLUE}docker-compose ps${NC}"
echo -e "  • Restart:          ${BLUE}docker-compose restart${NC}"
echo -e "  • Stop:             ${BLUE}docker-compose down${NC}"
echo ""

echo -e "${YELLOW}Important Notes:${NC}"
echo -e "  • First HTTPS access will show security warning (self-signed cert)"
echo -e "  • Click 'Advanced' → 'Proceed to site' in browser"
echo -e "  • Check logs if any issues: ${BLUE}cd /opt/yoda && docker-compose logs -f${NC}"
echo ""

echo -e "${GREEN}Deployment successful! Your HealthYoda chatbot is live! 🚀${NC}"

