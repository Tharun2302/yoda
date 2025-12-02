# Yoda Deployment Options

## Available Docker Compose Configurations

### 1. **docker-compose.ollama.yml** (Recommended for Quick Setup)

**Use Case**: Quick deployment with direct port access

**Features**:
- ✅ Ollama with Medgemma model
- ✅ Application on port 8002
- ✅ MongoDB for session storage
- ✅ Direct HTTP access (no SSL)

**Pros**:
- Simple and fast setup
- Direct port access (good for testing)
- No SSL certificate needed

**Cons**:
- No HTTPS/SSL encryption
- No nginx reverse proxy
- Suitable for development/testing only

**Deploy Command**:
```bash
docker-compose -f docker-compose.ollama.yml up -d
```

**Access**:
- App: http://68.183.88.5:8002
- Ollama: http://68.183.88.5:11434

---

### 2. **docker-compose.ollama-with-nginx.yml** (Recommended for Production)

**Use Case**: Production deployment with SSL and reverse proxy

**Features**:
- ✅ Ollama with Medgemma model
- ✅ Application on port 8002
- ✅ MongoDB for session storage
- ✅ Nginx reverse proxy with SSL support
- ✅ HTTPS encryption

**Pros**:
- Production-ready with SSL
- Nginx handles HTTPS/SSL
- Better security
- Can add authentication at nginx level

**Cons**:
- Requires SSL certificate setup
- More complex configuration

**Deploy Command**:
```bash
# First, generate SSL certificates (see SSL_SETUP.md)
docker-compose -f docker-compose.ollama-with-nginx.yml up -d
```

**Access**:
- App: https://68.183.88.5 (through nginx)
- Direct: http://68.183.88.5:8002 (if port open)
- Ollama: http://68.183.88.5:11434

---

### 3. **docker-compose.yml** (OpenAI Version - Original)

**Use Case**: If you want to use OpenAI instead of Ollama

**Features**:
- ✅ OpenAI API integration
- ✅ Application on port 8002
- ✅ MongoDB for session storage
- ✅ Nginx with SSL
- ❌ No Ollama (uses OpenAI instead)

**Requires**:
- OpenAI API key
- SSL certificates

**Deploy Command**:
```bash
# Set OPENAI_API_KEY in .env first
docker-compose up -d
```

---

## Comparison Matrix

| Feature | ollama.yml | ollama-with-nginx.yml | OpenAI (yml) |
|---------|-----------|----------------------|--------------|
| Local LLM (Ollama) | ✅ | ✅ | ❌ |
| Medgemma Model | ✅ | ✅ | ❌ |
| OpenAI API | ❌ | ❌ | ✅ |
| Nginx Reverse Proxy | ❌ | ✅ | ✅ |
| HTTPS/SSL Support | ❌ | ✅ | ✅ |
| MongoDB | ✅ | ✅ | ✅ |
| Direct Port Access | ✅ | ✅ | ✅ |
| Setup Complexity | Low | Medium | Medium |
| Cost | Free (local) | Free (local) | $$ (OpenAI) |

---

## Recommended Deployment Path

### Development/Testing:
```bash
# Use simple Ollama setup
docker-compose -f docker-compose.ollama.yml up -d
```

### Production:
```bash
# Use Ollama with nginx and SSL
docker-compose -f docker-compose.ollama-with-nginx.yml up -d
```

---

## Configuration Differences

### Internal Docker Network (All versions):
```env
# Containers communicate using Docker network hostnames
OLLAMA_BASE_URL=http://ollama:11434  # ✅ Internal (fast)
MONGODB_URI=mongodb://mongodb:27017/  # ✅ Internal (fast)
```

### External Access:
```env
# Access from your local machine
OLLAMA_BASE_URL=http://68.183.88.5:11434  # ✅ External
App: http://68.183.88.5:8002              # ✅ Direct
App: https://68.183.88.5                  # ✅ Through nginx (if using nginx version)
```

---

## Quick Start Commands

### 1. Deploy Simple Ollama (No SSL)
```bash
cd /opt/yoda
git pull origin main
docker-compose -f docker-compose.ollama.yml down
docker-compose -f docker-compose.ollama.yml up -d --build
sleep 30
docker exec yoda-ollama ollama list
curl http://localhost:8002/health
```

### 2. Deploy with Nginx and SSL
```bash
cd /opt/yoda
git pull origin main

# Generate SSL certificate first (self-signed for testing)
mkdir -p ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/key.pem -out ssl/cert.pem \
  -subj "/C=US/ST=State/L=City/O=Org/CN=68.183.88.5"

# Deploy
docker-compose -f docker-compose.ollama-with-nginx.yml down
docker-compose -f docker-compose.ollama-with-nginx.yml up -d --build
sleep 30
curl https://68.183.88.5 --insecure
```

### 3. Switch from OpenAI to Ollama
```bash
cd /opt/yoda
git pull origin main

# Stop OpenAI version
docker-compose down

# Start Ollama version
docker-compose -f docker-compose.ollama.yml up -d
sleep 30
docker exec yoda-ollama ollama pull alibayram/medgemma:4b
```

---

## Troubleshooting

### Port Already in Use
```bash
# Check what's using the port
sudo lsof -i :8002
sudo lsof -i :11434

# Stop conflicting services
docker-compose down  # Stops all versions
```

### Ollama Model Not Loaded
```bash
# Pull the model
docker exec yoda-ollama ollama pull alibayram/medgemma:4b

# List available models
docker exec yoda-ollama ollama list

# Test model
docker exec yoda-ollama ollama run alibayram/medgemma:4b "Hello"
```

### SSL Certificate Issues (nginx version)
```bash
# Generate self-signed certificate
mkdir -p ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/key.pem -out ssl/cert.pem \
  -subj "/C=US/ST=State/L=City/O=Org/CN=68.183.88.5"

# For production, use Let's Encrypt
# See SSL_SETUP.md
```

---

## Environment Variables

All versions support these common variables in `.env`:

```env
# Ollama Configuration (ollama versions only)
OLLAMA_MODEL=alibayram/medgemma:4b
OLLAMA_API_KEY=ollama

# OpenAI Configuration (OpenAI version only)
OPENAI_API_KEY=sk-...

# MongoDB
MONGODB_URI=mongodb://mongodb:27017/
MONGODB_DB=healthyoda

# CORS
ALLOWED_ORIGINS=http://68.183.88.5,http://68.183.88.5:8002

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600

# Langfuse (optional)
LANGFUSE_ENABLED=false
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
```

---

## Summary

- **Quick Testing**: Use `docker-compose.ollama.yml`
- **Production**: Use `docker-compose.ollama-with-nginx.yml` with proper SSL
- **OpenAI**: Use `docker-compose.yml` if you prefer OpenAI over local Ollama

Choose based on your needs! 🚀

