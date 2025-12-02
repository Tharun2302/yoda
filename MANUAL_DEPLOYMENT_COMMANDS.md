# 🚀 Manual Deployment Commands for Server 68.183.88.5

**Branch**: SUditya  
**Repository**: https://github.com/Tharun2302/yoda.git  
**Server IP**: 68.183.88.5

---

## 📋 COMPLETE STEP-BY-STEP COMMANDS

Copy and paste these commands one by one into your server terminal.

---

### 🔐 STEP 1: SSH INTO SERVER

```bash
ssh root@68.183.88.5
# OR
ssh your-username@68.183.88.5
```

---

### 🧹 STEP 2: CLEAN EXISTING DEPLOYMENT

```bash
# Stop existing Docker containers
cd /opt/yoda 2>/dev/null || cd ~
docker-compose down -v 2>/dev/null || true
docker compose down -v 2>/dev/null || true

# Remove all hyoda/yoda containers
docker ps -a | grep -E "hyoda|yoda" | awk '{print $1}' | xargs docker rm -f 2>/dev/null || true

# Remove old deployment directory
sudo rm -rf /opt/yoda

# Clean Docker system (removes unused containers, images, volumes)
docker system prune -f --volumes

echo "✓ Server cleaned successfully"
```

---

### 📦 STEP 3: INSTALL PREREQUISITES

```bash
# Update system
sudo apt update -y

# Install Docker (if not installed)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
rm get-docker.sh

# Install Docker Compose (if not installed)
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installations
docker --version
docker-compose --version

echo "✓ Prerequisites installed"
```

**Note**: If you installed Docker for the first time, you may need to log out and log back in, or run:
```bash
newgrp docker
```

---

### 📥 STEP 4: CLONE SUditya BRANCH FROM GITHUB

```bash
# Create deployment directory
sudo mkdir -p /opt/yoda
sudo chown -R $USER:$USER /opt/yoda
cd /opt/yoda

# Clone ONLY the SUditya branch
git clone -b SUditya --single-branch https://github.com/Tharun2302/yoda.git .

# Verify branch
git branch
# Should show: * SUditya

echo "✓ SUditya branch cloned successfully"
```

---

### ⚙️ STEP 5: CONFIGURE ENVIRONMENT

```bash
# Copy environment template
cp env.template .env

# Edit .env file and add your OpenAI API key
nano .env
```

**In nano editor:**
1. Find line: `OPENAI_API_KEY=your-openai-api-key-here`
2. Replace with: `OPENAI_API_KEY=sk-your-actual-key-here`
3. (Optional) Enable Langfuse if needed
4. Press `Ctrl+X`, then `Y`, then `Enter` to save

**Alternative - One-line command to set API key:**
```bash
# Replace YOUR_ACTUAL_KEY with your real OpenAI API key
sed -i 's/OPENAI_API_KEY=your-openai-api-key-here/OPENAI_API_KEY=YOUR_ACTUAL_KEY/' .env

# Verify
grep OPENAI_API_KEY .env

# Set proper permissions
chmod 600 .env

echo "✓ Environment configured"
```

---

### 🔒 STEP 6: GENERATE SSL CERTIFICATES

```bash
# Make script executable
chmod +x generate_ssl_cert.sh

# Generate SSL certificates for IP 68.183.88.5
./generate_ssl_cert.sh

# Verify certificates were created
ls -lh ssl/
# Should show: cert.pem and key.pem

echo "✓ SSL certificates generated"
```

---

### 🐳 STEP 7: DEPLOY WITH DOCKER

```bash
# Make deploy script executable
chmod +x deploy.sh

# Deploy all services (app + mongodb + nginx)
./deploy.sh

# This will:
# 1. Build Docker images
# 2. Start all containers
# 3. Set up networking
# 4. Configure SSL
```

**Alternative - Manual Docker Compose:**
```bash
# Build and start containers
docker-compose up -d --build

# View progress
docker-compose logs -f
```

---

### ✅ STEP 8: VERIFY DEPLOYMENT

```bash
# Wait for services to start (30-60 seconds)
sleep 30

# Check service status
docker-compose ps
# All 3 services should show "Up (healthy)"

# Test health endpoint
curl http://localhost:8002/health
# Should return: {"status":"healthy"}

# View logs
docker-compose logs hyoda-app | tail -50

# Check for these success messages:
# ✅ "Server running on port 8002"
# ✅ "RAG system initialized"
# ✅ "HealthBench evaluation modules loaded"
```

---

## 🌐 ACCESS YOUR APPLICATION

After successful deployment, access your chatbot at:

### Primary URLs:
- **HTTPS** (Recommended): https://68.183.88.5
- **HTTP**: http://68.183.88.5:8002
- **Dashboard**: https://68.183.88.5/healthbench/dashboard

### First Time HTTPS Access:
1. Browser will show "Your connection is not private" warning
2. Click **"Advanced"**
3. Click **"Proceed to 68.183.88.5 (unsafe)"**
4. This is normal for self-signed certificates

---

## 🛠️ USEFUL COMMANDS

### View Logs
```bash
# All services
docker-compose logs -f

# Just the app
docker-compose logs -f hyoda-app

# Just MongoDB
docker-compose logs -f mongodb

# Just nginx
docker-compose logs -f nginx

# Last 100 lines
docker-compose logs --tail=100 hyoda-app
```

### Service Management
```bash
# Check service status
docker-compose ps

# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart hyoda-app

# Stop all services
docker-compose down

# Start all services
docker-compose up -d

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

### System Monitoring
```bash
# Check resource usage
docker stats

# Check disk space
df -h

# Check running containers
docker ps

# Check Docker logs
docker-compose logs --tail=50
```

---

## 🔧 TROUBLESHOOTING

### If Services Don't Start

```bash
# Check logs for errors
docker-compose logs hyoda-app

# Check if ports are available
sudo lsof -i :80
sudo lsof -i :443
sudo lsof -i :8002

# Restart services
docker-compose restart

# Full rebuild (if needed)
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### If Health Check Fails

```bash
# Check if app is running
docker-compose ps hyoda-app

# View detailed logs
docker-compose logs hyoda-app | tail -100

# Check OpenAI API key
docker-compose exec hyoda-app env | grep OPENAI_API_KEY

# Restart app
docker-compose restart hyoda-app
```

### If Can't Access via Browser

```bash
# Check nginx is running
docker-compose ps nginx

# Check nginx logs
docker-compose logs nginx

# Test direct backend access
curl http://localhost:8002/health

# Check firewall
sudo ufw status
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8002/tcp
```

### Complete Reset (Last Resort)

```bash
# ⚠️ WARNING: This deletes all data!
cd /opt/yoda
docker-compose down -v
docker system prune -af --volumes
docker-compose up -d --build
```

---

## 📊 VERIFICATION CHECKLIST

After deployment, verify:

- [ ] `docker-compose ps` shows all 3 services as "Up (healthy)"
- [ ] `curl http://localhost:8002/health` returns `{"status":"healthy"}`
- [ ] Can access `https://68.183.88.5` in browser
- [ ] Chatbot interface loads correctly
- [ ] Can send messages and get AI responses
- [ ] Dashboard accessible at `https://68.183.88.5/healthbench/dashboard`
- [ ] No critical errors in logs: `docker-compose logs hyoda-app`

---

## 🔐 SECURITY RECOMMENDATIONS

```bash
# Configure firewall (Ubuntu/Debian)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# Secure .env file
chmod 600 /opt/yoda/.env

# Set up automatic security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## 📝 UPDATE PROCEDURE

To update your deployment:

```bash
cd /opt/yoda

# Pull latest changes from SUditya branch
git pull origin SUditya

# Rebuild and restart
docker-compose down
docker-compose up -d --build

# Verify
docker-compose ps
curl http://localhost:8002/health
```

---

## 🆘 NEED HELP?

1. **Check logs first**: `docker-compose logs -f hyoda-app`
2. **Verify services**: `docker-compose ps`
3. **Test health**: `curl http://localhost:8002/health`
4. **Read documentation**: `/opt/yoda/README.md`
5. **Check checklist**: `/opt/yoda/DEPLOYMENT_CHECKLIST.md`

---

## 📞 QUICK REFERENCE

| Command | Purpose |
|---------|---------|
| `cd /opt/yoda` | Go to deployment directory |
| `docker-compose ps` | Check service status |
| `docker-compose logs -f` | View live logs |
| `docker-compose restart` | Restart all services |
| `docker-compose down` | Stop all services |
| `docker-compose up -d` | Start all services |
| `curl http://localhost:8002/health` | Test health |
| `git pull origin SUditya` | Update code |

---

**Deployment completed!** 🎉

Your HealthYoda AI chatbot is now live at: **https://68.183.88.5**

