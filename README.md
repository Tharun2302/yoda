# HealthYoda AI Chatbot 🏥

A production-ready medical AI chatbot powered by OpenAI GPT-4, featuring RAG (Retrieval-Augmented Generation), real-time evaluation with HealthBench, and comprehensive observability through Langfuse.

## 🚀 Features

- **Intelligent Medical Conversations**: GPT-4 powered responses with context awareness
- **RAG System**: Knowledge retrieval from medical question banks using ChromaDB
- **Real-time Evaluation**: HealthBench & HELM-style medical accuracy evaluation
- **Observability**: Langfuse integration for conversation tracking and analytics
- **Voice Support**: Optional voice input/output processing
- **Production Ready**: Docker deployment with nginx, SSL, and MongoDB
- **Security**: HIPAA-compliant headers, CORS protection, rate limiting

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Deployment to Server](#deployment-to-server)
- [Configuration](#configuration)
- [Architecture](#architecture)
- [API Endpoints](#api-endpoints)
- [Monitoring & Logs](#monitoring--logs)
- [Troubleshooting](#troubleshooting)

## 🔧 Prerequisites

### For Development
- Python 3.11+
- OpenAI API Key
- (Optional) Langfuse account for observability

### For Production Deployment
- Docker & Docker Compose
- Linux server (Ubuntu 20.04+ recommended)
- Minimum 2GB RAM, 20GB disk space
- OpenSSL (for SSL certificate generation)

## ⚡ Quick Start

### 1. Clone Repository

```bash
git clone -b SUditya https://github.com/Tharun2302/yoda.git
cd yoda
```

### 2. Set Up Environment

```bash
# Copy environment template
cp env.template .env

# Edit .env and add your API keys
nano .env
```

**Required Configuration:**
```env
OPENAI_API_KEY=sk-your-openai-api-key-here
```

**Optional Configuration:**
```env
# Langfuse (for observability)
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...

# MongoDB (enabled by default in docker-compose)
MONGODB_URI=mongodb://mongodb:27017/
MONGODB_DB=healthyoda
```

### 3. Generate SSL Certificates

```bash
# On Linux/Mac
./generate_ssl_cert.sh

# On Windows
.\generate_ssl_cert.bat
```

This creates self-signed certificates in `ssl/` directory:
- `ssl/cert.pem` - SSL certificate
- `ssl/key.pem` - Private key

### 4. Deploy with Docker

```bash
# Make deploy script executable (Linux/Mac only)
chmod +x deploy.sh

# Run deployment
./deploy.sh

# Or manually with docker-compose
docker-compose up -d
```

### 5. Access Application

- **HTTPS**: https://your-server-ip (Recommended)
- **HTTP**: http://your-server-ip:8002
- **Dashboard**: https://your-server-ip/healthbench/dashboard
- **Health Check**: https://your-server-ip/health

**Note**: First HTTPS access will show browser warning (self-signed cert). Click "Advanced" → "Proceed to site".

## 🌐 Deployment to Server

### Step-by-Step Server Deployment

#### 1. Prepare Server

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

#### 2. Transfer Code to Server

**Option A: Git Clone (Recommended)**
```bash
cd /opt  # or your preferred directory
git clone -b SUditya https://github.com/Tharun2302/yoda.git
cd yoda
```

**Option B: Upload via SCP**
```bash
# From your local machine
scp -r . user@your-server-ip:/opt/yoda
```

#### 3. Configure Environment

```bash
cd /opt/yoda

# Create .env file
cp env.template .env
nano .env
```

Update these values in `.env`:
```env
OPENAI_API_KEY=sk-your-actual-key-here
ALLOWED_ORIGINS=https://your-server-ip,http://your-server-ip:8002
```

#### 4. Generate SSL Certificates

```bash
# Generate self-signed certificate
./generate_ssl_cert.sh

# For production, you can use Let's Encrypt instead:
# sudo certbot certonly --standalone -d yourdomain.com
# Then copy certificates to ssl/ directory
```

#### 5. Deploy Application

```bash
# Run deployment script
./deploy.sh

# Or deploy specific services
./deploy.sh --no-nginx  # Deploy without nginx (direct Flask access)
./deploy.sh --build     # Force rebuild Docker images
```

#### 6. Verify Deployment

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f

# Test health endpoint
curl http://localhost:8002/health
```

### Update Server IP Address

If your server IP is different from `167.71.238.114`, update these files:

1. **env.template** (line 37):
```env
ALLOWED_ORIGINS=http://YOUR_SERVER_IP:8002,http://localhost:8002
```

2. **nginx.conf** (lines 30 & 39):
```nginx
server_name YOUR_SERVER_IP;
```

3. **deploy.sh** (lines 159, 163, 165):
```bash
echo -e "  • http://YOUR_SERVER_IP:8002"
```

4. **generate_ssl_cert.sh** (lines 6, 16, 17, 23):
```bash
IP_ADDRESS="YOUR_SERVER_IP"
```

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | ✅ Yes | - | OpenAI API key for GPT models |
| `LANGFUSE_ENABLED` | No | `false` | Enable Langfuse observability |
| `LANGFUSE_PUBLIC_KEY` | No | - | Langfuse public key |
| `LANGFUSE_SECRET_KEY` | No | - | Langfuse secret key |
| `LANGFUSE_HOST` | No | `https://cloud.langfuse.com` | Langfuse server URL |
| `MONGODB_URI` | No | `mongodb://mongodb:27017/` | MongoDB connection string |
| `MONGODB_DB` | No | `healthyoda` | Database name |
| `HEALTHBENCH_GRADER_MODEL` | No | `gpt-4o-mini` | Model for HealthBench grading |
| `HELM_JUDGE_MODEL` | No | `gpt-4o-mini` | Model for HELM evaluation |
| `ALLOWED_ORIGINS` | No | See env.template | CORS allowed origins |
| `RATE_LIMIT_REQUESTS` | No | `100` | Rate limit (requests per window) |
| `RATE_LIMIT_WINDOW` | No | `3600` | Rate limit window (seconds) |
| `VOICE_ENABLED` | No | `false` | Enable voice features |
| `REBUILD_VECTORSTORE` | No | `false` | Rebuild vector database on startup |

### Docker Services

The stack includes three services:

1. **hyoda-app** (Port 8002)
   - Main Flask application
   - RAG system with ChromaDB
   - OpenAI integration
   - HealthBench evaluation

2. **mongodb** (Port 27017)
   - Session storage
   - Evaluation results
   - Conversation history

3. **nginx** (Ports 80, 443)
   - Reverse proxy
   - SSL termination
   - Rate limiting
   - Static file caching

### Volumes

- `mongodb_data`: Persistent MongoDB storage
- `./chroma_db`: ChromaDB vector database
- `./docx`: Medical knowledge base documents

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                         nginx                            │
│              (SSL, Rate Limiting, Caching)               │
└─────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────┐
│                    Flask Application                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   ChatBot    │  │  HealthBench │  │   Langfuse   │  │
│  │   Handler    │  │  Evaluator   │  │   Tracker    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│           │                 │                 │          │
│           └─────────────────┴─────────────────┘          │
│                            │                             │
│  ┌─────────────────────────┴──────────────────────────┐ │
│  │                  RAG System                         │ │
│  │  (ChromaDB + Question Book Retrieval)              │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                            │
          ┌─────────────────┴─────────────────┐
          ↓                                   ↓
┌──────────────────┐                 ┌─────────────────┐
│    MongoDB       │                 │  OpenAI API     │
│  (Conversations) │                 │   (GPT-4)       │
└──────────────────┘                 └─────────────────┘
```

## 📡 API Endpoints

### Chat Endpoints

- `POST /chat/stream` - Stream chat responses (SSE)
- `POST /chat` - Regular chat endpoint
- `GET /chat/session/<session_id>` - Get session history

### Voice Endpoints (if enabled)

- `POST /voice/stt` - Speech to text
- `POST /voice/tts` - Text to speech

### Evaluation Endpoints

- `GET /healthbench/dashboard` - HealthBench dashboard
- `GET /healthbench/results` - Get evaluation results
- `POST /healthbench/evaluate` - Trigger evaluation

### Utility Endpoints

- `GET /health` - Health check
- `GET /index.html` - Chatbot UI
- `GET /` - Root redirect

## 📊 Monitoring & Logs

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

### Monitor Resources

```bash
# Container stats
docker stats

# Service status
docker-compose ps

# MongoDB status
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"
```

### Langfuse Dashboard

If Langfuse is enabled:
1. Go to https://cloud.langfuse.com (or your self-hosted instance)
2. View conversation traces, token usage, and latency metrics
3. Analyze evaluation scores and quality metrics

## 🔧 Troubleshooting

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
sudo chown -R $USER:$USER .
chmod +x deploy.sh

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

### OpenAI API Errors

```bash
# Check API key is set
docker-compose exec hyoda-app env | grep OPENAI_API_KEY

# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Reset Everything

```bash
# Stop and remove all containers
docker-compose down -v

# Remove Docker images
docker-compose down --rmi all

# Clean rebuild
./deploy.sh --build
```

## 🔄 Maintenance

### Update Application

```bash
# Pull latest code
git pull origin SUditya

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Backup Data

```bash
# Backup MongoDB
docker-compose exec mongodb mongodump --out=/tmp/backup
docker cp hyoda-mongodb:/tmp/backup ./mongodb_backup

# Backup ChromaDB
tar -czf chroma_backup.tar.gz chroma_db/

# Backup environment
cp .env .env.backup
```

### Clean Up

```bash
# Remove old containers
docker system prune -a

# Remove unused volumes
docker volume prune
```

## 📝 Development

### Local Development (Without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Run Flask app
python app.py

# In another terminal, serve frontend
python serve.py

# Access at http://localhost:8000
```

### Run Tests

```bash
# Run all tests
python -m pytest

# Specific test files
python test_healthbench_integration.py
python test_mongodb.py
python test_safety_scoring.py
```

## 📄 License

Copyright © 2024 HealthYoda Team. All rights reserved.

## 🤝 Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review logs: `docker-compose logs -f`
3. Open an issue on GitHub

---

**Made with ❤️ for better healthcare AI**

