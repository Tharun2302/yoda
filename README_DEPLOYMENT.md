# 🚀 HYoda Docker Deployment - Complete Package

## 📦 What's Included

Your HYoda project is now **100% ready for Docker deployment** to Digital Ocean! All necessary files have been created and configured.

### ✅ Deployment Files Created

| File | Purpose |
|------|---------|
| `Dockerfile` | Builds the application container image |
| `docker-compose.yml` | Orchestrates app + MongoDB + nginx |
| `.dockerignore` | Optimizes Docker build process |
| `nginx.conf` | Reverse proxy configuration |
| `env.template` | Environment variables template |
| `deploy.sh` | Automated deployment script |
| `.gitignore` | Git ignore patterns |

### 📚 Documentation Created

| Document | Description |
|----------|-------------|
| `DEPLOYMENT.md` | Comprehensive deployment guide |
| `DEPLOYMENT_SUMMARY.md` | Quick reference with all commands |
| `QUICK_DEPLOY.md` | Minimal steps to get running |
| `WINDOWS_UPLOAD_GUIDE.md` | Windows-specific upload instructions |
| `README_DEPLOYMENT.md` | This file - overview |

### 🔧 Code Modifications

- ✅ `app.py` - Updated to bind to `0.0.0.0` for Docker compatibility
- ✅ All imports and dependencies verified

---

## 🎯 Quick Start - 3 Steps to Deploy

### Step 1️⃣: Upload to Server (Windows)

**Option A - Using PowerShell:**
```powershell
cd "C:\Users\TharunP\OneDrive - CloudFuze, Inc\Desktop\Evals"
scp -r HYoda root@167.71.238.114:/opt/hyoda
```

**Option B - Using WinSCP (Recommended for beginners):**
1. Download WinSCP: https://winscp.net/
2. Connect to `167.71.238.114` as `root`
3. Drag-drop `HYoda` folder to `/opt/`

### Step 2️⃣: Configure on Server

```bash
# SSH into server
ssh root@167.71.238.114

# Navigate to project
cd /opt/hyoda

# Install Docker & Docker Compose (first time only)
curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create environment file
cp env.template .env
nano .env
# Add: OPENAI_API_KEY=sk-your-key-here
# Save: Ctrl+X, Y, Enter
```

### Step 3️⃣: Deploy!

```bash
chmod +x deploy.sh
./deploy.sh
```

**That's it!** 🎉

---

## 🌐 Access Your Application

After successful deployment:

| What | URL |
|------|-----|
| 🏠 **Home Page** | http://167.71.238.114/ |
| 💬 **Chatbot** | http://167.71.238.114/index.html |
| 📊 **Dashboard** | http://167.71.238.114/healthbench/dashboard |
| ❤️ **Health Check** | http://167.71.238.114/health |

---

## 🔍 Verification Commands

After deployment, verify everything is working:

```bash
# Check containers are running
docker-compose ps

# Test health endpoint
curl http://localhost:8002/health

# View logs
docker-compose logs -f hyoda-app

# Check MongoDB
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"
```

---

## 📋 Complete Command Reference

### 🚀 Deployment Commands

```bash
# Initial deployment
./deploy.sh

# Force rebuild
./deploy.sh --build

# Deploy without nginx (direct Flask access)
./deploy.sh --no-nginx
```

### 📊 Monitoring Commands

```bash
# View all logs
docker-compose logs -f

# View app logs only
docker-compose logs -f hyoda-app

# View last 100 lines
docker-compose logs --tail=100 hyoda-app

# Container resource usage
docker stats

# Service status
docker-compose ps
```

### 🔄 Management Commands

```bash
# Restart all services
docker-compose restart

# Restart app only
docker-compose restart hyoda-app

# Stop all services
docker-compose down

# Start services
docker-compose up -d

# Complete clean restart
docker-compose down -v
./deploy.sh --build
```

### 🐛 Debugging Commands

```bash
# Check environment variables
docker-compose exec hyoda-app env | grep OPENAI

# Access app shell
docker-compose exec hyoda-app bash

# Access MongoDB shell
docker-compose exec mongodb mongosh

# Check network connectivity
docker-compose exec hyoda-app ping mongodb

# View nginx logs
docker-compose logs nginx
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│           Internet (Port 80)            │
└───────────────┬─────────────────────────┘
                │
        ┌───────▼────────┐
        │  Nginx Proxy   │  ← Rate limiting, SSL, Caching
        │  (Container)   │
        └───────┬────────┘
                │
        ┌───────▼────────┐
        │  Flask App     │  ← Main HYoda Application
        │  (Port 8002)   │
        └───────┬────────┘
                │
        ┌───────▼────────┐
        │   MongoDB      │  ← Session Storage
        │  (Port 27017)  │
        └────────────────┘

Docker Network: hyoda-network
Volumes: mongodb_data, chroma_db/, docx/
```

---

## ⚙️ Configuration Options

All configuration is in the `.env` file:

### 🔴 Required Settings

```bash
OPENAI_API_KEY=sk-your-actual-key-here  # MUST HAVE!
```

### 🟡 Recommended Settings

```bash
# Langfuse Tracking (Optional but useful)
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_SECRET_KEY=sk-lf-xxx
LANGFUSE_HOST=https://cloud.langfuse.com

# CORS (Update with your domain)
ALLOWED_ORIGINS=http://167.71.238.114,http://yourdomain.com
```

### 🟢 Optional Settings

```bash
# MongoDB
MONGODB_URI=mongodb://mongodb:27017/
MONGODB_DB=healthyoda

# Models
HEALTHBENCH_GRADER_MODEL=gpt-4o-mini
HELM_JUDGE_MODEL=gpt-4o-mini

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600

# Voice (experimental)
VOICE_ENABLED=false
```

---

## 🛡️ Security Checklist

Before going to production:

- [ ] ✅ Change default passwords
- [ ] ✅ Enable firewall (UFW)
- [ ] ✅ Setup SSL/HTTPS with Let's Encrypt
- [ ] ✅ Use environment-specific `.env` files
- [ ] ✅ Never commit `.env` to git
- [ ] ✅ Regular backups of MongoDB
- [ ] ✅ Monitor logs for suspicious activity
- [ ] ✅ Keep Docker images updated
- [ ] ✅ Use non-root user for deployment
- [ ] ✅ Setup automated security updates

### Quick Security Setup

```bash
# Firewall
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# Create non-root user
adduser deploy
usermod -aG docker deploy
usermod -aG sudo deploy

# SSH key authentication (from your local machine)
ssh-copy-id deploy@167.71.238.114
```

---

## 🐛 Common Issues & Solutions

### ❌ Port 8002 Already in Use

```bash
# Solution 1: Stop existing process
docker-compose down
./deploy.sh

# Solution 2: Kill process on port
lsof -i :8002
kill -9 <PID>
```

### ❌ Cannot Connect to MongoDB

```bash
# Check MongoDB status
docker-compose logs mongodb

# Restart MongoDB
docker-compose restart mongodb

# Verify network
docker network inspect hyoda-network
```

### ❌ OpenAI API Key Not Working

```bash
# Verify key is set correctly
docker-compose exec hyoda-app env | grep OPENAI

# Update .env and restart
nano .env
docker-compose restart hyoda-app
```

### ❌ Nginx Not Starting

```bash
# Check nginx logs
docker-compose logs nginx

# Test nginx config
docker-compose exec nginx nginx -t

# Common fix: Port 80 conflict
lsof -i :80
# Stop conflicting service or use different port
```

### ❌ Build Fails

```bash
# Clean Docker system
docker system prune -a

# Rebuild from scratch
docker-compose down -v
./deploy.sh --build
```

---

## 📦 What Gets Deployed

### Docker Images

1. **hyoda-app** (~500MB)
   - Base: Python 3.11-slim
   - Includes: Flask, OpenAI SDK, MongoDB driver, ChromaDB, etc.

2. **MongoDB** (~600MB)
   - Version: 7.0
   - Data persisted in volume

3. **Nginx** (~25MB)
   - Alpine-based
   - Reverse proxy + SSL termination

### Volumes

- `mongodb_data` - MongoDB database files
- `./chroma_db` - Vector database (mounted)
- `./docx` - Question book (mounted)

### Network

- `hyoda-network` - Bridge network for inter-container communication

---

## 🔄 Backup & Restore

### Backup MongoDB

```bash
# Create backup
docker-compose exec mongodb mongodump --out=/data/backup
docker cp hyoda-mongodb:/data/backup ./backup-$(date +%Y%m%d)

# Download to local (run on Windows)
scp -r root@167.71.238.114:/opt/hyoda/backup-* ./
```

### Restore MongoDB

```bash
# Upload backup to server
scp -r ./backup-* root@167.71.238.114:/opt/hyoda/

# Restore
docker cp ./backup-* hyoda-mongodb:/data/backup
docker-compose exec mongodb mongorestore /data/backup
```

---

## 📈 Monitoring & Maintenance

### View Metrics

```bash
# Real-time container stats
docker stats

# Disk usage
docker system df

# Service health
docker-compose ps
```

### Log Management

```bash
# Rotate logs
docker-compose logs --tail=1000 hyoda-app > archived-logs-$(date +%Y%m%d).log

# Clean old logs
docker-compose down
docker system prune -f
docker-compose up -d
```

### Updates

```bash
# Pull latest code (if using git)
git pull

# Rebuild and deploy
./deploy.sh --build

# Or manually
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## 📚 Additional Resources

### Documentation Files

- **DEPLOYMENT.md** - Full deployment guide with detailed explanations
- **QUICK_DEPLOY.md** - Minimal command reference
- **WINDOWS_UPLOAD_GUIDE.md** - Windows-specific upload methods
- **DEPLOYMENT_SUMMARY.md** - Complete command reference

### External Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Digital Ocean Guides](https://docs.digitalocean.com/)
- [Flask Deployment Guide](https://flask.palletsprojects.com/en/stable/deploying/)
- [Nginx Documentation](https://nginx.org/en/docs/)

---

## ✅ Deployment Checklist

Before deploying:

- [x] ✅ Dockerfile created
- [x] ✅ docker-compose.yml configured
- [x] ✅ nginx.conf configured
- [x] ✅ env.template created
- [x] ✅ deploy.sh script ready
- [x] ✅ Documentation complete
- [x] ✅ app.py updated for Docker

To do before first deployment:

- [ ] Upload files to server
- [ ] Create `.env` with OPENAI_API_KEY
- [ ] Ensure `docx/Question BOOK.docx` exists
- [ ] Configure firewall
- [ ] Run deploy.sh
- [ ] Test application
- [ ] Setup monitoring
- [ ] Configure backups
- [ ] (Optional) Setup SSL/HTTPS

---

## 🎉 Success Indicators

After running `./deploy.sh`, you should see:

```
✓ Environment file found
✓ Prerequisites checked
✓ Docker images built
✓ All services started

╔════════════════════════════════════════════╗
║         Deployment Completed! 🎉           ║
╚════════════════════════════════════════════╝

Application is running at:
  • http://167.71.238.114
  • http://167.71.238.114:8002
```

### Verify Success

```bash
# 1. All containers running
docker-compose ps | grep "Up"

# 2. Health check passes
curl http://localhost:8002/health
# Should return: {"status":"healthy"}

# 3. No errors in logs
docker-compose logs --tail=50 | grep ERROR
# Should have no critical errors

# 4. MongoDB connected
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"
# Should return: { ok: 1 }
```

---

## 📞 Support & Help

If you encounter issues:

1. **Check the logs**: `docker-compose logs -f hyoda-app`
2. **Verify configuration**: `cat .env`
3. **Test connectivity**: `curl http://localhost:8002/health`
4. **Review documentation**: Check DEPLOYMENT.md for detailed troubleshooting
5. **Clean restart**: `docker-compose down -v && ./deploy.sh --build`

---

## 🚀 Next Steps After Deployment

1. ✅ **Test the chatbot** - Go to http://167.71.238.114/index.html
2. ✅ **Check the dashboard** - Go to http://167.71.238.114/healthbench/dashboard
3. ✅ **Monitor logs** - Run `docker-compose logs -f`
4. ✅ **Setup SSL** - Use Let's Encrypt for HTTPS
5. ✅ **Configure backups** - Setup automated MongoDB backups
6. ✅ **Add monitoring** - Consider Grafana/Prometheus
7. ✅ **Document credentials** - Store API keys securely
8. ✅ **Test disaster recovery** - Practice restore procedures

---

**🎯 Your HYoda project is deployment-ready!**

**Status**: ✅ Production Ready  
**Version**: 1.0  
**Server IP**: 167.71.238.114  
**Deployment Method**: Docker Compose  
**Last Updated**: November 2024

---

*For detailed deployment instructions, see `DEPLOYMENT.md`*  
*For quick commands, see `QUICK_DEPLOY.md`*  
*For Windows upload help, see `WINDOWS_UPLOAD_GUIDE.md`*

