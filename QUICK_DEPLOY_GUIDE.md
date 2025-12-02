# ⚡ Quick Deployment Guide - HealthYoda

**5-Minute Deployment to Production Server**

## 🚀 Prerequisites

- Linux server with SSH access
- OpenAI API key
- 15 minutes of your time

## 📦 One-Line Deployment

```bash
curl -fsSL https://raw.githubusercontent.com/Tharun2302/yoda/SUditya/deploy.sh | bash
```

*Note: This requires .env to be configured first. See below for full manual steps.*

## 🔧 Step-by-Step (Recommended)

### 1️⃣ Connect to Your Server

```bash
ssh user@your-server-ip
cd /opt
```

### 2️⃣ Clone Repository

```bash
git clone -b SUditya https://github.com/Tharun2302/yoda.git
cd yoda
```

### 3️⃣ Configure Environment

```bash
# Copy template
cp env.template .env

# Edit configuration
nano .env
```

**Minimum Required Configuration:**
```env
OPENAI_API_KEY=sk-your-actual-openai-key-here
```

**Update Server IP (if different from 167.71.238.114):**
```env
ALLOWED_ORIGINS=https://YOUR_SERVER_IP,http://YOUR_SERVER_IP:8002
```

Save and exit (Ctrl+X, Y, Enter)

### 4️⃣ Generate SSL Certificates

```bash
./generate_ssl_cert.sh
```

### 5️⃣ Deploy!

```bash
./deploy.sh
```

Wait 2-3 minutes for services to start...

### 6️⃣ Test Deployment

```bash
# Check health
curl http://localhost:8002/health

# Check services
docker-compose ps
```

Expected output:
```
NAME                COMMAND                  SERVICE      STATUS         PORTS
hyoda-chatbot       "python app.py"          hyoda-app    Up (healthy)   0.0.0.0:8002->8002/tcp
hyoda-mongodb       "docker-entrypoint.s…"   mongodb      Up (healthy)   0.0.0.0:27017->27017/tcp
hyoda-nginx         "/docker-entrypoint.…"   nginx        Up (healthy)   0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
```

### 7️⃣ Access Your Chatbot

Open browser and go to:
- **HTTPS**: `https://your-server-ip` ✅ Recommended
- **HTTP**: `http://your-server-ip:8002`

**First time HTTPS access:** Click "Advanced" → "Proceed to site" (self-signed cert warning)

---

## 🔍 Verify Deployment

### Test Chat Functionality

1. Open `https://your-server-ip`
2. Type: "What is diabetes?"
3. Should get streaming AI response

### Check Dashboard

1. Go to: `https://your-server-ip/healthbench/dashboard`
2. Dashboard should load successfully

### View Logs

```bash
docker-compose logs -f hyoda-app
```

Look for:
- ✅ `Server running on port 8002`
- ✅ `RAG system initialized`
- ✅ `HealthBench evaluation modules loaded`

---

## 🛠️ Common Issues & Fixes

### Issue: Port Already in Use

```bash
# Check what's using the port
sudo lsof -i :8002
sudo lsof -i :80

# Stop conflicting service
sudo systemctl stop <service-name>

# Or use different ports in docker-compose.yml
```

### Issue: OpenAI API Key Not Working

```bash
# Verify key in .env
cat .env | grep OPENAI_API_KEY

# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer sk-your-key"

# If invalid, update .env and restart
nano .env
docker-compose restart hyoda-app
```

### Issue: Services Not Starting

```bash
# Check logs
docker-compose logs hyoda-app

# Common fixes:
docker-compose down
docker-compose up -d

# Nuclear option (rebuilds everything)
./deploy.sh --build
```

### Issue: SSL Certificate Error

```bash
# Regenerate certificates
rm -rf ssl/*
./generate_ssl_cert.sh

# Restart nginx
docker-compose restart nginx
```

### Issue: MongoDB Connection Failed

```bash
# Check MongoDB is running
docker-compose ps mongodb

# Restart MongoDB
docker-compose restart mongodb

# View MongoDB logs
docker-compose logs mongodb
```

---

## 📊 Useful Commands

### Service Management

```bash
# View all services
docker-compose ps

# Restart specific service
docker-compose restart hyoda-app

# Stop all services
docker-compose down

# Start all services
docker-compose up -d

# Force rebuild
./deploy.sh --build
```

### Logs

```bash
# All logs (follow mode)
docker-compose logs -f

# Specific service
docker-compose logs -f hyoda-app

# Last 100 lines
docker-compose logs --tail=100 hyoda-app

# Errors only
docker-compose logs hyoda-app | grep -i error
```

### Monitoring

```bash
# Resource usage
docker stats

# Disk space
df -h

# Service health
curl http://localhost:8002/health
```

### Updates

```bash
# Pull latest code
git pull origin SUditya

# Rebuild and redeploy
docker-compose down
./deploy.sh --build
```

---

## 🔐 Security Checklist

- [ ] OpenAI API key stored securely in `.env`
- [ ] `.env` file permissions set to 600: `chmod 600 .env`
- [ ] HTTPS enabled (self-signed cert minimum)
- [ ] Firewall configured (allow ports 80, 443, optionally 8002)
- [ ] SSH key authentication enabled (disable password auth)
- [ ] Regular backups scheduled
- [ ] Monitoring alerts configured

### Recommended Firewall Setup (Ubuntu/Debian)

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Optional: Allow direct backend access
sudo ufw allow 8002/tcp

# Enable firewall
sudo ufw enable
sudo ufw status
```

---

## 🆘 Emergency Commands

### Complete Reset

```bash
# ⚠️ WARNING: Deletes all data!
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Backup Before Reset

```bash
# Backup MongoDB
docker-compose exec mongodb mongodump --out=/tmp/backup
docker cp hyoda-mongodb:/tmp/backup ./mongodb_backup

# Backup ChromaDB
tar -czf chroma_backup_$(date +%Y%m%d).tar.gz chroma_db/

# Backup config
cp .env .env.backup
```

### Restore from Backup

```bash
# Restore MongoDB
docker cp ./mongodb_backup hyoda-mongodb:/tmp/backup
docker-compose exec mongodb mongorestore /tmp/backup

# Restore ChromaDB
tar -xzf chroma_backup_YYYYMMDD.tar.gz
```

---

## 📞 Need Help?

1. **Check Logs First**: `docker-compose logs -f`
2. **Health Check**: `curl http://localhost:8002/health`
3. **Service Status**: `docker-compose ps`
4. **GitHub Issues**: https://github.com/Tharun2302/yoda/issues
5. **Full Documentation**: See `README.md`

---

## ✅ Success Indicators

You know it's working when:

✅ `docker-compose ps` shows all services as "Up (healthy)"  
✅ `curl http://localhost:8002/health` returns `{"status":"healthy"}`  
✅ Browser shows chatbot interface at `https://your-server-ip`  
✅ Chat messages get AI responses  
✅ No errors in logs: `docker-compose logs hyoda-app`  

---

## 🎉 You're Live!

Your HealthYoda AI chatbot is now deployed and ready to use!

**Production URL**: `https://your-server-ip`  
**Dashboard**: `https://your-server-ip/healthbench/dashboard`  
**API Health**: `https://your-server-ip/health`

Enjoy! 🚀

