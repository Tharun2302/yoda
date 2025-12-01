# Testing Deployment Scenario Locally

## Step-by-Step Instructions

### Step 1: Start Flask Backend Server

Open **Terminal 1** and run:

```bash
python app.py
```

Wait until you see:
```
* Running on http://127.0.0.1:8002
```

**Keep this terminal open!**

---

### Step 2: Start Deployment Test Server

Open **Terminal 2** (new terminal window) and run:

**Windows:**
```bash
test_deployment_scenario.bat
```

**Or directly:**
```bash
python test_deployment_scenario.py
```

You'll see output like:
```
============================================================
DEPLOYMENT SCENARIO TEST SERVER
============================================================

⚠️  This server runs on HTTP (not HTTPS) to simulate deployment
   This will trigger getUserMedia security errors

📡 Server running on:
   http://192.168.1.100:8003/index.html
   http://127.0.0.1:8003/index.html
```

**Keep this terminal open too!**

---

### Step 3: Test in Browser

1. **Open your browser**
2. **Go to the URL shown** (use the IP address one, NOT 127.0.0.1):
   - Example: `http://192.168.1.100:8003/index.html`
   - **Important:** Use the IP address (not localhost) to simulate deployment

3. **Test the Voice Feature:**
   - Click the "Voice On" button
   - You should see an alert: **"Voice mode requires a secure connection (HTTPS) or localhost"**
   - This is the expected behavior in deployment (HTTP environment)

---

## What This Tests

✅ **getUserMedia error handling** - Catches the error gracefully instead of crashing  
✅ **HTTP (non-secure) scenario** - Simulates deployment environment  
✅ **Proper error messages** - Shows user-friendly messages  

---

## Expected Results

### ✅ Success (Fixed Version):
- Click "Voice On" → See alert: "Voice mode requires a secure connection (HTTPS)"
- No console errors about "Cannot read properties of undefined"
- App continues to work normally (just voice is disabled)

### ❌ Failure (Old Version):
- Click "Voice On" → Console error: "Cannot read properties of undefined (reading 'getUserMedia')"
- App might crash or behave unexpectedly

---

## Troubleshooting

**If API calls fail:**
- Make sure Flask backend (Terminal 1) is still running
- Check that it's on port 8002
- The test server proxies API calls to the backend

**If you don't see the error:**
- Make sure you're accessing via the **IP address** (not 127.0.0.1)
- Example: `http://192.168.1.100:8003/index.html` ✅
- NOT: `http://127.0.0.1:8003/index.html` ❌ (this is localhost, so it works)

**To stop:**
- Press `Ctrl+C` in both terminals

