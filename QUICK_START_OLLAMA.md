# Quick Start Guide - Yoda with Ollama

## Single Command Deployment

SSH into your server and run:

```bash
ssh root@68.183.88.5 'bash -s' < <(curl -fsSL https://raw.githubusercontent.com/Tharun2302/yoda/main/deploy-ollama.sh)
```

Or manually:

```bash
# SSH into server
ssh root@68.183.88.5

# Run automated deployment
cd /opt
git clone https://github.com/Tharun2302/yoda.git
cd yoda
chmod +x deploy-ollama.sh
./deploy-ollama.sh
```

## Manual Step-by-Step Commands

### 1. Connect to Server
```bash
ssh root@68.183.88.5
```

### 2. Clean Previous Installations
```bash
# Stop existing containers
docker stop $(docker ps -aq) 2>/dev/null || true
docker rm $(docker ps -aq) 2>/dev/null || true

# Clean system
docker system prune -af --volumes
```

### 3. Install Docker
```bash
# Update system
apt-get update && apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
systemctl enable docker
systemctl start docker

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Verify
docker --version
docker-compose --version
```

### 4. Clone and Setup
```bash
# Clone repository
cd /opt
git clone https://github.com/Tharun2302/yoda.git
cd yoda

# Setup environment
cp env.ollama.template .env
```

### 5. Deploy with Docker Compose
```bash
# Build images
docker-compose -f docker-compose.ollama.yml build --no-cache

# Start services
docker-compose -f docker-compose.ollama.yml up -d

# Wait for services
sleep 30
```

### 6. Install Medgemma Model
```bash
# Pull the model into Ollama
docker exec yoda-ollama ollama pull alibayram/medgemma:4b

# Verify model is installed
docker exec yoda-ollama ollama list
```

### 7. Verify Deployment
```bash
# Check all services
docker-compose -f docker-compose.ollama.yml ps

# Test health
curl http://localhost:8002/health

# Test Ollama
curl http://localhost:11434/api/tags

# View logs
docker-compose -f docker-compose.ollama.yml logs
```

### 8. Access Application
- Main Application: http://68.183.88.5:8002
- Ollama API: http://68.183.88.5:11434

## Test Locally First

Before deploying to server, test on your local machine:

```bash
# Clone repo
git clone https://github.com/Tharun2302/yoda.git
cd yoda

# Setup environment
cp env.ollama.template .env
# Edit ALLOWED_ORIGINS to include localhost
nano .env

# Deploy locally
docker-compose -f docker-compose.ollama.yml up -d

# Pull model
sleep 30
docker exec yoda-ollama ollama pull alibayram/medgemma:4b

# Test
curl http://localhost:8002/health
open http://localhost:8002
```

## Common Commands

### View Logs
```bash
docker-compose -f docker-compose.ollama.yml logs -f
```

### Restart Services
```bash
docker-compose -f docker-compose.ollama.yml restart
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
docker-compose -f docker-compose.ollama.yml up -d --build
```

## Troubleshooting

### Ollama not working?
```bash
docker logs yoda-ollama
docker exec yoda-ollama ollama list
docker restart yoda-ollama
```

### App can't connect to Ollama?
```bash
docker exec yoda-chatbot curl http://ollama:11434/api/tags
```

### Model not responding?
```bash
# Re-pull the model
docker exec yoda-ollama ollama pull alibayram/medgemma:4b

# Test model directly
docker exec yoda-ollama ollama run alibayram/medgemma:4b "Hello"
```

## Architecture

```
User Browser
     ↓
http://68.183.88.5:8002 (Yoda App)
     ↓
Ollama (port 11434) → Medgemma Model
     ↓
MongoDB (port 27017) → Session Data
```

## Key Features

✅ **No OpenAI API Key Required** - Runs completely locally  
✅ **Medical-Specific Model** - Uses Medgemma for healthcare  
✅ **Persistent Storage** - MongoDB for session management  
✅ **Docker Deployment** - Easy scaling and management  
✅ **Works Locally & Remotely** - Same OLLAMA_API_KEY works everywhere  

## Files Created

- `app_ollama.py` - Ollama-compatible application
- `Dockerfile.ollama` - Docker build file
- `docker-compose.ollama.yml` - Multi-container setup
- `env.ollama.template` - Environment configuration
- `deploy-ollama.sh` - Automated deployment script

## Support

For detailed instructions, see: `DEPLOYMENT_GUIDE_OLLAMA.md`

