# 🚀 HealthYoda Deployment Guide for movefuze.com

## 📋 Overview

**Domain**: movefuze.com (www.movefuze.com)  
**Server IP**: 68.183.88.5  
**Branch**: SUditya  
**Repository**: https://github.com/Tharun2302/yoda.git

---

## ✅ Pre-Deployment Checklist

### DNS Configuration
- [ ] Domain `movefuze.com` points to `68.183.88.5`
- [ ] Domain `www.movefuze.com` points to `68.183.88.5`
- [ ] DNS propagation completed (check with `nslookup movefuze.com`)

### Server Requirements
- [ ] Linux server (Ubuntu 20.04+ recommended)
- [ ] Minimum 2GB RAM
- [ ] Minimum 20GB disk space
- [ ] Root or sudo access
- [ ] Ports 80, 443, 8002 open

### API Keys Required
- [ ] OpenAI API Key (for GPT models)
- [ ] Gemini API Key (optional, for Google models)
- [ ] Deepgram API Key (optional, for voice features)
- [ ] Langfuse Keys (optional, for observability)

---

## 🚀 Quick Deployment (Automated)

### Option 1: One-Line Deployment

SSH into your server and run:

```bash
ssh root@68.183.88.5
curl -fsSL https://raw.githubusercontent.com/Tharun2302/yoda/SUditya/DEPLOY_TO_SERVER_68.183.88.5.sh -o deploy.sh && chmod +x deploy.sh && ./deploy.sh
```

This script will:
1. Clean any existing deployments
2. Install Docker and Docker Compose
3. Clone the SUditya branch
4. Prompt for API keys
5. Generate SSL certificates for movefuze.com
6. Build and start all services

### Option 2: Manual Deployment

#### Step 1: Connect to Server
```bash
ssh root@68.183.88.5
```

#### Step 2: Install Prerequisites
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installations
docker --version
docker-compose --version
```

#### Step 3: Clone Repository
```bash
# Create deployment directory
sudo mkdir -p /opt/yoda
sudo chown -R $USER:$USER /opt/yoda
cd /opt/yoda

# Clone SUditya branch
git clone -b SUditya --single-branch https://github.com/Tharun2302/yoda.git .
```

#### Step 4: Configure Environment
```bash
# Copy environment template
cp env.template .env

# Edit configuration
nano .env
```

**Update the following in .env:**
```env
# REQUIRED: OpenAI API Key
OPENAI_API_KEY=sk-your-actual-openai-key-here

# OPTIONAL: Google Gemini (for alternative models)
GEMINI_API_KEY=your-gemini-api-key-here

# OPTIONAL: Deepgram (for fast voice transcription)
DEEPGRAM_API_KEY=your-deepgram-api-key-here

# OPTIONAL: Langfuse (for observability)
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-your-public-key
LANGFUSE_SECRET_KEY=sk-your-secret-key

# CORS is already configured for movefuze.com
# ALLOWED_ORIGINS is set in env.template
```

#### Step 5: Generate SSL Certificates
```bash
# Generate self-signed SSL certificate
chmod +x generate_ssl_cert.sh
./generate_ssl_cert.sh
```

**Note**: This generates a self-signed certificate. For production, consider using Let's Encrypt:
```bash
# Install certbot
sudo apt install certbot

# Generate certificate
sudo certbot certonly --standalone -d movefuze.com -d www.movefuze.com

# Copy certificates to ssl directory
sudo cp /etc/letsencrypt/live/movefuze.com/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/movefuze.com/privkey.pem ssl/key.pem
sudo chown $USER:$USER ssl/*.pem
```

#### Step 6: Deploy Application
```bash
# Make deploy script executable
chmod +x deploy.sh

# Deploy all services
./deploy.sh

# Or force rebuild
./deploy.sh --build
```

#### Step 7: Verify Deployment
```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f

# Test health endpoint
curl http://localhost:8002/health
```

---

## 🌐 Access Your Application

### URLs
- **Primary (HTTPS)**: https://movefuze.com
- **WWW (HTTPS)**: https://www.movefuze.com
- **IP (HTTPS)**: https://68.183.88.5
- **Direct HTTP**: http://68.183.88.5:8002
- **Dashboard**: https://movefuze.com/healthbench/dashboard
- **Health Check**: https://movefuze.com/health

### First Access
When accessing via HTTPS for the first time (if using self-signed cert):
1. Browser will show security warning
2. Click "Advanced"
3. Click "Proceed to movefuze.com (unsafe)"
4. This is normal for self-signed certificates

---

## 🔧 Configuration Files Updated

All files have been configured for `movefuze.com` and `68.183.88.5`:

| File | Updates Made |
|------|-------------|
| `env.template` | Added movefuze.com to ALLOWED_ORIGINS |
| `docker-compose.yml` | Added movefuze.com to CORS origins |
| `nginx.conf` | Added movefuze.com to server_name |
| `generate_ssl_cert.sh` | SSL cert for movefuze.com + IP |
| `generate_ssl_cert.bat` | SSL cert for movefuze.com + IP (Windows) |
| `app.py` | Updated CORS and CSP headers |
| `deploy.sh` | Updated display URLs |
| `DEPLOY_TO_SERVER_68.183.88.5.sh` | Updated deployment URLs |

---

## 📊 Service Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     nginx (Port 80/443)                  │
│   - SSL Termination                                      │
│   - Rate Limiting                                        │
│   - Domain: movefuze.com, www.movefuze.com              │
└─────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────┐
│              Flask Application (Port 8002)               │
│   - HealthYoda Chatbot                                   │
│   - RAG System (ChromaDB)                                │
│   - HealthBench Evaluation                               │
│   - Langfuse Tracking                                    │
└─────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────┐
│                 MongoDB (Port 27017)                     │
│   - Session Storage                                      │
│   - Conversation History                                 │
│   - Evaluation Results                                   │
└─────────────────────────────────────────────────────────┘
```

---

## 🛠️ Useful Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f hyoda-app
docker-compose logs -f mongodb
docker-compose logs -f nginx

# Last 100 lines
docker-compose logs --tail=100 hyoda-app
```

### Service Management
```bash
# Check status
docker-compose ps

# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart hyoda-app

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Update Application
```bash
cd /opt/yoda

# Pull latest code
git pull origin SUditya

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Database Operations
```bash
# Access MongoDB shell
docker-compose exec mongodb mongosh

# Backup MongoDB
docker-compose exec mongodb mongodump --out=/tmp/backup
docker cp hyoda-mongodb:/tmp/backup ./mongodb_backup

# Restore MongoDB
docker cp ./mongodb_backup hyoda-mongodb:/tmp/restore
docker-compose exec mongodb mongorestore /tmp/restore
```

### Resource Monitoring
```bash
# Container resource usage
docker stats

# Disk usage
docker system df

# Clean up unused resources
docker system prune -a
```

---

## 🔍 Troubleshooting

### Service Won't Start
```bash
# Check logs for errors
docker-compose logs hyoda-app

# Common issues:
# 1. Port already in use
sudo lsof -i :8002
sudo lsof -i :80
sudo lsof -i :443

# 2. Permission issues
sudo chown -R $USER:$USER /opt/yoda
chmod +x deploy.sh generate_ssl_cert.sh

# 3. Missing .env file
cp env.template .env
nano .env
```

### SSL Certificate Issues
```bash
# Regenerate certificates
rm -rf ssl/*
./generate_ssl_cert.sh

# Verify certificates
openssl x509 -in ssl/cert.pem -text -noout

# Check certificate domain
openssl x509 -in ssl/cert.pem -noout -subject -ext subjectAltName
```

### MongoDB Connection Issues
```bash
# Check MongoDB is running
docker-compose ps mongodb

# Test connection
docker-compose exec mongodb mongosh --eval "db.version()"

# Restart MongoDB
docker-compose restart mongodb
```

### Domain Not Working
```bash
# Check DNS resolution
nslookup movefuze.com
dig movefuze.com

# Check nginx configuration
docker-compose exec nginx nginx -t

# Restart nginx
docker-compose restart nginx
```

### Application Errors
```bash
# Check application logs
docker-compose logs -f hyoda-app

# Access application shell
docker-compose exec hyoda-app bash

# Test health endpoint
curl http://localhost:8002/health

# Test from outside
curl https://movefuze.com/health
```

---

## 🔐 Security Recommendations

### Production SSL Certificate
For production use, replace self-signed certificate with Let's Encrypt:

```bash
# Install certbot
sudo apt install certbot

# Stop nginx temporarily
docker-compose stop nginx

# Generate certificate
sudo certbot certonly --standalone \
  -d movefuze.com \
  -d www.movefuze.com \
  --non-interactive \
  --agree-tos \
  --email your-email@example.com

# Copy certificates
sudo cp /etc/letsencrypt/live/movefuze.com/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/movefuze.com/privkey.pem ssl/key.pem
sudo chown $USER:$USER ssl/*.pem

# Restart nginx
docker-compose start nginx
```

### Auto-Renewal Setup
```bash
# Create renewal script
cat > /opt/yoda/renew-ssl.sh << 'EOF'
#!/bin/bash
docker-compose stop nginx
certbot renew --quiet
cp /etc/letsencrypt/live/movefuze.com/fullchain.pem /opt/yoda/ssl/cert.pem
cp /etc/letsencrypt/live/movefuze.com/privkey.pem /opt/yoda/ssl/key.pem
docker-compose start nginx
EOF

chmod +x /opt/yoda/renew-ssl.sh

# Add to crontab (runs monthly)
(crontab -l 2>/dev/null; echo "0 0 1 * * /opt/yoda/renew-ssl.sh") | crontab -
```

### Firewall Configuration
```bash
# Install UFW
sudo apt install ufw

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

---

## 📈 Monitoring & Observability

### Langfuse Dashboard
If Langfuse is enabled:
1. Go to https://cloud.langfuse.com
2. Login with your account
3. View conversation traces, token usage, latency metrics
4. Analyze evaluation scores and quality metrics

### HealthBench Dashboard
Access at: https://movefuze.com/healthbench/dashboard
- View evaluation results
- Monitor chatbot accuracy
- Track performance metrics

### System Monitoring
```bash
# CPU and Memory usage
docker stats

# Disk usage
df -h
docker system df

# Network connections
netstat -tulpn | grep -E '(80|443|8002|27017)'
```

---

## 🎯 Next Steps

1. **Test the Application**
   - Access https://movefuze.com
   - Test chatbot functionality
   - Check dashboard at https://movefuze.com/healthbench/dashboard

2. **Upload Knowledge Base** (if needed)
   - Place your `Question BOOK.docx` in `/opt/yoda/docx/`
   - Place text files in `/opt/yoda/txt/`
   - Restart application: `docker-compose restart hyoda-app`

3. **Set Up Production SSL**
   - Follow Let's Encrypt instructions above
   - Set up auto-renewal

4. **Configure Monitoring**
   - Set up Langfuse (optional)
   - Monitor logs regularly
   - Set up alerts

5. **Regular Maintenance**
   - Backup MongoDB weekly
   - Update application monthly
   - Renew SSL certificates before expiry

---

## 📞 Support

For issues or questions:
1. Check this guide's troubleshooting section
2. Review logs: `docker-compose logs -f`
3. Check GitHub repository for updates
4. Review deployment status files in the repository

---

**🎉 Your HealthYoda chatbot is ready for production at movefuze.com!**

Last Updated: December 2025

