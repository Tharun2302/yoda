#!/bin/bash

###############################################################################
# HYoda Deployment Script for Digital Ocean
###############################################################################
# This script automates the deployment of HYoda chatbot to Digital Ocean
# using Docker and Docker Compose.
#
# Usage: ./deploy.sh [options]
# Options:
#   --build         Force rebuild Docker images
#   --no-nginx      Skip nginx (use Flask directly)
#   --help          Show this help message
###############################################################################

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
FORCE_BUILD=false
SKIP_NGINX=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --build)
            FORCE_BUILD=true
            shift
            ;;
        --no-nginx)
            SKIP_NGINX=true
            shift
            ;;
        --help)
            echo "HYoda Deployment Script"
            echo ""
            echo "Usage: ./deploy.sh [options]"
            echo ""
            echo "Options:"
            echo "  --build         Force rebuild Docker images"
            echo "  --no-nginx      Skip nginx (use Flask directly)"
            echo "  --help          Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   HYoda Digital Ocean Deployment Script   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo -e "${YELLOW}Warning: Running as root. Consider using a non-root user.${NC}"
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}ERROR: .env file not found!${NC}"
    echo -e "${YELLOW}Please copy env.template to .env and configure it:${NC}"
    echo -e "  cp env.template .env"
    echo -e "  nano .env  # Edit and add your API keys"
    exit 1
fi

# Check if OPENAI_API_KEY is set
if ! grep -q "OPENAI_API_KEY=sk-" .env; then
    echo -e "${RED}ERROR: OPENAI_API_KEY not configured in .env${NC}"
    echo -e "${YELLOW}Please add your OpenAI API key to .env file${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Environment file found${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}ERROR: Docker is not installed${NC}"
    echo -e "${YELLOW}Installing Docker...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo -e "${GREEN}✓ Docker installed${NC}"
    echo -e "${YELLOW}Note: You may need to log out and back in for group changes to take effect${NC}"
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}ERROR: Docker Compose is not installed${NC}"
    echo -e "${YELLOW}Installing Docker Compose...${NC}"
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}✓ Docker Compose installed${NC}"
fi

# Check if Question BOOK.docx exists
if [ ! -f "docx/Question BOOK.docx" ]; then
    echo -e "${YELLOW}Warning: Question BOOK.docx not found in docx/ directory${NC}"
    echo -e "${YELLOW}Make sure to upload it before starting the application${NC}"
fi

echo -e "${GREEN}✓ Prerequisites checked${NC}"
echo ""

# Stop existing containers
echo -e "${BLUE}Stopping existing containers...${NC}"
docker-compose down || true

# Build images
if [ "$FORCE_BUILD" = true ]; then
    echo -e "${BLUE}Building Docker images (forced rebuild)...${NC}"
    docker-compose build --no-cache
else
    echo -e "${BLUE}Building Docker images...${NC}"
    docker-compose build
fi

echo -e "${GREEN}✓ Docker images built${NC}"
echo ""

# Start services
echo -e "${BLUE}Starting services...${NC}"
if [ "$SKIP_NGINX" = true ]; then
    docker-compose up -d hyoda-app mongodb
    echo -e "${GREEN}✓ Services started (without nginx)${NC}"
else
    docker-compose up -d
    echo -e "${GREEN}✓ All services started${NC}"
fi

echo ""
echo -e "${BLUE}Waiting for services to be healthy...${NC}"
sleep 10

# Check service status
echo ""
echo -e "${BLUE}Service Status:${NC}"
docker-compose ps

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         Deployment Completed! 🎉           ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""

if [ "$SKIP_NGINX" = true ]; then
    echo -e "${YELLOW}Application is running at:${NC}"
    echo -e "  • http://167.71.238.114:8002"
    echo -e "  • http://localhost:8002 (if running locally)"
else
    echo -e "${YELLOW}Application is running at:${NC}"
    echo -e "  • https://167.71.238.114 (HTTPS via nginx) 🔒"
    echo -e "  • http://167.71.238.114 (redirects to HTTPS)"
    echo -e "  • http://167.71.238.114:8002 (direct access, HTTP only)"
    echo ""
    echo -e "${YELLOW}Note:${NC} First-time HTTPS access will show a browser security warning."
    echo -e "      This is normal for self-signed certificates. Click 'Advanced' → 'Proceed'."
fi

echo ""
echo -e "${YELLOW}Available endpoints:${NC}"
echo -e "  • Chatbot:    /index.html"
echo -e "  • Dashboard:  /healthbench/dashboard"
echo -e "  • Health:     /health"
echo ""

echo -e "${YELLOW}Useful commands:${NC}"
echo -e "  • View logs:        docker-compose logs -f"
echo -e "  • View app logs:    docker-compose logs -f hyoda-app"
echo -e "  • Stop services:    docker-compose down"
echo -e "  • Restart:          docker-compose restart"
echo -e "  • Shell access:     docker-compose exec hyoda-app bash"
echo ""

echo -e "${GREEN}Deployment completed successfully!${NC}"

