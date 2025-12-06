# 🚀 Quick Start - HealthYoda on movefuze.com

## One-Command Deployment

SSH into your server and run:

```bash
ssh root@68.183.88.5
curl -fsSL https://raw.githubusercontent.com/Tharun2302/yoda/SUditya/DEPLOY_TO_SERVER_68.183.88.5.sh -o deploy.sh && chmod +x deploy.sh && ./deploy.sh
```

## What This Does

1. ✅ Installs Docker & Docker Compose
2. ✅ Clones the SUditya branch
3. ✅ Prompts for OpenAI API key
4. ✅ Generates SSL certificate for movefuze.com
5. ✅ Builds and starts all services
6. ✅ Verifies deployment

## Access Your App

After deployment completes:

- **🌐 Primary URL**: https://movefuze.com
- **🌐 WWW URL**: https://www.movefuze.com
- **📊 Dashboard**: https://movefuze.com/healthbench/dashboard
- **❤️ Health Check**: https://movefuze.com/health

## DNS Requirements

Before deploying, ensure:
- `movefuze.com` → `68.183.88.5` (A record)
- `www.movefuze.com` → `68.183.88.5` (A record)

Check DNS propagation:
```bash
nslookup movefuze.com
```

## Required

- OpenAI API Key (will be prompted during deployment)

## Optional

- Gemini API Key (for alternative AI models)
- Deepgram API Key (for voice features)
- Langfuse Keys (for observability)

## Post-Deployment

### View Logs
```bash
cd /opt/yoda
docker-compose logs -f
```

### Check Status
```bash
docker-compose ps
```

### Restart Services
```bash
docker-compose restart
```

## Troubleshooting

### Can't Access Site?
```bash
# Check services are running
docker-compose ps

# Check nginx logs
docker-compose logs nginx

# Verify DNS
nslookup movefuze.com
```

### Application Errors?
```bash
# Check app logs
docker-compose logs -f hyoda-app

# Restart app
docker-compose restart hyoda-app
```

### SSL Certificate Warning?
- This is normal for self-signed certificates
- Click "Advanced" → "Proceed to movefuze.com"
- For production, use Let's Encrypt (see full guide)

## Full Documentation

See `DEPLOYMENT_GUIDE_MOVEFUZE.md` for complete documentation.

---

**🎉 You're all set! Your HealthYoda AI chatbot is live!**

