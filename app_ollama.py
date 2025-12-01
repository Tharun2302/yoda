from flask import Flask, request, jsonify, Response, send_file
from flask_cors import CORS
from functools import wraps
import json
import time
import os
import sys
import re
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from langfuse_tracker import langfuse_tracker
from rag_system import QuestionBookRAG

# Load environment variables from .env file
load_dotenv()

# Ollama client setup
import httpx

# MongoDB imports
try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    print("⚠️  pymongo not installed - MongoDB features disabled")

# Voice processing imports
try:
    import voice_processor
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False
    print("⚠️  voice_processor not available - voice features disabled")

# Import HealthBench evaluation modules
try:
    evals_path = Path(__file__).resolve().parent / 'evals'
    sys.path.insert(0, str(evals_path))
    
    from simple_live_evaluator import get_live_evaluator
    from helm_live_evaluator import get_helm_evaluator
    from langfuse_scorer import create_langfuse_scorer
    from results_storage import get_results_storage
    
    EVALUATION_AVAILABLE = True
    print("✅ HealthBench evaluation modules loaded from local evals folder")
except Exception as e:
    EVALUATION_AVAILABLE = False
    print(f"[WARNING] HealthBench evaluation not available: {e}")

app = Flask(__name__)

# CORS Configuration
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://68.183.88.5,http://localhost:8002,http://127.0.0.1:8002').split(',')
CORS(app, origins=ALLOWED_ORIGINS, supports_credentials=True)

# Security headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    if 'Content-Security-Policy' not in response.headers:
        content_type = response.headers.get('Content-Type', '')
        if 'text/html' in content_type:
            response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline'; connect-src 'self' http://68.183.88.5:8002 http://68.183.88.5 http://127.0.0.1:8002 http://localhost:8002"
        else:
            response.headers['Content-Security-Policy'] = "default-src 'self'"
    
    return response

# Ollama Configuration
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'alibayram/medgemma:4b')
OLLAMA_API_KEY = os.getenv('OLLAMA_API_KEY', 'ollama')  # Local Ollama doesn't need real key

# Initialize Ollama client
ollama_client = httpx.Client(base_url=OLLAMA_BASE_URL, timeout=60.0)

def call_ollama_chat(messages, stream=True, temperature=0.7, max_tokens=1000):
    """Call Ollama API for chat completion"""
    try:
        payload = {
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        if stream:
            with ollama_client.stream("POST", "/api/chat", json=payload) as response:
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "message" in data and "content" in data["message"]:
                                yield data["message"]["content"]
                        except json.JSONDecodeError:
                            continue
        else:
            response = ollama_client.post("/api/chat", json=payload)
            data = response.json()
            return data.get("message", {}).get("content", "")
    except Exception as e:
        print(f"[ERROR] Ollama API call failed: {e}")
        raise

# Langfuse tracker
langfuse = langfuse_tracker.client

# Initialize RAG system
rag_system = None
live_evaluator = None
helm_evaluator = None
langfuse_scorer = None
results_storage = None

def initialize_rag_system():
    """Initialize RAG system"""
    global rag_system
    if rag_system is None:
        try:
            # For Ollama, we pass None as openai_client since embeddings will use Ollama
            rag_system = QuestionBookRAG('docx/Question BOOK.docx', openai_client=None)
            print(f"✅ RAG System loaded: {len(rag_system.questions)} questions available")
        except Exception as e:
            print(f"[WARNING] Could not load RAG system: {e}")
            rag_system = None

def initialize_evaluation_system():
    """Initialize evaluation system"""
    global live_evaluator, helm_evaluator, langfuse_scorer, results_storage
    
    if not EVALUATION_AVAILABLE:
        print("[INFO] Evaluation system not available")
        return
    
    if live_evaluator is None:
        try:
            grader_model = os.getenv('HEALTHBENCH_GRADER_MODEL', 'gpt-4o-mini')
            helm_judge_model = os.getenv('HELM_JUDGE_MODEL', 'gpt-4o-mini')
            
            live_evaluator = get_live_evaluator(grader_model=grader_model)
            helm_evaluator = get_helm_evaluator(judge_model=helm_judge_model)
            langfuse_scorer = create_langfuse_scorer(langfuse_client=langfuse)
            results_storage = get_results_storage()
            
            if live_evaluator.enabled:
                print(f"[OK] HealthBench evaluation initialized (grader: {grader_model})")
            if helm_evaluator and helm_evaluator.enabled:
                print(f"[OK] HELM evaluation initialized (judge: {helm_judge_model})")
            if results_storage:
                print(f"[OK] Results storage initialized for custom dashboard")
                
        except Exception as e:
            print(f"[WARNING] Could not initialize evaluation system: {e}")

initialize_rag_system()
initialize_evaluation_system()

# In-memory conversation history
conversations = {}

# MongoDB connection
mongodb_client = None
mongodb_db = None
patient_sessions_collection = None

def initialize_mongodb():
    """Initialize MongoDB connection"""
    global mongodb_client, mongodb_db, patient_sessions_collection
    
    if not MONGODB_AVAILABLE:
        print("⚠️  MongoDB not available")
        return False
    
    try:
        mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://mongodb:27017/')
        mongodb_db_name = os.getenv('MONGODB_DB', 'healthyoda')
        
        mongodb_client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        mongodb_client.admin.command('ping')
        mongodb_db = mongodb_client[mongodb_db_name]
        patient_sessions_collection = mongodb_db['patient_sessions']
        
        patient_sessions_collection.create_index('session_id', unique=True)
        patient_sessions_collection.create_index('created_at')
        
        print(f"✅ MongoDB connected: {mongodb_db_name}")
        return True
    except Exception as e:
        print(f"⚠️  MongoDB connection failed: {e}")
        mongodb_client = None
        mongodb_db = None
        patient_sessions_collection = None
        return False

mongodb_connected = initialize_mongodb()

# Rate limiting
from collections import defaultdict
from datetime import timedelta

rate_limit_store = defaultdict(list)
RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', '100'))
RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', '3600'))

def check_rate_limit(ip_address):
    """Check rate limit"""
    now = datetime.now()
    window_start = now - timedelta(seconds=RATE_LIMIT_WINDOW)
    
    rate_limit_store[ip_address] = [
        ts for ts in rate_limit_store[ip_address] 
        if ts > window_start
    ]
    
    if len(rate_limit_store[ip_address]) >= RATE_LIMIT_REQUESTS:
        return False
    
    rate_limit_store[ip_address].append(now)
    return True

def sanitize_input(text, max_length=5000):
    """Sanitize user input"""
    if not isinstance(text, str):
        return ""
    
    text = text.replace('\x00', '')
    
    if len(text) > max_length:
        text = text[:max_length]
    
    text = re.sub(r'[^\w\s\.,;:\-\(\)\[\]\/\?\'"]', '', text)
    
    return text.strip()

def validate_session_id(session_id):
    """Validate session ID format"""
    if not session_id or not isinstance(session_id, str):
        return False
    if not re.match(r'^[a-zA-Z0-9._-]+$', session_id):
        return False
    if len(session_id) > 200:
        return False
    return True

# System prompt
SYSTEM_PROMPT = """You are HealthYoda, a medical intake voice agent.
Your role is to conduct an extensive, medically accurate patient interview to support Level 5 medical decision-making.

You must not give medical advice, diagnosis, interpretation, reassurance, or treatment of any kind.

Ask one question at a time (≤ 12 words).
Adapt the next question based on the patient's last answer.
Maintain empathy, clarity, and a professional tone.

When starting a new conversation, introduce yourself as HealthYoda and ask what brings them in today."""

@app.route('/chat/greeting', methods=['POST'])
def chat_greeting():
    """Send initial greeting"""
    try:
        if rag_system is None:
            initialize_rag_system()
        
        data = request.get_json() or {}
        session_id = data.get('session_id', 'default')
        if not validate_session_id(session_id):
            session_id = 'default'
        
        if session_id not in conversations:
            conversations[session_id] = []
        
        conversation_history = conversations[session_id]
        
        has_user_messages = any(msg.get('role') == 'user' for msg in conversation_history)
        
        if len(conversation_history) == 0 and not has_user_messages:
            messages = [
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': 'Introduce yourself as HealthYoda and ask what brings them in today.'}
            ]
            
            def generate():
                try:
                    yield f"data: {json.dumps({'type': 'thinking_complete'})}\n\n"
                    
                    full_response = ""
                    
                    for token in call_ollama_chat(messages, stream=True, temperature=0.7, max_tokens=1000):
                        full_response += token
                        yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"
                    
                    conversation_history.append({'role': 'user', 'content': 'Introduce yourself as HealthYoda and ask what brings them in today.'})
                    conversation_history.append({'role': 'assistant', 'content': full_response})
                    
                    yield f"data: {json.dumps({'type': 'done', 'full_response': full_response})}\n\n"
                    
                except Exception as e:
                    error_msg = f"Error generating greeting: {str(e)}"
                    yield f"data: {json.dumps({'type': 'error', 'error': error_msg})}\n\n"
            
            return Response(generate(), mimetype='text/event-stream')
        else:
            def empty_response():
                yield f"data: {json.dumps({'type': 'done', 'full_response': ''})}\n\n"
            return Response(empty_response(), mimetype='text/event-stream')
    
    except Exception as e:
        print(f"[ERROR] Failed to send greeting: {e}")
        def error_response():
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        return Response(error_response(), mimetype='text/event-stream')

@app.route('/chat/stream', methods=['POST'])
def chat_stream():
    """Streaming chat endpoint using Ollama"""
    try:
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if not check_rate_limit(client_ip):
            def error_response():
                yield f"data: {json.dumps({'type': 'error', 'error': 'Rate limit exceeded'})}\n\n"
            return Response(error_response(), mimetype='text/event-stream')
        
        if rag_system is None:
            initialize_rag_system()
        
        data = request.get_json()
        if not data:
            def error_response():
                yield f"data: {json.dumps({'type': 'error', 'error': 'No JSON data provided'})}\n\n"
            return Response(error_response(), mimetype='text/event-stream')
        
        question = data.get('question', '')
        if not question:
            def error_response():
                yield f"data: {json.dumps({'type': 'error', 'error': 'Question is required'})}\n\n"
            return Response(error_response(), mimetype='text/event-stream')
        
        question = sanitize_input(question, max_length=5000)
        if not question:
            def error_response():
                yield f"data: {json.dumps({'type': 'error', 'error': 'Invalid question format'})}\n\n"
            return Response(error_response(), mimetype='text/event-stream')
        
        session_id = data.get('session_id', 'default')
        if not validate_session_id(session_id):
            session_id = 'default'
        
        if session_id not in conversations:
            conversations[session_id] = []
        
        conversation_history = conversations[session_id]
        conversation_history.append({'role': 'user', 'content': question})
        
        messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]
        messages.extend(conversation_history[-20:])
        
        def generate():
            try:
                yield f"data: {json.dumps({'type': 'thinking_complete'})}\n\n"
                
                full_response = ""
                
                for token in call_ollama_chat(messages, stream=True, temperature=0.7, max_tokens=1000):
                    full_response += token
                    yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"
                
                assistant_msg = {'role': 'assistant', 'content': full_response}
                conversation_history.append(assistant_msg)
                
                trace_id = f'trace_{int(time.time())}'
                yield f"data: {json.dumps({'type': 'done', 'full_response': full_response, 'trace_id': trace_id})}\n\n"
                
            except Exception as e:
                error_msg = f"Error calling Ollama API: {str(e)}"
                yield f"data: {json.dumps({'type': 'error', 'error': error_msg})}\n\n"
        
        return Response(generate(), mimetype='text/event-stream')
    
    except Exception as e:
        error_msg = str(e)
        def error_response():
            yield f"data: {json.dumps({'type': 'error', 'error': error_msg})}\n\n"
        return Response(error_response(), mimetype='text/event-stream')

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'model': OLLAMA_MODEL})

@app.route('/', methods=['GET'])
def index():
    """Landing page"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>HealthYoda - Ollama Powered</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            .container {
                max-width: 800px;
                background: white;
                padding: 60px 40px;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                text-align: center;
            }
            h1 {
                font-size: 48px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 20px;
            }
            p {
                color: #7f8c8d;
                font-size: 18px;
                margin-bottom: 40px;
            }
            .badge {
                display: inline-block;
                background: #4CAF50;
                color: white;
                padding: 5px 15px;
                border-radius: 15px;
                font-size: 14px;
                margin-bottom: 20px;
            }
            .link-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 40px 30px;
                border-radius: 15px;
                text-decoration: none;
                display: inline-block;
                color: white;
                transition: transform 0.3s;
            }
            .link-card:hover {
                transform: translateY(-10px);
            }
            .link-card h2 {
                font-size: 32px;
                margin-bottom: 15px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏥 HealthYoda</h1>
            <div class="badge">Powered by Ollama + Medgemma</div>
            <p>AI-Powered Medical Interview Assistant</p>
            
            <a href="/index.html" class="link-card">
                <h2>🤖 Start Chatbot</h2>
                <p>Begin medical interview</p>
            </a>
        </div>
    </body>
    </html>
    """
    
    from flask import make_response
    response = make_response(html_content)
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self' http://68.183.88.5:8002 http://68.183.88.5 http://127.0.0.1:8002 http://localhost:8002"
    return response

@app.route('/index.html', methods=['GET'])
def chatbot_interface():
    """Serve chatbot interface"""
    try:
        chatbot_path = Path(__file__).parent / 'index.html'
        
        if not chatbot_path.exists():
            return f"<h1>Chatbot not found</h1>", 404
        
        response = send_file(chatbot_path)
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline'; connect-src 'self' http://68.183.88.5:8002 http://68.183.88.5 http://127.0.0.1:8002 http://localhost:8002; img-src 'self' data: blob:; media-src 'self' blob:"
        
        return response
    
    except Exception as e:
        return f"<h1>Error</h1><p>{str(e)}</p>", 500

if __name__ == '__main__':
    print("Starting HealthYoda with Ollama...")
    print(f"Ollama URL: {OLLAMA_BASE_URL}")
    print(f"Model: {OLLAMA_MODEL}")
    print("Server will run on http://0.0.0.0:8002")
    print("-" * 50)
    
    app.run(host='0.0.0.0', port=8002, debug=False)

