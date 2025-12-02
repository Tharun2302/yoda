#!/usr/bin/env python3
"""
Test Ollama connection from local machine
Usage: python test_ollama_connection.py
"""

import httpx
import json
import sys

# Configuration
OLLAMA_URL = "http://68.183.88.5:11434"
MODEL = "alibayram/medgemma:4b"

def test_connection():
    """Test basic Ollama connection"""
    print("=" * 60)
    print("Testing Ollama Connection")
    print("=" * 60)
    print(f"URL: {OLLAMA_URL}")
    print(f"Model: {MODEL}")
    print()
    
    try:
        client = httpx.Client(base_url=OLLAMA_URL, timeout=10.0)
        
        # Test 1: Check if Ollama is running
        print("Test 1: Checking Ollama status...")
        response = client.get("/api/tags")
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            print(f"✅ Ollama is running!")
            print(f"   Available models: {len(models)}")
            for model in models:
                print(f"   - {model.get('name', 'unknown')}")
        else:
            print(f"❌ Ollama returned status {response.status_code}")
            return False
        
        print()
        
        # Test 2: Check if our model is available
        print(f"Test 2: Checking if {MODEL} is available...")
        model_found = any(m.get('name', '').startswith(MODEL.split(':')[0]) for m in models)
        if model_found:
            print(f"✅ Model {MODEL} is available!")
        else:
            print(f"❌ Model {MODEL} not found!")
            print(f"   Available models: {[m.get('name') for m in models]}")
            return False
        
        print()
        
        # Test 3: Send a test message
        print("Test 3: Sending test message...")
        response = client.post("/api/chat", json={
            "model": MODEL,
            "messages": [
                {"role": "user", "content": "Say 'Hello, I am MedGemma!' and nothing else."}
            ],
            "stream": False
        }, timeout=30.0)
        
        if response.status_code == 200:
            data = response.json()
            content = data.get('message', {}).get('content', '')
            print(f"✅ Chat response received!")
            print(f"   Response: {content[:100]}...")
        else:
            print(f"❌ Chat request failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        print()
        print("=" * 60)
        print("✅ All tests passed! Ollama is accessible from local machine.")
        print("=" * 60)
        print()
        print("You can now use this configuration in your local app:")
        print(f"  OLLAMA_BASE_URL={OLLAMA_URL}")
        print(f"  OLLAMA_MODEL={MODEL}")
        print(f"  OLLAMA_API_KEY=ollama")
        
        return True
        
    except httpx.ConnectError as e:
        print(f"❌ Connection Error: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Check if server is accessible: ping 68.183.88.5")
        print("  2. Check if port 11434 is open: telnet 68.183.88.5 11434")
        print("  3. Check firewall on server: sudo ufw status")
        print("  4. Check if Ollama container is running:")
        print("     ssh root@68.183.88.5 'docker ps | grep ollama'")
        return False
        
    except httpx.TimeoutException as e:
        print(f"❌ Timeout Error: {e}")
        print()
        print("The server is reachable but Ollama is taking too long to respond.")
        print("Try increasing the timeout or check Ollama logs on the server.")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        client.close()

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)

