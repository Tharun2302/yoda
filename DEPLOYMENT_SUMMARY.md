# 🚀 HYoda Deployment Summary

## ✅ All Deployment Files Ready

Your project is now **deployment-ready** for Digital Ocean! Here's what has been added:

### 📁 New Files Created

1. **`Dockerfile`** - Container image definition for the Flask app
2. **`docker-compose.yml`** - Multi-container orchestration (app + MongoDB + nginx)
3. **`.dockerignore`** - Excludes unnecessary files from Docker image
4. **`env.template`** - Environment variables template
5. **`nginx.conf`** - Nginx reverse proxy configuration
6. **`deploy.sh`** - Automated deployment script
7. **`DEPLOYMENT.md`** - Comprehensive deployment guide
8. **`QUICK_DEPLOY.md`** - Quick start commands
9. **`.gitignore`** - Git ignore file for cleaner repository

### 🔧 Modified Files

1. **`app.py`** - Updated to bind to `0.0.0.0` for Docker compatibility

---

## 🎯 Complete Deployment Commands

### Step 1: Upload Files to Digital Ocean

**From Windows (PowerShell):**

```powershell
# Navigate to your project directory
cd "C:\Users\TharunP\OneDrive - CloudFuze, Inc\Desktop\Evals"

# Upload to Digital Ocean server
scp -r HYoda root@167.71.238.114:/opt/hyoda
```

**Or use an FTP client like:**
- WinSCP
- FileZilla
- Upload to: `/opt/hyoda`

### Step 2: SSH into Your Server

```powershell
ssh root@167.71.238.114
```

### Step 3: Install Docker (One-Time Setup)

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### Step 4: Configure Environment

```bash
# Navigate to project
cd /opt/hyoda

# Create .env file from template
cp env.template .env

# Edit the .env file
nano .env
```

**Add your OpenAI API key:**
```bash
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
```

Save with `Ctrl+X`, then `Y`, then `Enter`

### Step 5: Setup Firewall

```bash
# Install and configure firewall
apt install -y ufw
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8002/tcp
ufw enable
```

### Step 6: Deploy!

```bash
# Make deploy script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

---

## 🌐 Access Your Application

After successful deployment:

| Service | URL |
|---------|-----|
| **Landing Page** | http://167.71.238.114/ |
| **Chatbot** | http://167.71.238.114/index.html |
| **Dashboard** | http://167.71.238.114/healthbench/dashboard |
| **Health Check** | http://167.71.238.114/health |
| **Direct Access** | http://167.71.238.114:8002 |

---

## 📊 Architecture Overview

```
Internet
   ↓
Nginx (Port 80) → Rate limiting, SSL termination, caching
   ↓
Flask App (Port 8002) → Main application
   ↓
MongoDB (Port 27017) → Session storage
```

---

## 🔍 Verify Deployment

```bash
# 1. Check if containers are running
docker-compose ps

# Expected output:
# NAME                COMMAND             STATUS    PORTS
# hyoda-chatbot       "python app.py"     Up        0.0.0.0:8002->8002/tcp
# hyoda-mongodb       "docker-entrypoint…" Up        27017/tcp
# hyoda-nginx         "/docker-entrypoint…" Up        0.0.0.0:80->80/tcp

# 2. Check health endpoint
curl http://localhost:8002/health

# Expected output:
# {"status":"healthy"}

# 3. View logs
docker-compose logs -f
```

---

## 🛠️ Essential Management Commands

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Just the app
docker-compose logs -f hyoda-app

# Last 100 lines
docker-compose logs --tail=100 hyoda-app
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart just app
docker-compose restart hyoda-app

# Stop all
docker-compose down

# Start all
docker-compose up -d
```

### Update Application

```bash
# After uploading new code
cd /opt/hyoda
./deploy.sh --build
```

### Clean Restart

```bash
# Complete clean restart (removes volumes)
docker-compose down -v
./deploy.sh --build
```

---

## 🐛 Troubleshooting

### Issue: Port Already in Use

**Solution:**
```bash
# Find what's using port 8002
lsof -i :8002

# Kill the process
kill -9 <PID>

# Or just stop existing containers
docker-compose down
./deploy.sh
```

### Issue: Cannot Connect Externally

**Solution:**
```bash
# Check firewall
ufw status

# Open required ports
ufw allow 80/tcp
ufw allow 8002/tcp

# Check if service is listening
netstat -tlnp | grep 8002
```

### Issue: MongoDB Connection Failed

**Solution:**
```bash
# Check MongoDB status
docker-compose ps

# Restart MongoDB
docker-compose restart mongodb

# Check logs
docker-compose logs mongodb
```

### Issue: OpenAI API Errors

**Solution:**
```bash
# Verify API key is set
docker-compose exec hyoda-app env | grep OPENAI

# Update .env and restart
nano .env
docker-compose restart hyoda-app
```

### Issue: Build Fails

**Solution:**
```bash
# Clean build
docker system prune -a
./deploy.sh --build
```

---

## 📋 Pre-Deployment Checklist

Before deploying, ensure:

- [ ] ✅ `.env` file created with valid `OPENAI_API_KEY`
- [ ] ✅ `docx/Question BOOK.docx` file exists
- [ ] ✅ Server has at least 2GB RAM
- [ ] ✅ Ports 80, 443, 8002 are open in firewall
- [ ] ✅ Docker and Docker Compose installed
- [ ] ✅ SSH access to server working

---

## 🔒 Security Considerations

### Production Recommendations:

1. **Use HTTPS** - Setup SSL certificate with Let's Encrypt
2. **Change default ports** - Move away from 8002 if needed
3. **Enable authentication** - Add user authentication layer
4. **Setup monitoring** - Use tools like Grafana, Prometheus
5. **Regular backups** - Backup MongoDB data regularly
6. **Update regularly** - Keep Docker images updated
7. **Use secrets management** - Consider HashiCorp Vault for production

### Basic Security Setup:

```bash
# 1. Create non-root user
adduser deploy
usermod -aG docker deploy
usermod -aG sudo deploy

# 2. Setup SSH key authentication
# (On your local machine)
ssh-copy-id deploy@167.71.238.114

# 3. Disable root SSH login
nano /etc/ssh/sshd_config
# Set: PermitRootLogin no
systemctl restart ssh

# 4. Setup automated security updates
apt install -y unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades
```

---

## 📈 Monitoring

### View Resource Usage

```bash
# Container stats
docker stats

# Disk usage
df -h

# Memory usage
free -h

# CPU usage
top
```

### Application Logs

```bash
# Real-time logs with timestamps
docker-compose logs -f --timestamps hyoda-app

# Export logs to file
docker-compose logs hyoda-app > app-logs-$(date +%Y%m%d).log
```

---

## 🔄 Backup and Restore

### Backup MongoDB

```bash
# Create backup
docker-compose exec mongodb mongodump --out=/data/backup

# Copy to host
docker cp hyoda-mongodb:/data/backup ./backup-$(date +%Y%m%d)

# Download to local machine (run on local)
scp -r root@167.71.238.114:/opt/hyoda/backup-* ./
```

### Restore MongoDB

```bash
# Upload backup to server
scp -r ./backup-* root@167.71.238.114:/opt/hyoda/

# Copy to container
docker cp ./backup-* hyoda-mongodb:/data/backup

# Restore
docker-compose exec mongodb mongorestore /data/backup
```

---

## 📞 Support

If you encounter issues:

1. **Check logs**: `docker-compose logs -f hyoda-app`
2. **Verify configuration**: `cat .env`
3. **Check service status**: `docker-compose ps`
4. **Test connectivity**: `curl http://localhost:8002/health`
5. **Review deployment guide**: `DEPLOYMENT.md`

---

## 🎉 Success!

Your HYoda medical chatbot is now deployed and ready for use!

**Next Steps:**
1. Test the chatbot at http://167.71.238.114/index.html
2. Check the dashboard at http://167.71.238.114/healthbench/dashboard
3. Monitor logs: `docker-compose logs -f`
4. Consider setting up HTTPS for production use

**Useful Links:**
- [Full Deployment Guide](DEPLOYMENT.md)
- [Quick Commands](QUICK_DEPLOY.md)
- Docker Compose: https://docs.docker.com/compose/
- Digital Ocean: https://docs.digitalocean.com/

---

**Status**: ✅ DEPLOYMENT READY
**Version**: 1.0
**Last Updated**: 2024

