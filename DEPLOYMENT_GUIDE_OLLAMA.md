# Yoda Deployment Guide - Ollama + Medgemma

## Complete Step-by-Step Deployment Instructions

### Server Information
- **Server IP**: 68.183.88.5
- **Repository**: https://github.com/Tharun2302/yoda.git
- **Model**: alibayram/medgemma:4b (via Ollama)

---

## Prerequisites

Before starting, ensure you have:
1. SSH access to the server (68.183.88.5)
2. Root or sudo access
3. Internet connection on the server

---

## Step 1: Connect to Your Server

```bash
ssh root@68.183.88.5
```

---

## Step 2: Clean Up Existing Containers (Optional but Recommended)

```bash
# Stop all running containers
docker stop $(docker ps -aq) 2>/dev/null || true

# Remove all containers
docker rm $(docker ps -aq) 2>/dev/null || true

# Remove all images (optional - saves space)
docker rmi $(docker images -q) 2>/dev/null || true

# Remove all volumes (optional - WARNING: deletes data)
docker volume rm $(docker volume ls -q) 2>/dev/null || true

# Clean system
docker system prune -af --volumes
```

---

## Step 3: Install System Dependencies

```bash
# Update system
apt-get update && apt-get upgrade -y

# Install required packages
apt-get install -y curl git wget ca-certificates gnupg lsb-release
```

---

## Step 4: Install Docker

```bash
# Remove old Docker versions
apt-get remove -y docker docker-engine docker.io containerd runc

# Add Docker's official GPG key
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start and enable Docker
systemctl enable docker
systemctl start docker

# Verify Docker installation
docker --version
```

---

## Step 5: Install Docker Compose

```bash
# Download Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Make it executable
chmod +x /usr/local/bin/docker-compose

# Verify installation
docker-compose --version
```

---

## Step 6: Clone the Repository

```bash
# Navigate to /opt directory
cd /opt

# Clone the repository
git clone https://github.com/Tharun2302/yoda.git

# Enter the project directory
cd yoda
```

---

## Step 7: Configure Environment Variables

```bash
# Copy the Ollama environment template
cp .env.ollama .env

# (Optional) Edit the .env file if needed
nano .env
```

The `.env` file should contain:
```env
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=alibayram/medgemma:4b
OLLAMA_API_KEY=ollama
ALLOWED_ORIGINS=http://68.183.88.5,http://68.183.88.5:8002,http://localhost:8002
MONGODB_URI=mongodb://mongodb:27017/
MONGODB_DB=healthyoda
```

---

## Step 8: Build and Start Services

```bash
# Build the Docker images
docker-compose -f docker-compose.ollama.yml build --no-cache

# Start all services in detached mode
docker-compose -f docker-compose.ollama.yml up -d

# Check container status
docker-compose -f docker-compose.ollama.yml ps
```

---

## Step 9: Install Ollama and Pull Medgemma Model

```bash
# Wait for Ollama container to be ready
sleep 30

# Pull the Medgemma model
docker exec yoda-ollama ollama pull alibayram/medgemma:4b

# Verify the model is installed
docker exec yoda-ollama ollama list
```

**Note**: This may take 5-10 minutes depending on your internet speed (model is ~2.7GB)

---

## Step 10: Verify Deployment

```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# Check application health
curl http://localhost:8002/health

# Check all container logs
docker-compose -f docker-compose.ollama.yml logs

# Check specific service logs
docker-compose -f docker-compose.ollama.yml logs yoda-app
docker-compose -f docker-compose.ollama.yml logs ollama
docker-compose -f docker-compose.ollama.yml logs mongodb
```

---

## Step 11: Test the Application

### From your local machine:

```bash
# Test health endpoint
curl http://68.183.88.5:8002/health

# Test Ollama endpoint
curl http://68.183.88.5:11434/api/tags

# Open in browser
# Visit: http://68.183.88.5:8002
```

---

## Step 12: Configure Firewall (If Needed)

```bash
# Allow HTTP traffic
ufw allow 8002/tcp
ufw allow 11434/tcp

# Reload firewall
ufw reload
```

---

## Automated Deployment Script

For convenience, you can use the automated deployment script:

```bash
cd /opt/yoda
chmod +x deploy-ollama.sh
sudo ./deploy-ollama.sh
```

---

## Useful Commands

### View Logs
```bash
# All services
docker-compose -f docker-compose.ollama.yml logs -f

# Specific service
docker-compose -f docker-compose.ollama.yml logs -f yoda-app
docker-compose -f docker-compose.ollama.yml logs -f ollama
docker-compose -f docker-compose.ollama.yml logs -f mongodb
```

### Restart Services
```bash
# Restart all services
docker-compose -f docker-compose.ollama.yml restart

# Restart specific service
docker-compose -f docker-compose.ollama.yml restart yoda-app
docker-compose -f docker-compose.ollama.yml restart ollama
```

### Stop Services
```bash
docker-compose -f docker-compose.ollama.yml down
```

### Update Application
```bash
cd /opt/yoda
git pull
docker-compose -f docker-compose.ollama.yml down
docker-compose -f docker-compose.ollama.yml build --no-cache
docker-compose -f docker-compose.ollama.yml up -d
```

### Check Container Status
```bash
docker ps -a
docker stats
```

### Access Container Shell
```bash
# Application container
docker exec -it yoda-chatbot bash

# Ollama container
docker exec -it yoda-ollama bash

# MongoDB container
docker exec -it yoda-mongodb bash
```

---

## Troubleshooting

### Issue: Ollama not responding
```bash
# Check Ollama logs
docker logs yoda-ollama

# Restart Ollama
docker restart yoda-ollama

# Check if model is installed
docker exec yoda-ollama ollama list
```

### Issue: Application not connecting to Ollama
```bash
# Check network connectivity
docker exec yoda-chatbot curl http://ollama:11434/api/tags

# Check environment variables
docker exec yoda-chatbot env | grep OLLAMA
```

### Issue: Out of memory
```bash
# Check system resources
free -h
df -h

# Stop and prune unused resources
docker system prune -af
```

---

## Testing Locally Before Server Deployment

If you want to test on your local machine first:

```bash
# Clone the repo
git clone https://github.com/Tharun2302/yoda.git
cd yoda

# Copy environment file
cp .env.ollama .env

# Update .env for local testing
nano .env
# Change: ALLOWED_ORIGINS=http://localhost:8002,http://127.0.0.1:8002

# Build and run
docker-compose -f docker-compose.ollama.yml up -d

# Wait for Ollama and pull model
sleep 30
docker exec yoda-ollama ollama pull alibayram/medgemma:4b

# Test
curl http://localhost:8002/health
```

Then open http://localhost:8002 in your browser.

---

## Security Recommendations

1. **Firewall**: Only expose necessary ports (8002, 11434)
2. **HTTPS**: Consider setting up SSL/TLS with Let's Encrypt
3. **Authentication**: Add authentication for production use
4. **Monitoring**: Set up monitoring for resource usage
5. **Backups**: Regular backups of MongoDB data

---

## Architecture

```
┌─────────────────┐
│   Internet      │
└────────┬────────┘
         │
    ┌────▼────┐
    │  Port   │
    │  8002   │
    └────┬────┘
         │
    ┌────▼──────────┐
    │  Yoda App     │
    │  Container    │
    └───┬───────┬───┘
        │       │
   ┌────▼───┐  │
   │ Ollama │  │
   │ :11434 │  │
   └────────┘  │
               │
          ┌────▼────┐
          │ MongoDB │
          │ :27017  │
          └─────────┘
```

---

## Support

For issues or questions:
- Check logs: `docker-compose -f docker-compose.ollama.yml logs`
- Verify services: `docker-compose -f docker-compose.ollama.yml ps`
- Test endpoints: `curl http://localhost:8002/health`

---

## Summary

Your Yoda application with Ollama and Medgemma is now deployed and running on http://68.183.88.5:8002

The application uses:
- **Ollama** for local LLM inference (no OpenAI API needed)
- **Medgemma:4b** model for medical conversations
- **MongoDB** for session storage
- **Docker** for containerization

All services run locally on your server - no external API calls required!

