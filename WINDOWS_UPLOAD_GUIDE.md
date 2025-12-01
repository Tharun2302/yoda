# 🪟 Uploading HYoda to Digital Ocean from Windows

## Quick Guide for Windows Users

### Method 1: Using PowerShell SCP (Recommended)

1. **Open PowerShell as Administrator**

2. **Navigate to your project folder:**
```powershell
cd "C:\Users\TharunP\OneDrive - CloudFuze, Inc\Desktop\Evals"
```

3. **Upload the entire HYoda folder:**
```powershell
scp -r HYoda root@167.71.238.114:/opt/hyoda
```

4. **Enter your server password when prompted**

---

### Method 2: Using WinSCP (Easiest for Beginners)

1. **Download WinSCP**: https://winscp.net/eng/download.php

2. **Install and open WinSCP**

3. **Create new connection:**
   - File Protocol: `SCP`
   - Host name: `167.71.238.114`
   - Port: `22`
   - User name: `root`
   - Password: `<your-server-password>`

4. **Click "Login"**

5. **Navigate to `/opt/` on the remote side (right panel)**

6. **Drag and drop the `HYoda` folder from your PC (left panel) to `/opt/` (right panel)**

7. **Wait for upload to complete**

---

### Method 3: Using FileZilla

1. **Download FileZilla**: https://filezilla-project.org/

2. **Open FileZilla**

3. **Quick Connect:**
   - Host: `sftp://167.71.238.114`
   - Username: `root`
   - Password: `<your-server-password>`
   - Port: `22`

4. **Click "Quickconnect"**

5. **Navigate to `/opt/` on remote server (right panel)**

6. **Drag and drop `HYoda` folder from local to remote**

---

### Method 4: Using Git (If You Have a Repository)

If your code is in a Git repository (GitHub, GitLab, Bitbucket):

1. **SSH into your server:**
```powershell
ssh root@167.71.238.114
```

2. **Clone your repository:**
```bash
cd /opt
git clone https://github.com/yourusername/hyoda.git hyoda
cd hyoda
```

---

## After Upload: Deployment Steps

Once files are uploaded, SSH into your server and run:

```powershell
# Connect to server
ssh root@167.71.238.114
```

Then on the server:

```bash
# 1. Navigate to project
cd /opt/hyoda

# 2. Install Docker (if not installed)
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# 3. Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# 4. Create environment file
cp env.template .env

# 5. Edit environment file (add your OpenAI API key)
nano .env

# Add this line:
# OPENAI_API_KEY=sk-your-actual-openai-key-here
# Save with Ctrl+X, then Y, then Enter

# 6. Make deploy script executable
chmod +x deploy.sh

# 7. Run deployment
./deploy.sh
```

---

## Verify Upload Worked

After upload, SSH into server and check:

```bash
ssh root@167.71.238.114

# Check if folder exists
ls -la /opt/hyoda

# Check if required files exist
ls -la /opt/hyoda/docker-compose.yml
ls -la /opt/hyoda/Dockerfile
ls -la /opt/hyoda/app.py
ls -la /opt/hyoda/docx/
```

You should see all your project files listed!

---

## Common Windows Issues

### Issue: "scp: command not found"

**Solution**: Windows 10/11 has OpenSSH built-in, but may need to be enabled:

1. Open "Settings" → "Apps" → "Optional Features"
2. Click "Add a feature"
3. Find "OpenSSH Client" and install it
4. Restart PowerShell

**Alternative**: Use WinSCP or FileZilla instead

### Issue: Permission Denied

**Solution**: Make sure you're using the correct:
- Server IP: `167.71.238.114`
- Username: `root` (or your server username)
- Correct password/SSH key

### Issue: Host Key Verification Failed

**Solution**: First time connecting? Accept the fingerprint:
```powershell
# This will prompt you to accept the server's fingerprint
ssh root@167.71.238.114
# Type 'yes' when prompted
# Then exit
# Now try the scp command again
```

### Issue: Upload Interrupted/Failed

**Solution**: Resume the upload:
```powershell
# Re-run the scp command - it will skip already uploaded files
scp -r HYoda root@167.71.238.114:/opt/hyoda
```

---

## File Size Warnings

The upload might take a few minutes depending on:
- Your internet speed
- Size of `chroma_db/` folder (vector database)
- Size of `Helm/` folder (if present)

**To speed up uploads**, you can exclude certain folders:

```powershell
# Create a temporary copy without heavy folders
robocopy HYoda HYoda-upload /E /XD __pycache__ .git chroma_db Helm

# Upload the lighter version
scp -r HYoda-upload root@167.71.238.114:/opt/hyoda
```

---

## Quick Reference Card

```
┌─────────────────────────────────────────────┐
│  WINDOWS → DIGITAL OCEAN DEPLOYMENT         │
├─────────────────────────────────────────────┤
│                                             │
│  1. Upload Files:                           │
│     WinSCP or PowerShell SCP                │
│                                             │
│  2. SSH Into Server:                        │
│     ssh root@167.71.238.114                 │
│                                             │
│  3. Run Commands:                           │
│     cd /opt/hyoda                           │
│     cp env.template .env                    │
│     nano .env (add API key)                 │
│     chmod +x deploy.sh                      │
│     ./deploy.sh                             │
│                                             │
│  4. Access App:                             │
│     http://167.71.238.114                   │
│                                             │
└─────────────────────────────────────────────┘
```

---

## Need Help?

1. Check if server is accessible: `ping 167.71.238.114`
2. Test SSH connection: `ssh root@167.71.238.114`
3. Verify files uploaded: `ssh root@167.71.238.114 "ls -la /opt/hyoda"`
4. Check deployment logs: `ssh root@167.71.238.114 "cd /opt/hyoda && docker-compose logs"`

---

**Windows Version Tested**: Windows 10/11
**PowerShell Version**: 5.1+
**Upload Methods Tested**: ✅ SCP, ✅ WinSCP, ✅ FileZilla

