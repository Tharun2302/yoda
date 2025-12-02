# HealthYoda Deployment Checklist ✅

Use this checklist to ensure a successful deployment of HealthYoda to your server.

## 📋 Pre-Deployment Checklist

### 1. Prerequisites Verification

- [ ] **Server Requirements**
  - [ ] Linux server (Ubuntu 20.04+ or similar)
  - [ ] Minimum 2GB RAM available
  - [ ] Minimum 20GB disk space available
  - [ ] Server IP address noted: `___________________`
  - [ ] SSH access configured and tested

- [ ] **Required Software**
  - [ ] Docker installed and running
  - [ ] Docker Compose installed
  - [ ] OpenSSL available (for SSL generation)
  - [ ] Git installed (if cloning from repository)

- [ ] **API Keys & Credentials**
  - [ ] OpenAI API key obtained
  - [ ] (Optional) Langfuse account created
  - [ ] (Optional) Langfuse public/secret keys obtained

### 2. Repository Setup

- [ ] Repository cloned from GitHub
  ```bash
  git clone -b SUditya https://github.com/Tharun2302/yoda.git
  ```
- [ ] Navigated to project directory: `cd yoda`
- [ ] All files present and intact

### 3. Environment Configuration

- [ ] `.env` file created from template
  ```bash
  cp env.template .env
  ```
- [ ] OpenAI API key added to `.env`
- [ ] Server IP address updated in `.env` (ALLOWED_ORIGINS)
- [ ] (Optional) Langfuse credentials added to `.env`
- [ ] (Optional) MongoDB configuration verified in `.env`
- [ ] `.env` file permissions set correctly
  ```bash
  chmod 600 .env
  ```

### 4. SSL Certificate Generation

- [ ] SSL directory exists: `mkdir -p ssl`
- [ ] SSL certificates generated
  ```bash
  ./generate_ssl_cert.sh
  ```
- [ ] Verify certificate files exist:
  - [ ] `ssl/cert.pem` exists
  - [ ] `ssl/key.pem` exists
- [ ] Certificate permissions set correctly
  ```bash
  chmod 600 ssl/key.pem
  chmod 644 ssl/cert.pem
  ```

### 5. Configuration Files Review

- [ ] **nginx.conf** - Server IP updated (if needed)
- [ ] **docker-compose.yml** - Ports not conflicting with existing services
- [ ] **Dockerfile** - No modifications needed
- [ ] **deploy.sh** - Execute permissions set
  ```bash
  chmod +x deploy.sh
  ```

### 6. Knowledge Base

- [ ] Question Book document exists: `docx/Question BOOK.docx`
- [ ] Document is readable and not corrupted
- [ ] Backup of original document created (optional but recommended)

## 🚀 Deployment Process

### 1. Pre-Deployment Verification

- [ ] All pre-deployment checklist items completed
- [ ] No conflicting services running on ports 80, 443, 8002, 27017
  ```bash
  sudo lsof -i :80
  sudo lsof -i :443
  sudo lsof -i :8002
  sudo lsof -i :27017
  ```
- [ ] Docker service is running
  ```bash
  sudo systemctl status docker
  ```

### 2. Deploy Application

- [ ] Run deployment script
  ```bash
  ./deploy.sh
  ```
  OR
  ```bash
  docker-compose up -d
  ```
- [ ] Deployment script completed without errors
- [ ] All services started successfully

### 3. Service Verification

- [ ] Check service status
  ```bash
  docker-compose ps
  ```
- [ ] All services showing as "healthy" or "Up":
  - [ ] `hyoda-chatbot` - Status: Up (healthy)
  - [ ] `hyoda-mongodb` - Status: Up (healthy)
  - [ ] `hyoda-nginx` - Status: Up (healthy)

### 4. Service Logs Check

- [ ] Application logs show no errors
  ```bash
  docker-compose logs hyoda-app | tail -50
  ```
- [ ] MongoDB connected successfully
- [ ] OpenAI API key validated
- [ ] RAG system initialized
- [ ] HealthBench evaluator loaded
- [ ] No Python exceptions in startup

## 🧪 Testing & Validation

### 1. Health Check

- [ ] Health endpoint responds successfully
  ```bash
  curl http://localhost:8002/health
  ```
- [ ] Response is: `{"status": "healthy"}`

### 2. Network Access Tests

- [ ] **HTTP Access** (should redirect to HTTPS)
  ```bash
  curl -I http://YOUR_SERVER_IP
  ```
  Expected: 301 Redirect to HTTPS

- [ ] **HTTPS Access** (main access point)
  ```bash
  curl -k https://YOUR_SERVER_IP/health
  ```
  Expected: `{"status": "healthy"}`

- [ ] **Direct Backend Access**
  ```bash
  curl http://YOUR_SERVER_IP:8002/health
  ```
  Expected: `{"status": "healthy"}`

### 3. Frontend Access

- [ ] Open browser and navigate to: `https://YOUR_SERVER_IP`
- [ ] Accept self-signed certificate warning (click Advanced → Proceed)
- [ ] Chatbot interface loads correctly
- [ ] No JavaScript console errors
- [ ] Chat input field is visible and functional

### 4. Functional Testing

- [ ] **Basic Chat Test**
  - [ ] Type a message in chat interface
  - [ ] Send message
  - [ ] Receive streaming response from AI
  - [ ] Response is relevant and coherent

- [ ] **Medical Query Test**
  - [ ] Ask: "What are the symptoms of diabetes?"
  - [ ] Receive detailed, medically accurate response
  - [ ] Response includes information from Question Book (if applicable)

- [ ] **Evaluation Dashboard**
  - [ ] Navigate to: `https://YOUR_SERVER_IP/healthbench/dashboard`
  - [ ] Dashboard loads without errors
  - [ ] Can view evaluation metrics (may be empty initially)

### 5. Database Verification

- [ ] MongoDB is accessible
  ```bash
  docker-compose exec mongodb mongosh --eval "db.version()"
  ```
- [ ] Database initialized
  ```bash
  docker-compose exec mongodb mongosh --eval "show dbs"
  ```
- [ ] HealthYoda database exists

### 6. ChromaDB Verification

- [ ] ChromaDB directory has files
  ```bash
  ls -lh chroma_db/
  ```
- [ ] Vector database initialized
- [ ] Question Book indexed (check logs for "RAG system initialized")

## 🔒 Security Verification

### 1. SSL/TLS

- [ ] HTTPS working correctly
- [ ] HTTP redirects to HTTPS
- [ ] Certificate valid (even if self-signed)
- [ ] TLS 1.2 and 1.3 enabled

### 2. Security Headers

- [ ] Test security headers
  ```bash
  curl -I https://YOUR_SERVER_IP -k
  ```
- [ ] Verify headers present:
  - [ ] `X-Content-Type-Options: nosniff`
  - [ ] `X-Frame-Options: DENY`
  - [ ] `X-XSS-Protection: 1; mode=block`
  - [ ] `Strict-Transport-Security` (HSTS)

### 3. Rate Limiting

- [ ] Rate limiting configured in nginx
- [ ] Test by sending multiple rapid requests
- [ ] Verify 429 (Too Many Requests) response when limit exceeded

### 4. CORS

- [ ] CORS configured with specific origins
- [ ] No wildcard (*) origins in production
- [ ] Only allowed origins can access API

## 📊 Monitoring Setup

### 1. Logging

- [ ] Application logs accessible
  ```bash
  docker-compose logs -f hyoda-app
  ```
- [ ] MongoDB logs accessible
- [ ] Nginx logs accessible
- [ ] Log rotation configured (for long-term deployment)

### 2. Langfuse Integration (Optional)

- [ ] Langfuse enabled in `.env`
- [ ] Test conversation tracked in Langfuse dashboard
- [ ] Metrics visible in Langfuse UI
- [ ] No authentication errors in logs

### 3. Resource Monitoring

- [ ] Check container resource usage
  ```bash
  docker stats
  ```
- [ ] Memory usage within acceptable limits
- [ ] CPU usage reasonable
- [ ] Disk space sufficient

## 📝 Post-Deployment

### 1. Documentation

- [ ] Deployment date recorded: `___________________`
- [ ] Server IP documented: `___________________`
- [ ] Admin credentials stored securely
- [ ] Backup procedures documented
- [ ] Emergency contact information updated

### 2. Backup Configuration

- [ ] MongoDB backup script created
- [ ] ChromaDB backup scheduled
- [ ] `.env` file backed up securely
- [ ] SSL certificates backed up

### 3. User Access

- [ ] Frontend URL shared with users
- [ ] User documentation provided
- [ ] Self-signed certificate warning explained
- [ ] Support contact information shared

### 4. Monitoring Alerts (Optional)

- [ ] Uptime monitoring configured
- [ ] Email alerts for downtime
- [ ] Resource usage alerts configured
- [ ] Log aggregation setup

## 🔄 Maintenance Tasks

### Regular Maintenance

- [ ] **Daily**
  - [ ] Check service status: `docker-compose ps`
  - [ ] Monitor disk space: `df -h`
  - [ ] Review error logs

- [ ] **Weekly**
  - [ ] Review full application logs
  - [ ] Check MongoDB size and performance
  - [ ] Verify backup completion
  - [ ] Update monitoring dashboards

- [ ] **Monthly**
  - [ ] Update Docker images
  - [ ] Review and rotate logs
  - [ ] Security audit
  - [ ] Performance optimization review

### Update Procedure

- [ ] Pull latest code: `git pull origin SUditya`
- [ ] Review changelog
- [ ] Test in staging (if available)
- [ ] Backup current state
- [ ] Run: `./deploy.sh --build`
- [ ] Verify all tests pass

## 🚨 Emergency Procedures

### If Service Fails

1. [ ] Check logs: `docker-compose logs hyoda-app`
2. [ ] Check service status: `docker-compose ps`
3. [ ] Restart service: `docker-compose restart hyoda-app`
4. [ ] If still failing, full restart: `docker-compose down && docker-compose up -d`

### If Database Corrupts

1. [ ] Stop services: `docker-compose down`
2. [ ] Restore from backup
3. [ ] Restart services: `docker-compose up -d`
4. [ ] Verify data integrity

### Complete Reset (Last Resort)

```bash
# WARNING: This will delete all data!
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

## ✅ Final Sign-Off

- [ ] All checklist items completed
- [ ] Application accessible and functional
- [ ] No critical errors in logs
- [ ] Users can access the chatbot
- [ ] Monitoring in place
- [ ] Documentation complete

**Deployment Completed By:** `___________________`

**Date:** `___________________`

**Time:** `___________________`

**Production URL:** `___________________`

**Notes:** 
```
_______________________________________________________________
_______________________________________________________________
_______________________________________________________________
```

---

## 📞 Support Contacts

**Technical Issues:**
- Check logs first: `docker-compose logs -f`
- GitHub Issues: https://github.com/Tharun2302/yoda/issues

**OpenAI API Issues:**
- OpenAI Status: https://status.openai.com/
- OpenAI Support: https://help.openai.com/

**Docker Issues:**
- Docker Documentation: https://docs.docker.com/

---

**Deployment Checklist Version:** 1.0
**Last Updated:** December 2024

