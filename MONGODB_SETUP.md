# MongoDB Setup Guide for HealthYoda

**Quick Setup Instructions**

---

## Option 1: MongoDB Atlas (Cloud - Recommended for Quick Start) ⭐

**Best for:** Quick setup, no local installation needed, free tier available

### Steps:

1. **Create MongoDB Atlas Account**
   - Go to https://www.mongodb.com/cloud/atlas/register
   - Sign up for free (M0 Free Tier available)

2. **Create a Cluster**
   - Click "Create Cluster"
   - Choose "M0 Free" tier
   - Select a cloud provider and region (closest to you)
   - Click "Create Cluster" (takes 3-5 minutes)

3. **Create Database User**
   - Go to "Database Access" → "Add New Database User"
   - Username: `healthyoda` (or your choice)
   - Password: Create a strong password (save it!)
   - Database User Privileges: "Atlas admin" or "Read and write to any database"
   - Click "Add User"

4. **Whitelist Your IP**
   - Go to "Network Access" → "Add IP Address"
   - Click "Add Current IP Address" (for development)
   - Or add `0.0.0.0/0` for all IPs (less secure, but easier for testing)

5. **Get Connection String**
   - Go to "Database" → "Connect"
   - Choose "Connect your application"
   - Copy the connection string (looks like: `mongodb+srv://username:password@cluster.mongodb.net/`)
   - Replace `<password>` with your actual password
   - Replace `<dbname>` with `healthyoda` (or remove it)

6. **Add to .env file**
   ```bash
   MONGODB_URI=mongodb+srv://healthyoda:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/healthyoda?retryWrites=true&w=majority
   MONGODB_DB=healthyoda
   ```

---

## Option 2: Local MongoDB Installation

**Best for:** Development, offline work, full control

### Windows Installation:

1. **Download MongoDB**
   - Go to https://www.mongodb.com/try/download/community
   - Select: Windows, MSI, Latest version
   - Download and run installer

2. **Install MongoDB**
   - Choose "Complete" installation
   - Install as Windows Service (recommended)
   - Install MongoDB Compass (GUI tool - optional but helpful)

3. **Verify Installation**
   ```powershell
   # Check if MongoDB is running
   Get-Service MongoDB
   
   # Should show "Running"
   ```

4. **Add to .env file**
   ```bash
   MONGODB_URI=mongodb://localhost:27017/
   MONGODB_DB=healthyoda
   ```

### Mac Installation:

```bash
# Using Homebrew
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community

# Verify
brew services list
```

### Linux Installation:

```bash
# Ubuntu/Debian
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod
```

---

## Setup Steps (After MongoDB is Running)

### 1. Install Python Package

```bash
pip install pymongo>=4.6.0
```

Or if using requirements.txt:
```bash
pip install -r requirements.txt
```

### 2. Create .env File

Create a `.env` file in your project root:

```bash
# OpenAI API Key
OPENAI_API_KEY=sk-your-openai-key-here

# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB=healthyoda

# For MongoDB Atlas (cloud):
# MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/healthyoda?retryWrites=true&w=majority
```

### 3. Test Connection

Run your Flask app:
```bash
python app.py
```

**Look for this message:**
```
✅ MongoDB connected: healthyoda
```

**If you see:**
```
⚠️  MongoDB connection failed: ...
```
- Check if MongoDB is running (local) or connection string is correct (Atlas)
- Verify `.env` file has correct `MONGODB_URI`

---

## Quick Test Script

Create `test_mongodb.py` to test connection:

```python
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
mongodb_db_name = os.getenv('MONGODB_DB', 'healthyoda')

try:
    client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    db = client[mongodb_db_name]
    print(f"✅ MongoDB connected successfully!")
    print(f"   Database: {mongodb_db_name}")
    print(f"   Collections: {db.list_collection_names()}")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
```

Run it:
```bash
python test_mongodb.py
```

---

## Verification

After setup, when you run `python app.py`, you should see:

```
Starting HealthYoda chatbot server...
Server will run on http://127.0.0.1:8002
--------------------------------------------------
✅ OpenAI API key found!
✅ Langfuse configured! Traces will be logged.
✅ MongoDB connected! Session data will be persisted.
   Database: healthyoda
   Collection: patient_sessions
--------------------------------------------------
```

---

## Troubleshooting

### "MongoDB connection failed"

**Local MongoDB:**
- Check if MongoDB service is running: `Get-Service MongoDB` (Windows) or `brew services list` (Mac)
- Start MongoDB: `net start MongoDB` (Windows) or `brew services start mongodb-community` (Mac)
- Check if port 27017 is available

**MongoDB Atlas:**
- Verify IP is whitelisted in Network Access
- Check username/password in connection string
- Verify cluster is running (not paused)

### "pymongo not installed"

```bash
pip install pymongo>=4.6.0
```

### Connection String Format

**Local:**
```
MONGODB_URI=mongodb://localhost:27017/
```

**Atlas:**
```
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/dbname?retryWrites=true&w=majority
```

**With Authentication (Local):**
```
MONGODB_URI=mongodb://username:password@localhost:27017/
```

---

## What Happens After Setup

1. **First Chat Session:**
   - MongoDB creates a new document with `session_id`
   - Data starts getting stored

2. **Subsequent Questions:**
   - Bot checks MongoDB before asking
   - Skips questions if data already collected
   - Stores new data as user responds

3. **View Data:**
   - Use MongoDB Compass (GUI) to browse data
   - Or use API: `GET /session/<session_id>/data`

---

## Recommended: MongoDB Compass (GUI Tool)

Download from: https://www.mongodb.com/products/compass

- Visual database browser
- See your data in real-time
- Easy to query and explore
- Free and included with MongoDB

**Connect with:**
- Local: `mongodb://localhost:27017/`
- Atlas: Your connection string from Atlas

---

## Summary

**Quickest Setup (5 minutes):**
1. Sign up for MongoDB Atlas (free)
2. Create cluster
3. Get connection string
4. Add to `.env` file
5. Run `pip install pymongo`
6. Start app - done! ✅

**That's it!** Your bot will now:
- Store data in MongoDB
- Prevent duplicate questions
- Persist data across server restarts

