# HYoda Deployment Guide for Digital Ocean

This guide provides complete instructions for deploying the HYoda medical chatbot application to a Digital Ocean server using Docker.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Server Setup](#initial-server-setup)
3. [Quick Deployment](#quick-deployment)
4. [Manual Deployment](#manual-deployment)
5. [Configuration](#configuration)
6. [Post-Deployment](#post-deployment)
7. [Troubleshooting](#troubleshooting)
8. [Maintenance](#maintenance)

---

## Prerequisites

Before deploying, ensure you have:

- ✅ Digital Ocean account with a droplet created
- ✅ Server IP: `167.71.238.114`
- ✅ SSH access to the server
- ✅ OpenAI API key
- ✅ (Optional) Langfuse API keys for tracking
- ✅ (Optional) Domain name pointed to server IP

### Recommended Server Specs

- **OS**: Ubuntu 22.04 LTS or later
- **RAM**: 2GB minimum (4GB recommended)
- **CPU**: 2 vCPUs minimum
- **Storage**: 25GB minimum
- **Ports**: 80, 443, 8002 (open in firewall)

---

## Initial Server Setup

### 1. Connect to Your Server

```bash
ssh root@167.71.238.114
```

### 2. Update System Packages

```bash
apt update && apt upgrade -y
```

### 3. Install Required Tools

```bash
# Install git
apt install -y git curl nano

# Install Docker (automated)
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Verify installations
docker --version
docker-compose --version
```

### 4. Configure Firewall

```bash
# Install UFW firewall
apt install -y ufw

# Configure firewall rules
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8002/tcp

# Enable firewall
ufw enable
ufw status
```

---

## Quick Deployment

### 1. Clone/Upload Your Project

```bash
# Option A: Using git (if you have a repository)
git clone <your-repo-url> /opt/hyoda
cd /opt/hyoda

# Option B: Upload via SCP from your local machine
# Run this on YOUR LOCAL MACHINE:
scp -r HYoda root@167.71.238.114:/opt/hyoda
# Then SSH into server:
ssh root@167.71.238.114
cd /opt/hyoda
```

### 2. Configure Environment

```bash
# Copy environment template
cp env.template .env

# Edit the .env file
nano .env
```

**Required Configuration in `.env`:**

```bash
# MUST CONFIGURE:
OPENAI_API_KEY=sk-your-actual-openai-api-key-here

# Update if needed:
ALLOWED_ORIGINS=http://167.71.238.114:8002,http://167.71.238.114,http://localhost:8002
```

**Optional but Recommended:**

```bash
# Langfuse (for observability)
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_SECRET_KEY=sk-lf-xxx

# MongoDB (enabled by default in docker-compose)
MONGODB_URI=mongodb://mongodb:27017/
MONGODB_DB=healthyoda
```

Save and exit (Ctrl+X, Y, Enter)

### 3. Ensure Required Files Exist

```bash
# Check if Question BOOK.docx exists
ls -la docx/

# If missing, upload it:
# On your local machine:
# scp "HYoda/docx/Question BOOK.docx" root@167.71.238.114:/opt/hyoda/docx/
```

### 4. Run Deployment Script

```bash
# Make script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

That's it! Your application should now be running.

---

## Manual Deployment

If you prefer manual control or the script fails:

### 1. Build Docker Images

```bash
docker-compose build
```

### 2. Start Services

```bash
# Start all services
docker-compose up -d

# Or start specific services
docker-compose up -d hyoda-app mongodb nginx
```

### 3. Check Status

```bash
# View running containers
docker-compose ps

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f hyoda-app
```

---

## Configuration

### Environment Variables

All configuration is done via the `.env` file. Here are the key variables:

#### Required

- `OPENAI_API_KEY` - Your OpenAI API key (MUST be set)

#### Optional but Recommended

- `LANGFUSE_ENABLED` - Enable Langfuse tracking (true/false)
- `LANGFUSE_PUBLIC_KEY` - Langfuse public key
- `LANGFUSE_SECRET_KEY` - Langfuse secret key
- `MONGODB_URI` - MongoDB connection string
- `ALLOWED_ORIGINS` - CORS allowed origins (update with your domain)

#### Advanced

- `HEALTHBENCH_GRADER_MODEL` - Model for evaluation (default: gpt-4o-mini)
- `HELM_JUDGE_MODEL` - Model for HELM evaluation (default: gpt-4o-mini)
- `RATE_LIMIT_REQUESTS` - Max requests per window (default: 100)
- `RATE_LIMIT_WINDOW` - Rate limit window in seconds (default: 3600)
- `VOICE_ENABLED` - Enable voice features (default: false)

### Docker Compose Services

The stack includes three services:

1. **hyoda-app** - Flask application (Port 8002)
2. **mongodb** - Database for session storage (Port 27017)
3. **nginx** - Reverse proxy (Port 80/443)

To disable nginx and use Flask directly:

```bash
./deploy.sh --no-nginx
```

---

## Post-Deployment

### 1. Verify Deployment

```bash
# Check health endpoint
curl http://localhost:8002/health

# Or from outside
curl http://167.71.238.114/health
```

Expected response:
```json
{"status":"healthy"}
```

### 2. Access the Application

Open in your browser:

- **Chatbot Interface**: http://167.71.238.114/index.html
- **Evaluation Dashboard**: http://167.71.238.114/healthbench/dashboard
- **Landing Page**: http://167.71.238.114/

### 3. Test Basic Functionality

1. Go to the chatbot interface
2. Click "Start Conversation"
3. Try asking: "I have chest pain"
4. Verify the bot responds appropriately

### 4. Monitor Logs

```bash
# Follow all logs
docker-compose logs -f

# Follow only app logs
docker-compose logs -f hyoda-app

# View last 100 lines
docker-compose logs --tail=100 hyoda-app
```

---

## Troubleshooting

### Port Already in Use

If you see "port already in use" error:

```bash
# Find process using port 8002
sudo lsof -i :8002

# Kill the process
sudo kill -9 <PID>

# Or use different port in docker-compose.yml
```

### Cannot Connect to MongoDB

```bash
# Check if MongoDB is running
docker-compose ps

# Restart MongoDB
docker-compose restart mongodb

# Check MongoDB logs
docker-compose logs mongodb
```

### OpenAI API Errors

```bash
# Verify API key is set correctly
docker-compose exec hyoda-app env | grep OPENAI

# Update .env file and restart
nano .env
docker-compose restart hyoda-app
```

### Application Not Starting

```bash
# View detailed logs
docker-compose logs hyoda-app

# Check container status
docker-compose ps

# Restart all services
docker-compose down
docker-compose up -d
```

### CORS Errors

Update `ALLOWED_ORIGINS` in `.env`:

```bash
ALLOWED_ORIGINS=http://167.71.238.114,http://167.71.238.114:8002,http://yourdomain.com
```

Then restart:

```bash
docker-compose restart hyoda-app
```

### Rebuild from Scratch

```bash
# Stop and remove everything
docker-compose down -v

# Rebuild and restart
./deploy.sh --build
```

---

## Maintenance

### Viewing Logs

```bash
# Real-time logs (all services)
docker-compose logs -f

# Last 100 lines from app
docker-compose logs --tail=100 hyoda-app

# Export logs to file
docker-compose logs hyoda-app > app.log
```

### Updating the Application

```bash
# Pull latest code (if using git)
cd /opt/hyoda
git pull

# Rebuild and restart
./deploy.sh --build
```

### Backup MongoDB Data

```bash
# Create backup
docker-compose exec mongodb mongodump --out=/data/backup

# Copy to host
docker cp hyoda-mongodb:/data/backup ./mongodb-backup-$(date +%Y%m%d)
```

### Restore MongoDB Data

```bash
# Copy backup to container
docker cp ./mongodb-backup hyoda-mongodb:/data/backup

# Restore
docker-compose exec mongodb mongorestore /data/backup
```

### Updating Environment Variables

```bash
# Edit .env
nano .env

# Restart services to apply changes
docker-compose restart
```

### Checking Resource Usage

```bash
# Container stats
docker stats

# Disk usage
docker system df

# Clean up unused images
docker system prune -a
```

### SSL/HTTPS Setup (Optional)

For production, you should use HTTPS:

```bash
# Install certbot
apt install -y certbot

# Get SSL certificate (requires domain name)
certbot certonly --standalone -d yourdomain.com

# Copy certificates
mkdir -p /opt/hyoda/ssl
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem /opt/hyoda/ssl/cert.pem
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem /opt/hyoda/ssl/key.pem

# Update nginx.conf to enable HTTPS section
nano nginx.conf

# Restart nginx
docker-compose restart nginx
```

---

## Common Commands Reference

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View logs
docker-compose logs -f

# Rebuild and restart
docker-compose up -d --build

# Access app shell
docker-compose exec hyoda-app bash

# Access MongoDB shell
docker-compose exec mongodb mongosh

# Check service status
docker-compose ps

# Remove everything (including volumes)
docker-compose down -v
```

---

## Support

For issues or questions:

1. Check logs: `docker-compose logs -f hyoda-app`
2. Verify configuration in `.env` file
3. Ensure all required files exist (especially `docx/Question BOOK.docx`)
4. Check firewall settings: `ufw status`
5. Verify Docker is running: `docker ps`

---

## Security Best Practices

1. ✅ Keep `.env` file secure (never commit to git)
2. ✅ Use strong passwords for MongoDB
3. ✅ Enable firewall (UFW)
4. ✅ Use HTTPS in production
5. ✅ Regularly update Docker images
6. ✅ Monitor logs for suspicious activity
7. ✅ Set up automated backups
8. ✅ Use non-root user for deployment (create dedicated user)

---

**Deployment Status**: Ready for Production ✅
**Last Updated**: 2024
**Maintained By**: HYoda Team

