# 📝 Step-by-Step Deployment Guide

## Complete Deployment Checklist for HYoda on Digital Ocean

Follow these steps in order. Check off each step as you complete it.

---

## 🔧 Phase 1: Preparation (On Your Windows PC)

### ☐ Step 1: Verify Project Files

```powershell
cd "C:\Users\TharunP\OneDrive - CloudFuze, Inc\Desktop\Evals\HYoda"
dir
```

**Verify these files exist:**
- [ ] Dockerfile
- [ ] docker-compose.yml
- [ ] env.template
- [ ] deploy.sh
- [ ] nginx.conf
- [ ] app.py
- [ ] requirements.txt
- [ ] docx/Question BOOK.docx

### ☐ Step 2: Get Your OpenAI API Key Ready

You'll need your OpenAI API key. Get it from: https://platform.openai.com/api-keys

Write it down or copy it:
```
OPENAI_API_KEY: sk-_______________________________
```

---

## 📤 Phase 2: Upload to Digital Ocean Server

### ☐ Step 3: Upload Files

**Choose ONE method:**

#### Method A: PowerShell (Fast)

```powershell
cd "C:\Users\TharunP\OneDrive - CloudFuze, Inc\Desktop\Evals"
scp -r HYoda root@167.71.238.114:/opt/hyoda
```

**Enter your server password when prompted**

#### Method B: WinSCP (Easier for beginners)

1. Download WinSCP: https://winscp.net/eng/download.php
2. Install and open WinSCP
3. New Session:
   - File protocol: `SCP`
   - Host name: `167.71.238.114`
   - User name: `root`
   - Password: `<your-password>`
4. Click "Login"
5. Drag `HYoda` folder from left to `/opt/` on right
6. Wait for upload to complete

### ☐ Step 4: Verify Upload

```powershell
ssh root@167.71.238.114 "ls -la /opt/hyoda"
```

**You should see all your project files listed**

---

## 🖥️ Phase 3: Server Setup (On Digital Ocean Server)

### ☐ Step 5: Connect to Server

```powershell
ssh root@167.71.238.114
```

**From this point on, all commands run on the server**

### ☐ Step 6: Update System

```bash
apt update && apt upgrade -y
```

**Wait for updates to complete (2-5 minutes)**

### ☐ Step 7: Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# Verify installation
docker --version
```

**Expected output:** `Docker version 24.x.x`

### ☐ Step 8: Install Docker Compose

```bash
# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Verify installation
docker-compose --version
```

**Expected output:** `docker-compose version 1.x.x` or `Docker Compose version v2.x.x`

### ☐ Step 9: Configure Firewall

```bash
# Install firewall
apt install -y ufw

# Configure firewall rules
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8002/tcp

# Enable firewall
ufw --force enable

# Check status
ufw status
```

**Expected output:** Shows ports 22, 80, 443, 8002 as ALLOW

---

## ⚙️ Phase 4: Configure Application

### ☐ Step 10: Navigate to Project Directory

```bash
cd /opt/hyoda
pwd
```

**Expected output:** `/opt/hyoda`

### ☐ Step 11: Create Environment File

```bash
# Copy template
cp env.template .env

# Verify file created
ls -la .env
```

**Expected output:** File `.env` exists

### ☐ Step 12: Edit Environment File

```bash
nano .env
```

**Edit these lines:**

```bash
# Change this line (REQUIRED):
OPENAI_API_KEY=your-openai-api-key-here

# TO (use your actual key):
OPENAI_API_KEY=sk-your-actual-key-from-step-2

# Also update CORS (RECOMMENDED):
ALLOWED_ORIGINS=http://167.71.238.114,http://167.71.238.114:8002,http://localhost:8002
```

**Save and exit:**
- Press `Ctrl+X`
- Press `Y`
- Press `Enter`

### ☐ Step 13: Verify Configuration

```bash
# Check if API key is set
grep "OPENAI_API_KEY" .env
```

**Should show:** `OPENAI_API_KEY=sk-...` (your actual key)

**⚠️ IMPORTANT:** If it still shows `your-openai-api-key-here`, go back to Step 12!

### ☐ Step 14: Verify Question Book Exists

```bash
ls -la docx/
```

**Must see:** `Question BOOK.docx`

**If missing:**
```bash
# Create docx directory if needed
mkdir -p docx

# Then upload from Windows:
# scp "C:\...\Question BOOK.docx" root@167.71.238.114:/opt/hyoda/docx/
```

---

## 🚀 Phase 5: Deployment

### ☐ Step 15: Make Deploy Script Executable

```bash
chmod +x deploy.sh
```

### ☐ Step 16: Run Deployment

```bash
./deploy.sh
```

**This will take 5-10 minutes on first run**

**You should see:**
```
✓ Environment file found
✓ Prerequisites checked
Building Docker images...
[Building...]
✓ Docker images built
Starting services...
✓ All services started
╔════════════════════════════════════════════╗
║         Deployment Completed! 🎉           ║
╚════════════════════════════════════════════╝
```

---

## ✅ Phase 6: Verification

### ☐ Step 17: Check Container Status

```bash
docker-compose ps
```

**Expected output:** 3 containers with status "Up":
```
NAME                COMMAND             STATUS
hyoda-chatbot       "python app.py"     Up
hyoda-mongodb       "docker-entrypoint" Up
hyoda-nginx         "/docker-entrypoint" Up
```

**⚠️ If any show "Exit" status, check logs:** `docker-compose logs <service-name>`

### ☐ Step 18: Test Health Endpoint

```bash
curl http://localhost:8002/health
```

**Expected output:** `{"status":"healthy"}`

**If you get error, check logs:** `docker-compose logs hyoda-app`

### ☐ Step 19: Test External Access

**From your Windows PC browser, visit:**

```
http://167.71.238.114/health
```

**Expected:** You should see `{"status":"healthy"}`

**If connection refused:**
- Check firewall: `ufw status`
- Check nginx: `docker-compose logs nginx`

### ☐ Step 20: Test Chatbot Interface

**Open in browser:**

```
http://167.71.238.114/index.html
```

**Expected:** Chatbot interface loads

### ☐ Step 21: Test Chatbot Functionality

1. Click "Start Conversation"
2. Type: "I have chest pain"
3. Bot should respond with a question

**If bot doesn't respond:**
```bash
# Check logs for errors
docker-compose logs -f hyoda-app

# Common issue: API key not set correctly
docker-compose exec hyoda-app env | grep OPENAI
```

### ☐ Step 22: Test Dashboard

**Open in browser:**

```
http://167.71.238.114/healthbench/dashboard
```

**Expected:** Dashboard interface loads

---

## 🎉 Phase 7: Final Checks

### ☐ Step 23: Check MongoDB Connection

```bash
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"
```

**Expected output:** `{ ok: 1 }`

### ☐ Step 24: View Application Logs

```bash
docker-compose logs --tail=50 hyoda-app
```

**Look for:**
- ✅ "Starting HealthYoda chatbot server..."
- ✅ "OpenAI API key found!"
- ✅ "MongoDB connected!"
- ✅ "RAG System loaded: X questions available"
- ❌ NO "ERROR" or "FAILED" messages

### ☐ Step 25: Check Resource Usage

```bash
docker stats --no-stream
```

**Verify:**
- CPU usage < 50%
- Memory usage < 80%

### ☐ Step 26: Test Full Conversation Flow

1. Go to: http://167.71.238.114/index.html
2. Start conversation
3. Answer 5-10 questions
4. Check dashboard: http://167.71.238.114/healthbench/dashboard
5. Verify evaluation scores appear

---

## 📊 Success Criteria

Your deployment is successful if:

- [x] ✅ All 3 containers are "Up"
- [x] ✅ Health endpoint returns `{"status":"healthy"}`
- [x] ✅ Chatbot interface loads in browser
- [x] ✅ Bot responds to messages
- [x] ✅ Dashboard shows evaluation data
- [x] ✅ No critical errors in logs
- [x] ✅ MongoDB is connected

---

## 🔄 Ongoing Maintenance

### Monitor Logs

```bash
# View real-time logs
docker-compose logs -f

# View app logs only
docker-compose logs -f hyoda-app
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart app only
docker-compose restart hyoda-app
```

### Update Application

```bash
# After uploading new code
cd /opt/hyoda
./deploy.sh --build
```

### Backup MongoDB

```bash
# Create backup
docker-compose exec mongodb mongodump --out=/data/backup
docker cp hyoda-mongodb:/data/backup ./backup-$(date +%Y%m%d)
```

---

## 🐛 Troubleshooting Quick Reference

| Issue | Quick Fix |
|-------|-----------|
| Port 8002 in use | `docker-compose down && ./deploy.sh` |
| Can't connect externally | `ufw allow 8002/tcp && ufw reload` |
| MongoDB connection failed | `docker-compose restart mongodb` |
| API key not working | `nano .env` (fix key) → `docker-compose restart hyoda-app` |
| Container keeps restarting | `docker-compose logs <container-name>` |
| Out of disk space | `docker system prune -a` |

---

## 📞 Getting Help

If stuck on any step:

1. **Check logs:** `docker-compose logs -f hyoda-app`
2. **Verify config:** `cat .env | grep OPENAI`
3. **Check docs:** See `DEPLOYMENT.md` for detailed troubleshooting
4. **Clean restart:** `docker-compose down -v && ./deploy.sh --build`

---

## ✅ Deployment Complete!

If you've completed all steps above, congratulations! 🎉

Your HYoda medical chatbot is now:
- ✅ Running on Digital Ocean
- ✅ Accessible at http://167.71.238.114
- ✅ Fully functional with OpenAI integration
- ✅ Storing sessions in MongoDB
- ✅ Evaluating responses with HealthBench

**Next Steps:**
- Consider setting up SSL/HTTPS
- Setup automated backups
- Monitor logs regularly
- Keep system updated

---

**Deployment Status:** ✅ COMPLETE  
**Total Steps Completed:** ____ / 26  
**Deployment Time:** ~20-30 minutes  
**Date Deployed:** _______________

