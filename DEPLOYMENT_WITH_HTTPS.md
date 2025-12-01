# Deployment Guide with HTTPS

## Quick Deployment Steps

### 1. Push to Git (Normal Process)

```bash
git add .
git commit -m "Add HTTPS support with self-signed certificate"
git push origin main
```

**Note:** SSL certificates (`ssl/*.pem`) are already in `.gitignore`, so they won't be committed. This is correct - certificates should be generated on the server.

---

### 2. On Your Server (167.71.238.114)

#### Step 1: Pull Latest Code

```bash
cd /path/to/HYoda-1
git pull origin main
```

#### Step 2: Generate SSL Certificate (First Time Only)

```bash
# Make script executable
chmod +x generate_ssl_cert.sh

# Generate certificate
./generate_ssl_cert.sh
```

This creates:
- `ssl/cert.pem` - SSL certificate
- `ssl/key.pem` - Private key

**Important:** Only do this once. The certificate is valid for 365 days.

#### Step 3: Verify SSL Files Exist

```bash
ls -la ssl/
# Should show:
# - cert.pem
# - key.pem
```

#### Step 4: Deploy (Normal Process)

```bash
# Option A: Use deploy script
./deploy.sh

# Option B: Manual deployment
docker-compose down
docker-compose build
docker-compose up -d
```

#### Step 5: Verify HTTPS is Working

1. **Check nginx is running:**
   ```bash
   docker-compose ps
   ```

2. **Test HTTP redirect:**
   ```bash
   curl -I http://167.71.238.114
   # Should show: HTTP/1.1 301 Moved Permanently
   # Location: https://167.71.238.114
   ```

3. **Test HTTPS:**
   ```bash
   curl -k https://167.71.238.114/health
   # -k flag ignores self-signed cert warning
   ```

4. **Open in browser:**
   - Go to: `https://167.71.238.114`
   - Accept the security warning (click "Advanced" → "Proceed")
   - Voice features should now work!

---

## What Changed?

### Files Modified:
- ✅ `nginx.conf` - Added HTTPS server block, HTTP→HTTPS redirect
- ✅ `app.py` - Added HTTPS to CORS and CSP headers
- ✅ `docker-compose.yml` - Added HTTPS to allowed origins

### Files Added:
- ✅ `generate_ssl_cert.sh` - SSL certificate generation script
- ✅ `generate_ssl_cert.bat` - Windows version
- ✅ `HTTPS_SETUP_GUIDE.md` - Detailed setup guide

### Files NOT Committed (by design):
- ❌ `ssl/cert.pem` - Generated on server
- ❌ `ssl/key.pem` - Generated on server

---

## Subsequent Deployments

After the first HTTPS setup, future deployments are normal:

```bash
# On server
git pull origin main
./deploy.sh
# OR
docker-compose restart
```

**No need to regenerate SSL certificate** - it's valid for 365 days.

---

## Troubleshooting

### Certificate Missing Error

If you see: `SSL: certificate not found`

```bash
# Regenerate certificate
./generate_ssl_cert.sh

# Restart nginx
docker-compose restart nginx
```

### Port 443 Not Accessible

```bash
# Check firewall
sudo ufw status
sudo ufw allow 443/tcp

# Check if port is listening
sudo netstat -tulpn | grep 443
```

### Nginx Can't Read Certificate

```bash
# Check file permissions
chmod 644 ssl/cert.pem
chmod 600 ssl/key.pem

# Check docker volume mount
docker-compose exec nginx ls -la /etc/nginx/ssl/
```

### Still Getting HTTP Instead of HTTPS

1. Clear browser cache
2. Try incognito/private mode
3. Check nginx logs: `docker-compose logs nginx`
4. Verify redirect is working: `curl -I http://167.71.238.114`

---

## Summary

✅ **Push to Git:** Normal process (SSL files are ignored)  
✅ **On Server:** Pull code, generate SSL (first time), deploy  
✅ **Result:** HTTPS enabled, voice features work!

The deployment process is the same, just with one extra step (SSL generation) the first time.

