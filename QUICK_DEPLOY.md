# Quick Deployment Commands for Digital Ocean

## 🚀 Fastest Way to Deploy

### On Your Local Machine

```bash
# 1. Copy your project to the server
scp -r HYoda root@167.71.238.114:/opt/hyoda

# 2. SSH into the server
ssh root@167.71.238.114
```

### On the Digital Ocean Server

```bash
# 1. Navigate to project directory
cd /opt/hyoda

# 2. Install Docker (if not already installed)
curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh && rm get-docker.sh

# 3. Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose && chmod +x /usr/local/bin/docker-compose

# 4. Configure environment
cp env.template .env
nano .env  # Add your OPENAI_API_KEY

# 5. Make deployment script executable
chmod +x deploy.sh

# 6. Deploy!
./deploy.sh
```

## ⚡ One-Line Deploy (After Files Uploaded)

```bash
cd /opt/hyoda && cp env.template .env && nano .env && chmod +x deploy.sh && ./deploy.sh
```

## 🔧 Essential Commands

```bash
# View logs
docker-compose logs -f

# Restart application
docker-compose restart hyoda-app

# Stop all services
docker-compose down

# Start all services
docker-compose up -d

# Rebuild and restart
./deploy.sh --build
```

## 🌐 Access Your Application

After deployment, access at:

- **Main App**: http://167.71.238.114/
- **Chatbot**: http://167.71.238.114/index.html
- **Dashboard**: http://167.71.238.114/healthbench/dashboard
- **Health Check**: http://167.71.238.114/health

## ✅ Required Configuration

In your `.env` file, you MUST set:

```bash
OPENAI_API_KEY=sk-your-actual-key-here
```

Everything else has sensible defaults!

## 🐛 Quick Troubleshooting

**Port already in use?**
```bash
docker-compose down && ./deploy.sh
```

**Can't connect?**
```bash
# Check firewall
ufw status
ufw allow 80/tcp
ufw allow 8002/tcp
```

**Need to see what's wrong?**
```bash
docker-compose logs -f hyoda-app
```

**Fresh start?**
```bash
docker-compose down -v && ./deploy.sh --build
```

## 📦 What Gets Deployed?

1. **Flask Application** (Port 8002)
2. **MongoDB** (Port 27017) - For session storage
3. **Nginx** (Port 80) - Reverse proxy and load balancer

## 🎯 Success Indicators

After running `./deploy.sh`, you should see:

```
✓ Environment file found
✓ Prerequisites checked
✓ Docker images built
✓ All services started
Deployment completed successfully!
```

Then test:
```bash
curl http://localhost:8002/health
# Should return: {"status":"healthy"}
```

## 💡 Pro Tips

1. **Use screen/tmux** for long-running sessions:
   ```bash
   screen -S deploy
   ./deploy.sh
   # Ctrl+A, D to detach
   # screen -r deploy to reattach
   ```

2. **Monitor in real-time**:
   ```bash
   watch docker-compose ps
   ```

3. **Quick log check**:
   ```bash
   docker-compose logs --tail=50 hyoda-app
   ```

4. **Auto-restart on crash**:
   Already configured in docker-compose.yml with `restart: unless-stopped`

---

**Need more details?** See `DEPLOYMENT.md` for comprehensive guide.

