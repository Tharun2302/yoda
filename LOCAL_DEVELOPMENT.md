# Local Development with Remote Ollama

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│  Server (68.183.88.5)                                   │
│  ┌─────────────────────────────────────────────┐       │
│  │  Docker Network                              │       │
│  │  ┌──────────┐    ┌─────────┐                │       │
│  │  │ App      │───→│ Ollama  │                │       │
│  │  │ :8002    │    │ :11434  │                │       │
│  │  └──────────┘    └─────────┘                │       │
│  │       ↑               ↑                      │       │
│  └───────│───────────────│──────────────────────┘       │
│          │               │                              │
└──────────│───────────────│──────────────────────────────┘
           │               │
           │               └─────────────────────┐
           │                                     │
    ┌──────▼───────────────────────────────────────────┐
    │  Your Local Machine                              │
    │  - Access App: http://68.183.88.5:8002          │
    │  - Access Ollama: http://68.183.88.5:11434      │
    └──────────────────────────────────────────────────┘
```

## Using Ollama from Local Machine

### Option 1: Access Remote Ollama Directly

Set your local environment to use the remote Ollama:

```bash
# On your local machine
export OLLAMA_BASE_URL=http://68.183.88.5:11434
export OLLAMA_MODEL=alibayram/medgemma:4b
export OLLAMA_API_KEY=ollama
```

### Option 2: Test with cURL

```bash
# Test from your local machine
curl http://68.183.88.5:11434/api/tags

# Test chat
curl -X POST http://68.183.88.5:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "alibayram/medgemma:4b",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": false
  }'
```

### Option 3: Run Local App with Remote Ollama

Create a `.env.local` file:

```env
OLLAMA_BASE_URL=http://68.183.88.5:11434
OLLAMA_MODEL=alibayram/medgemma:4b
OLLAMA_API_KEY=ollama
ALLOWED_ORIGINS=http://localhost:8002,http://127.0.0.1:8002
```

Then run locally:

```bash
# On your local machine
python app_ollama.py
```

## Python SDK Example

```python
import httpx
import json

# Configure to use remote Ollama
OLLAMA_URL = "http://68.183.88.5:11434"
MODEL = "alibayram/medgemma:4b"

client = httpx.Client(base_url=OLLAMA_URL, timeout=60.0)

# Send a chat request
response = client.post("/api/chat", json={
    "model": MODEL,
    "messages": [
        {"role": "user", "content": "What is diabetes?"}
    ],
    "stream": False
})

result = response.json()
print(result["message"]["content"])
```

## JavaScript/Node.js Example

```javascript
const OLLAMA_URL = "http://68.183.88.5:11434";
const MODEL = "alibayram/medgemma:4b";

async function chat(message) {
  const response = await fetch(`${OLLAMA_URL}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: MODEL,
      messages: [{ role: 'user', content: message }],
      stream: false
    })
  });
  
  const data = await response.json();
  return data.message.content;
}

// Usage
chat("What is hypertension?").then(console.log);
```

## Troubleshooting

### Can't Connect from Local Machine

```bash
# On server, check if port is exposed
docker ps | grep ollama

# Should show: 0.0.0.0:11434->11434/tcp

# Check firewall
sudo ufw status
sudo ufw allow 11434/tcp

# Test from server
curl http://localhost:11434/api/tags

# Test from local machine
curl http://68.183.88.5:11434/api/tags
```

### Timeout Issues

Increase timeout in your local code:

```python
client = httpx.Client(base_url=OLLAMA_URL, timeout=120.0)
```

### Model Not Responding

Check if model is loaded on server:

```bash
ssh root@68.183.88.5
docker exec yoda-ollama ollama list
```

## Environment Variables Summary

### Server (Docker) - Use Internal Hostname
```env
OLLAMA_BASE_URL=http://ollama:11434
```

### Local Development - Use Server IP
```env
OLLAMA_BASE_URL=http://68.183.88.5:11434
```

Both configurations work with the same `OLLAMA_API_KEY=ollama`!

## Security Note

⚠️ **Production Warning**: Exposing Ollama publicly (port 11434) means anyone can use your model. Consider:

1. **Add authentication** (nginx reverse proxy with auth)
2. **Use VPN** for secure access
3. **Firewall rules** to restrict IPs
4. **Rate limiting** to prevent abuse

For production, use nginx as a reverse proxy:

```nginx
location /ollama/ {
    proxy_pass http://ollama:11434/;
    # Add authentication here
}
```

