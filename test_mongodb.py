"""
Quick MongoDB Connection Test Script
Run this to verify your MongoDB connection is working.
"""
import sys
import os

# Fix Windows console encoding for emoji
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from dotenv import load_dotenv

load_dotenv()

mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
mongodb_db_name = os.getenv('MONGODB_DB', 'healthyoda')

print("Testing MongoDB connection...")
# Mask password in URI for display
display_uri = mongodb_uri
if '@' in mongodb_uri:
    # Hide password: mongodb+srv://user:***@cluster...
    parts = mongodb_uri.split('@')
    if len(parts) == 2:
        user_part = parts[0].split('://')
        if len(user_part) == 2:
            display_uri = f"{user_part[0]}://***:***@{parts[1]}"
print(f"URI: {display_uri}")
print(f"Database: {mongodb_db_name}")
print("-" * 50)

try:
    client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
    # Test connection
    client.admin.command('ping')
    print("[OK] MongoDB connection successful!")
    
    # Get database
    db = client[mongodb_db_name]
    collections = db.list_collection_names()
    
    print(f"\nDatabase: {mongodb_db_name}")
    print(f"Collections: {collections if collections else 'None (will be created automatically)'}")
    
    # Test patient_sessions collection
    patient_sessions = db['patient_sessions']
    count = patient_sessions.count_documents({})
    print(f"\nPatient Sessions: {count} document(s)")
    
    if count > 0:
        # Show one example
        example = patient_sessions.find_one()
        print(f"\nExample session:")
        print(f"  Session ID: {example.get('session_id', 'N/A')}")
        print(f"  Complaint: {example.get('complaint_name', 'None')}")
        print(f"  Created: {example.get('created_at', 'N/A')}")
    
    print("\n[OK] MongoDB is ready to use!")
    
except ConnectionFailure as e:
    print(f"[ERROR] MongoDB connection failed: {e}")
    print("\nTroubleshooting:")
    print("1. Check if MongoDB is running (local) or connection string is correct (Atlas)")
    print("2. Verify MONGODB_URI in .env file")
    print("3. For Atlas: Check IP whitelist and credentials")
except ServerSelectionTimeoutError as e:
    print(f"[ERROR] MongoDB server not reachable")
    print(f"Details: {str(e)[:200]}")
    print("\nTroubleshooting:")
    print("1. LOCAL MongoDB:")
    print("   - Check if MongoDB service is running")
    print("   - Windows: Open Services, find 'MongoDB', start it")
    print("   - Or install MongoDB: https://www.mongodb.com/try/download/community")
    print("\n2. MongoDB Atlas (Cloud):")
    print("   - Verify connection string in .env")
    print("   - Check IP whitelist in Atlas dashboard")
    print("   - Verify username/password are correct")
    print("\n3. Quick Fix - Use MongoDB Atlas (Free):")
    print("   - Sign up: https://www.mongodb.com/cloud/atlas/register")
    print("   - Create free cluster")
    print("   - Get connection string")
    print("   - Add to .env: MONGODB_URI=mongodb+srv://...")
except Exception as e:
    print(f"[ERROR] Unexpected error: {e}")
    import traceback
    traceback.print_exc()

