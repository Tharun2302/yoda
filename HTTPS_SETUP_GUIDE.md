# HTTPS Setup Guide for IP Address

This guide shows how to set up HTTPS for your IP address `167.71.238.114` using a self-signed certificate.

## ⚠️ Important Notes

- **Self-signed certificates** will show a browser security warning (this is normal and safe)
- Users will need to click "Advanced" → "Proceed to site" the first time
- This is perfect for development/testing and internal use
- For production with real users, consider getting a domain name and using Let's Encrypt

## Step 1: Generate SSL Certificate

### On Linux/Mac (or WSL/Git Bash on Windows):

```bash
chmod +x generate_ssl_cert.sh
./generate_ssl_cert.sh
```

### On Windows (PowerShell/CMD):

```bash
generate_ssl_cert.bat
```

**Or manually with OpenSSL:**

```bash
# Create ssl directory
mkdir ssl

# Generate private key
openssl genrsa -out ssl/key.pem 2048

# Generate certificate with IP address
openssl req -new -x509 -key ssl/key.pem -out ssl/cert.pem -days 365 \
  -subj "/CN=167.71.238.114" \
  -addext "subjectAltName=IP:167.71.238.114"
```

## Step 2: Verify Certificate Files

After generation, you should have:
- `ssl/cert.pem` - Certificate file
- `ssl/key.pem` - Private key file

Verify they exist:
```bash
ls -la ssl/
```

## Step 3: Deploy to Server

### Option A: Using SCP/SFTP

```bash
# Copy SSL files to server
scp ssl/cert.pem ssl/key.pem user@167.71.238.114:/path/to/HYoda-1/ssl/
```

### Option B: Using Git (if ssl/ is in .gitignore)

```bash
# On server, generate directly
ssh user@167.71.238.114
cd /path/to/HYoda-1
./generate_ssl_cert.sh
```

## Step 4: Update Configuration

The `nginx.conf` has already been updated to:
- ✅ Redirect HTTP (port 80) → HTTPS (port 443)
- ✅ Use SSL certificate from `ssl/cert.pem` and `ssl/key.pem`
- ✅ Configure secure SSL protocols and ciphers

The `docker-compose.yml` already mounts the `ssl/` directory.

## Step 5: Restart Services

```bash
# On your server
cd /path/to/HYoda-1
docker-compose restart nginx
```

Or rebuild if needed:
```bash
docker-compose up -d --build
```

## Step 6: Test HTTPS

1. **Access your site:**
   ```
   https://167.71.238.114
   ```

2. **Browser Security Warning:**
   - You'll see: "Your connection is not private" or "NET::ERR_CERT_AUTHORITY_INVALID"
   - This is **normal** for self-signed certificates
   - Click **"Advanced"** → **"Proceed to 167.71.238.114 (unsafe)"**

3. **Verify HTTPS is working:**
   - Check the address bar shows 🔒 (lock icon)
   - URL should be `https://167.71.238.114`
   - Voice features should now work!

## Step 7: Update Frontend (if needed)

The frontend will automatically detect HTTPS and use it. The `getApiBase()` function in `index.html` will use the current protocol.

## Troubleshooting

### Certificate not found error:
```bash
# Check if files exist
ls -la ssl/

# Check permissions
chmod 644 ssl/cert.pem
chmod 600 ssl/key.pem
```

### Nginx can't read certificate:
```bash
# Check docker volume mount
docker-compose config

# Check file permissions inside container
docker-compose exec nginx ls -la /etc/nginx/ssl/
```

### Port 443 not accessible:
```bash
# Check firewall
sudo ufw status
sudo ufw allow 443/tcp

# Check if port is open
sudo netstat -tulpn | grep 443
```

### Still getting HTTP instead of HTTPS:
- Clear browser cache
- Try incognito/private mode
- Check nginx logs: `docker-compose logs nginx`

## Security Considerations

1. **Self-signed certificates are fine for:**
   - Development/testing
   - Internal tools
   - Personal projects

2. **For production with real users:**
   - Get a domain name (e.g., `yourdomain.com`)
   - Use Let's Encrypt (free SSL)
   - Or use a commercial SSL certificate

3. **Current setup provides:**
   - ✅ Encrypted connection (HTTPS)
   - ✅ getUserMedia support (secure context)
   - ✅ Voice features enabled
   - ⚠️ Browser warning (expected with self-signed)

## Next Steps

Once HTTPS is working:
1. ✅ Voice features will work
2. ✅ getUserMedia will be available
3. ✅ All API calls will be encrypted
4. ✅ Better security overall

## Getting a Domain (Optional - Future)

When you're ready for a real domain:
1. Register domain (e.g., Namecheap, Google Domains)
2. Point DNS to your IP: `167.71.238.114`
3. Use Let's Encrypt:
   ```bash
   sudo certbot certonly --standalone -d yourdomain.com
   ```
4. Update nginx.conf to use Let's Encrypt certificates

---

**You're all set!** 🎉 Your site will now work with HTTPS and voice features will be enabled.

