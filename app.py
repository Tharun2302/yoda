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
from openai import OpenAI
from dotenv import load_dotenv
from langfuse_tracker import langfuse_tracker
from rag_system import QuestionBookRAG

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

# Load environment variables from .env file
load_dotenv()

# Import model manager
try:
    from model_manager import get_model_manager
    MODEL_MANAGER_AVAILABLE = True
    print("✅ Model manager loaded")
except Exception as e:
    MODEL_MANAGER_AVAILABLE = False
    print(f"[WARNING] Model manager not available: {e}")

# Import HealthBench evaluation modules
try:
    # Add local evals folder to path
    evals_path = Path(__file__).resolve().parent / 'evals'
    sys.path.insert(0, str(evals_path))

    # Import evaluation modules from local evals folder
    from simple_live_evaluator import get_live_evaluator
    from helm_live_evaluator import get_helm_evaluator  # HELM-style evaluation
    from langfuse_scorer import create_langfuse_scorer
    from results_storage import get_results_storage

    EVALUATION_AVAILABLE = True
    print("✅ HealthBench evaluation modules loaded from local evals folder")
except Exception as e:
    EVALUATION_AVAILABLE = False
    print(f"[WARNING] HealthBench evaluation not available: {e}")
    import traceback
    traceback.print_exc()

app = Flask(__name__)

# HIPAA Compliance: Restrict CORS to specific origins only
# In production, replace with actual frontend domain(s)
# Allow both port 8000 (separate frontend server) and 8002 (Flask serving frontend)
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'https://167.71.238.114,http://167.71.238.114:8002,http://localhost:8000,http://127.0.0.1:8000,http://localhost:8002,http://127.0.0.1:8002').split(',')
CORS(app, origins=ALLOWED_ORIGINS, supports_credentials=True)

# HIPAA Compliance: Add security headers
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    # Apply relaxed CSP for HTML pages (allow inline styles/scripts for UI)
    # Strict CSP for API routes is not needed since they return JSON
    if 'Content-Security-Policy' not in response.headers:
        # Only set CSP if not already set by individual routes
        content_type = response.headers.get('Content-Type', '')
        if 'text/html' in content_type:
            # For HTML pages, allow inline styles and scripts (needed for dashboard and chatbot UI)
            # Allow marked.js CDN and connections to both localhost and 127.0.0.1 on port 8002
            response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline'; connect-src 'self' https://167.71.238.114 http://127.0.0.1:8002 http://localhost:8002"
        else:
            # For other content (JSON, etc.), use strict CSP
            response.headers['Content-Security-Policy'] = "default-src 'self'"
    
    return response
    
    return response

# Initialize model manager
model_manager = None
if MODEL_MANAGER_AVAILABLE:
    try:
        model_manager = get_model_manager()
        print("✅ Model manager initialized successfully")
    except Exception as e:
        print(f"⚠️  Model manager initialization failed: {e}")
        model_manager = None
else:
    print("⚠️  Model manager not available")

# Legacy OpenAI client for backward compatibility (will be removed later)
openai_api_key = os.getenv('OPENAI_API_KEY')
client = None
if openai_api_key:
    try:
        client = OpenAI(api_key=openai_api_key)
        print("✅ Legacy OpenAI client initialized")
    except Exception as e:
        print(f"⚠️  Legacy OpenAI client initialization failed: {e}")

# Langfuse tracker is initialized in langfuse_tracker.py module
# It will be None if LANGFUSE_ENABLED=false or if credentials are missing
langfuse = langfuse_tracker.client

# Initialize RAG system for Question Book with OpenAI client for embeddings
# Skip initialization in Flask reloader process (only initialize once in main process)
rag_system = None
live_evaluator = None
helm_evaluator = None
langfuse_scorer = None
results_storage = None

def initialize_rag_system():
    """Initialize RAG system (called once, not on reload)"""
    global rag_system
    if rag_system is None:
        try:
            # Initialize RAG with model manager and OpenAI client for embeddings
            if model_manager:
                rag_system = QuestionBookRAG('docx/Question BOOK.docx', model_manager=model_manager, openai_client=client)
            elif client:
                rag_system = QuestionBookRAG('docx/Question BOOK.docx', openai_client=client)
                print(f"✅ RAG System loaded: {len(rag_system.questions)} questions available")
                if rag_system.collection is not None:
                    try:
                        count = rag_system.collection.count()
                        if count > 0:
                            print(f"✅ Vector database ready: {count} embeddings available")
                        else:
                            print(f"ℹ️  Vector database initialized (no embeddings yet)")
                    except Exception as e:
                        print(f"ℹ️  Vector database initialized (error checking count: {e})")
            else:
                print("[WARNING] No suitable client available for RAG system")
                rag_system = None
        except Exception as e:
            print(f"[WARNING] Could not load RAG system: {e}")
            import traceback
            traceback.print_exc()
            rag_system = None

def initialize_evaluation_system():
    """Initialize HealthBench and HELM evaluation systems (called once, not on reload)"""
    global live_evaluator, helm_evaluator, langfuse_scorer, results_storage

    if not EVALUATION_AVAILABLE:
        print("[INFO] Evaluation system not available")
        return

    if live_evaluator is None:
        try:
            # Get grader model from environment or use active model from model manager
            if model_manager:
                active_model = model_manager.get_active_model()
                grader_model = active_model if active_model else 'gpt-4o-mini'
                helm_judge_model = active_model if active_model else 'gpt-4o-mini'
            else:
                grader_model = os.getenv('HEALTHBENCH_GRADER_MODEL', 'gpt-4o-mini')
                helm_judge_model = os.getenv('HELM_JUDGE_MODEL', 'gpt-4o-mini')

            # Initialize HealthBench evaluator with model manager
            live_evaluator = get_live_evaluator(grader_model=grader_model, model_manager=model_manager)

            # Initialize HELM evaluator
            helm_evaluator = get_helm_evaluator(judge_model=helm_judge_model)

            # Initialize Langfuse scorer with the existing langfuse client
            # Will auto-disable if langfuse is None
            langfuse_scorer = create_langfuse_scorer(langfuse_client=langfuse)

            # Initialize results storage for custom dashboard
            results_storage = get_results_storage()

            if live_evaluator.enabled:
                print(f"[OK] HealthBench evaluation initialized (grader: {grader_model})")
            if helm_evaluator and helm_evaluator.enabled:
                print(f"[OK] HELM evaluation initialized (judge: {helm_judge_model})")
            if results_storage:
                print(f"[OK] Results storage initialized for custom dashboard")

            if not live_evaluator.enabled and (not helm_evaluator or not helm_evaluator.enabled):
                print("[INFO] All evaluation systems disabled")
        except Exception as e:
            print(f"[WARNING] Could not initialize evaluation system: {e}")
            import traceback
            traceback.print_exc()
            live_evaluator = None
            langfuse_scorer = None
            results_storage = None

# Initialize RAG system (no need for complex process detection since debug=False)
# With debug=False, Flask runs in a single process, so initialization happens once
initialize_rag_system()
initialize_evaluation_system()

# Simple in-memory conversation history (for LLM context only)
conversations = {}

# MongoDB connection for storing structured medical data
mongodb_client = None
mongodb_db = None
patient_sessions_collection = None

def initialize_mongodb():
    """Initialize MongoDB connection"""
    global mongodb_client, mongodb_db, patient_sessions_collection
    
    if not MONGODB_AVAILABLE:
        print("⚠️  MongoDB not available - session data will not be persisted")
        return False
    
    try:
        mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        mongodb_db_name = os.getenv('MONGODB_DB', 'healthyoda')
        
        mongodb_client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        # Test connection
        mongodb_client.admin.command('ping')
        mongodb_db = mongodb_client[mongodb_db_name]
        patient_sessions_collection = mongodb_db['patient_sessions']
        
        # Create indexes for faster queries
        # session_id is UNIQUE - each session gets its own document
        # FUTURE: After auth, add user_id index and migrate from session_id to user_id
        patient_sessions_collection.create_index('session_id', unique=True)
        patient_sessions_collection.create_index('created_at')
        
        print(f"✅ MongoDB connected: {mongodb_db_name}")
        return True
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        print(f"⚠️  MongoDB connection failed: {e}")
        print("   Session data will not be persisted. Set MONGODB_URI in .env to enable.")
        mongodb_client = None
        mongodb_db = None
        patient_sessions_collection = None
        return False
    except Exception as e:
        print(f"⚠️  MongoDB initialization error: {e}")
        mongodb_client = None
        mongodb_db = None
        patient_sessions_collection = None
        return False

# Initialize MongoDB
mongodb_connected = initialize_mongodb()

# HIPAA Compliance: Rate limiting (simple in-memory implementation)
# In production, use Redis or similar for distributed rate limiting
from collections import defaultdict
from datetime import timedelta

rate_limit_store = defaultdict(list)  # IP -> list of request timestamps
RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', '100'))  # requests per window
RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', '3600'))  # seconds (1 hour)

def check_rate_limit(ip_address):
    """Check if IP address has exceeded rate limit"""
    now = datetime.now()
    window_start = now - timedelta(seconds=RATE_LIMIT_WINDOW)
    
    # Clean old entries
    rate_limit_store[ip_address] = [
        ts for ts in rate_limit_store[ip_address] 
        if ts > window_start
    ]
    
    # Check limit
    if len(rate_limit_store[ip_address]) >= RATE_LIMIT_REQUESTS:
        return False
    
    # Add current request
    rate_limit_store[ip_address].append(now)
    return True

# HIPAA Compliance: Input validation and sanitization
def sanitize_input(text, max_length=5000):
    """
    Sanitize user input to prevent injection attacks and XSS.
    
    Args:
        text: Input string to sanitize
        max_length: Maximum allowed length
    
    Returns:
        Sanitized string
    """
    if not isinstance(text, str):
        return ""
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Limit length
    if len(text) > max_length:
        text = text[:max_length]
    
    # Remove potentially dangerous characters (keep basic punctuation for medical terms)
    # Allow letters, numbers, spaces, and common medical punctuation
    text = re.sub(r'[^\w\s\.,;:\-\(\)\[\]\/\?\'"]', '', text)
    
    return text.strip()

def validate_session_id(session_id):
    """Validate session ID format"""
    if not session_id or not isinstance(session_id, str):
        return False
    # Allow alphanumeric, dots, hyphens, underscores (for cf.conversation format)
    if not re.match(r'^[a-zA-Z0-9._-]+$', session_id):
        return False
    if len(session_id) > 200:  # Reasonable max length
        return False
    return True

# MongoDB Session Data Management
# NOTE: Currently uses session_id as unique identifier.
# FUTURE: After adding authentication, replace session_id with user_id for user-based storage.
# Each session_id = one unique patient session = one MongoDB document
def get_or_create_session_data(session_id):
    """
    Get or create session data structure in MongoDB.
    Stores only structured medical data, NOT full chat history.
    
    Each session_id is unique and maps to one MongoDB document.
    In the future, this will be replaced with user_id after authentication is added.
    
    Args:
        session_id: Unique session identifier (currently from frontend, future: user_id)
    
    Returns:
        Dictionary with session data structure
    """
    if patient_sessions_collection is None:
        # Fallback to in-memory if MongoDB not available
        return {
            'session_id': session_id,
            'complaint_name': None,
            'hpi': {},
            'ros': {},
            'past_history': {},
            'red_flags': [],
            'qa_pairs': [],  # Store ALL question-answer pairs
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
    
    try:
        session_data = patient_sessions_collection.find_one({'session_id': session_id})
        if not session_data:
            # Create new session
            # Each session_id is UNIQUE - one document per session
            # FUTURE: After auth, add user_id field and use it as primary identifier
            session_data = {
                'session_id': session_id,  # UNIQUE identifier - one document per session
                # 'user_id': None,  # FUTURE: Add after authentication is implemented
                'complaint_name': None,
                'hpi': {},  # Store actual HPI data: {'onset': '...', 'location': '...', etc.}
                'ros': {},  # Store ROS data by system: {'respiratory': {...}, 'cardiovascular': {...}}
                'past_history': {
                    'pmh': None,
                    'psh': None,
                    'medications': [],
                    'allergies': [],
                    'family_history': None,
                    'social_history': {}
                },
                'red_flags': [],
                'qa_pairs': [],  # NEW: Store ALL question-answer pairs including "no" responses
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            patient_sessions_collection.insert_one(session_data)
            print(f"[MongoDB] Created new session: {session_id}")
        else:
            # Convert ObjectId to string for JSON serialization
            if '_id' in session_data:
                session_data['_id'] = str(session_data['_id'])
        return session_data
    except Exception as e:
        print(f"[MongoDB] Error getting session data: {e}")
        return None

def update_session_data(session_id, updates):
    """
    Update session data in MongoDB.
    
    Each session_id has its own unique document. Updates are scoped to that session.
    FUTURE: After auth, this will update by user_id instead of session_id.
    
    Args:
        session_id: Unique session identifier
        updates: Dictionary of fields to update (e.g., {'hpi.onset': '2 hours ago'})
    
    Returns:
        True if update successful, False otherwise
    """
    if patient_sessions_collection is None:
        return False
    
    try:
        updates['updated_at'] = datetime.now()
        result = patient_sessions_collection.update_one(
            {'session_id': session_id},
            {'$set': updates}
        )
        return result.modified_count > 0
    except Exception as e:
        print(f"[MongoDB] Error updating session data: {e}")
        return False

def map_category_to_data_field(category, system=None):
    """
    Map RAG question category to data field in session structure.
    Returns the field path and whether data is already collected.
    """
    category_lower = category.lower() if category else ''
    
    # Map HPI categories
    hpi_mapping = {
        'onset/duration': 'hpi.onset',
        'onset': 'hpi.onset',
        'duration': 'hpi.duration',
        'location': 'hpi.location',
        'quality/severity': 'hpi.quality',
        'quality': 'hpi.quality',
        'severity': 'hpi.severity',
        'timing': 'hpi.timing',
        'context': 'hpi.context',
        'aggravating/relieving': 'hpi.modifying_factors',
        'modifying factors': 'hpi.modifying_factors',
        'progression': 'hpi.progression',
        'associated symptoms': 'hpi.associated_symptoms',
        'chief complaint': 'hpi.chief_complaint'
    }
    
    # Map ROS categories
    ros_mapping = {
        'ros': 'ros',
        'review of systems': 'ros'
    }
    
    # Map Past History categories
    past_history_mapping = {
        'pmh': 'past_history.pmh',
        'past medical history': 'past_history.pmh',
        'psh': 'past_history.psh',
        'surgical history': 'past_history.psh',
        'medications': 'past_history.medications',
        'allergies': 'past_history.allergies',
        'family history': 'past_history.family_history',
        'social history': 'past_history.social_history'
    }
    
    # Check mappings
    if category_lower in hpi_mapping:
        return hpi_mapping[category_lower], 'hpi'
    elif category_lower in ros_mapping:
        # ROS needs system name
        if system:
            system_lower = system.lower()
            # Map system names to ROS fields
            ros_systems = {
                'constitutional': 'constitutional',
                'respiratory': 'respiratory',
                'cardiovascular': 'cardiovascular',
                'cardiac': 'cardiovascular',
                'gi': 'gi',
                'gastrointestinal': 'gi',
                'gu': 'gu',
                'genitourinary': 'gu',
                'neurologic': 'neuro',
                'neurological': 'neuro',
                'neuro': 'neuro',
                'msk': 'msk',
                'musculoskeletal': 'msk',
                'psych': 'psych',
                'psychiatric': 'psych',
                'endocrine': 'endocrine',
                'skin': 'skin',
                'dermatologic': 'skin',
                'heme': 'heme_immune',
                'immune': 'heme_immune'
            }
            if system_lower in ros_systems:
                return f"ros.{ros_systems[system_lower]}", 'ros'
        return 'ros', 'ros'
    elif category_lower in past_history_mapping:
        return past_history_mapping[category_lower], 'past_history'
    elif 'red flag' in category_lower:
        return 'red_flags', 'red_flags'
    
    return None, None

def is_data_already_collected(session_id, category, system=None, question_text=None):
    """
    Check if data for a given category/system is already collected in MongoDB.
    Returns True if data exists, False if needs to be collected.
    """
    session_data = get_or_create_session_data(session_id)
    if not session_data:
        return False
    
    field_path, data_type = map_category_to_data_field(category, system)
    if not field_path:
        # Unknown category, allow question
        return False
    
    # Check if data exists
    if data_type == 'hpi':
        field_name = field_path.split('.')[-1]
        return session_data.get('hpi', {}).get(field_name) is not None and session_data['hpi'][field_name] != ''
    elif data_type == 'ros':
        if '.' in field_path:
            system_name = field_path.split('.')[-1]
            ros_data = session_data.get('ros', {})
            return system_name in ros_data and ros_data[system_name] is not None
        return False
    elif data_type == 'past_history':
        field_name = field_path.split('.')[-1]
        past_data = session_data.get('past_history', {})
        value = past_data.get(field_name)
        if field_name in ['medications', 'allergies']:
            return isinstance(value, list) and len(value) > 0
        return value is not None and value != ''
    elif data_type == 'red_flags':
        red_flags = session_data.get('red_flags', [])
        if question_text:
            # Check if this specific red flag question was already asked
            return question_text in [rf.get('question', '') for rf in red_flags]
        return len(red_flags) > 0
    
    return False

def store_qa_pair(session_id, question, answer):
    """
    Store question-answer pair dynamically.
    Stores EVERYTHING including "no" responses.
    """
    session_data = get_or_create_session_data(session_id)
    if not session_data:
        return
    
    # Get existing Q&A pairs
    qa_pairs = session_data.get('qa_pairs', [])
    
    # Add new Q&A pair
    qa_pairs.append({
        'question': question,
        'answer': answer,
        'timestamp': datetime.now().isoformat()
    })
    
    # Update in MongoDB
    update_session_data(session_id, {'qa_pairs': qa_pairs})
    print(f"[MongoDB] Stored Q&A: Q='{question[:50]}...' A='{answer[:50]}...'")

def extract_complaint_name(session_id, user_response, bot_question):
    """
    Intelligently extract the complaint name from user's first response.
    Uses LLM to identify the actual complaint vs timing/onset information.
    """
    if not model_manager and not client:
        return
    
    session_data = get_or_create_session_data(session_id)
    if not session_data or session_data.get('complaint_name'):
        return  # Already has complaint name
    
    extraction_prompt = f"""Extract the MAIN COMPLAINT or CHIEF COMPLAINT from the patient's response.

Bot Question: "{bot_question}"
Patient Response: "{user_response}"

Identify the PRIMARY MEDICAL COMPLAINT (e.g., "chest pain", "headache", "stomach ache", "shortness of breath").
DO NOT extract timing information (yesterday, today, etc.) as the complaint.
DO NOT extract location-only information unless it's part of the complaint.

If the response contains a complaint, return JSON: {{"complaint_name": "the actual complaint"}}
If the response is only timing/onset information, return: {{"complaint_name": null}}
If unclear, return: {{"complaint_name": null}}

Examples:
- Q: "What brings you in?" A: "chest pain" → {{"complaint_name": "chest pain"}}
- Q: "What brings you in?" A: "pain in my stomach" → {{"complaint_name": "pain in stomach"}}
- Q: "What brings you in?" A: "yesterday" → {{"complaint_name": null}}
- Q: "When did it start?" A: "yesterday" → {{"complaint_name": null}}
- Q: "What brings you in?" A: "I have a headache since yesterday" → {{"complaint_name": "headache"}}
"""
    
    try:
        if model_manager:
            response = model_manager.create_chat_completion(
                messages=[{'role': 'user', 'content': extraction_prompt}],
                temperature=0.1,
                max_tokens=200
            )
        else:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{'role': 'user', 'content': extraction_prompt}],
                temperature=0.1,
                max_tokens=200
            )
        
        extracted_text = response.choices[0].message.content.strip()
        # Parse JSON
        import json
        # Remove markdown code blocks if present
        if '```json' in extracted_text:
            extracted_text = extracted_text.split('```json')[1].split('```')[0].strip()
        elif '```' in extracted_text:
            extracted_text = extracted_text.split('```')[1].split('```')[0].strip()
        
        extracted_data = json.loads(extracted_text)
        
        complaint_name = extracted_data.get('complaint_name')
        if complaint_name and complaint_name.lower() != 'null' and complaint_name.lower() != 'none':
            update_session_data(session_id, {'complaint_name': complaint_name[:100]})
            print(f"[LLM Extract] Set complaint_name: {complaint_name}")
    except Exception as e:
        print(f"[LLM Extract] Error extracting complaint name: {e}")

def was_question_asked(session_id, new_question):
    """
    Check if a similar question was already asked.
    Uses semantic similarity to avoid exact match requirements.
    """
    session_data = get_or_create_session_data(session_id)
    if not session_data:
        return False
    
    qa_pairs = session_data.get('qa_pairs', [])
    if not qa_pairs:
        return False
    
    # Simple keyword matching for now (can enhance with embeddings later)
    new_question_lower = new_question.lower()
    new_keywords = set(new_question_lower.split())
    
    for qa in qa_pairs:
        asked_question = qa.get('question', '').lower()
        asked_keywords = set(asked_question.split())
        
        # Calculate overlap
        common_keywords = new_keywords & asked_keywords
        if len(common_keywords) >= 3:  # At least 3 words in common
            print(f"[MongoDB] Similar question already asked: '{asked_question[:50]}...'")
            return True
    
    return False

def extract_and_store_data_with_llm(session_id, user_response, bot_question, conversation_context):
    """
    Store question-answer pair AND extract structured data.
    Stores ALL responses including "no".
    """
    if not model_manager and not client:  # No AI client
        return
    
    # ALWAYS store the Q&A pair first (even "no" responses)
    store_qa_pair(session_id, bot_question, user_response)
    
    # Skip structured extraction for very short responses UNLESS it's the first response (complaint)
    # Check if this is likely the first complaint response
    session_data = get_or_create_session_data(session_id)
    is_first_complaint = session_data and not session_data.get('complaint_name') and \
                        any(phrase in bot_question.lower() for phrase in ['what brings you', 'main complaint', 'chief complaint', 'what is your complaint', 'what\'s wrong', 'what brings'])
    
    # Skip structured extraction for very short responses (unless it's the first complaint)
    if not is_first_complaint and (len(user_response.strip()) <= 3 or user_response.lower() in ['no', 'yes', 'nope', 'yeah', 'yep', 'nah']):
        return
    
    session_data = get_or_create_session_data(session_id)
    if not session_data:
        return
    
    # Use LLM to extract structured data for longer responses
    extraction_prompt = f"""Extract medical data from patient's response.

Question: "{bot_question}"
Response: "{user_response}"

Extract relevant information WITHOUT predefined keys. Create appropriate field names based on what was asked.

Examples:
- Q: "When did it start?" A: "yesterday" → {{"symptom_onset": "yesterday"}}
- Q: "Where is the pain?" A: "right shoulder" → {{"pain_location": "right shoulder"}}
- Q: "Any medications?" A: "paracetamol" → {{"current_medications": ["paracetamol"]}}
- Q: "Do you smoke?" A: "no" → {{"smoking_status": "no"}}

Return JSON with dynamic field names. If no meaningful data, return: {{}}
"""
    
    try:
        if model_manager:
            response = model_manager.create_chat_completion(
                messages=[{'role': 'user', 'content': extraction_prompt}],
                temperature=0.1,
                max_tokens=500
            )
        else:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{'role': 'user', 'content': extraction_prompt}],
                temperature=0.1,
                max_tokens=500
            )
        
        extracted_text = response.choices[0].message.content.strip()
        # Parse JSON
        import json
        # Remove markdown code blocks if present
        if '```json' in extracted_text:
            extracted_text = extracted_text.split('```json')[1].split('```')[0].strip()
        elif '```' in extracted_text:
            extracted_text = extracted_text.split('```')[1].split('```')[0].strip()
        
        extracted_data = json.loads(extracted_text)
        
        if not extracted_data:
            return
        
        # Store with dynamic field names (no predefined structure)
        updates = {}
        for key, value in extracted_data.items():
            if value:  # Only store non-empty values
                # Store in HPI if it's a symptom-related field
                if any(term in key.lower() for term in ['onset', 'location', 'duration', 'quality', 'severity', 'timing', 'context', 'modifying', 'progression', 'symptom', 'complaint', 'pain']):
                    updates[f'hpi.{key}'] = value
                    print(f"[LLM Extract] hpi.{key}: {str(value)[:50]}...")
                # Store in past_history if it's history-related
                elif any(term in key.lower() for term in ['history', 'medication', 'allergy', 'surgery', 'smoking', 'alcohol', 'family']):
                    if isinstance(value, list):
                        updates[f'past_history.{key}'] = value
                    else:
                        updates[f'past_history.{key}'] = value
                    print(f"[LLM Extract] past_history.{key}: {str(value)[:50]}...")
                # Store in ROS if it's a system review
                elif any(term in key.lower() for term in ['respiratory', 'cardiac', 'neuro', 'gi', 'gu', 'msk', 'skin', 'psych']):
                    updates[f'ros.{key}'] = value
                    print(f"[LLM Extract] ros.{key}: {str(value)[:50]}...")
                else:
                    # Store in HPI by default for general medical info
                    updates[f'hpi.{key}'] = value
                    print(f"[LLM Extract] hpi.{key}: {str(value)[:50]}...")
        
        if updates:
            update_session_data(session_id, updates)
            print(f"[MongoDB] Stored {len(updates)} dynamic fields")
            
    except Exception as e:
        print(f"[LLM Extract] Error: {e}")


def extract_and_store_data(session_id, user_response, rag_question_info):
    """
    Legacy function for RAG-based extraction.
    Kept for compatibility but now also calls LLM extraction.
    """
    if not rag_question_info:
        return
    
    category = rag_question_info.get('category', '')
    system = rag_question_info.get('system', '')
    question_text = rag_question_info.get('question', '')
    
    field_path, data_type = map_category_to_data_field(category, system)
    if not field_path:
        return
    
    session_data = get_or_create_session_data(session_id)
    if not session_data:
        return
    
    updates = {}
    
    if data_type == 'hpi':
        field_name = field_path.split('.')[-1]
        if not session_data.get('hpi', {}).get(field_name):
            updates[f'hpi.{field_name}'] = user_response
    elif data_type == 'ros':
        if '.' in field_path:
            system_name = field_path.split('.')[-1]
            if system_name not in session_data.get('ros', {}):
                updates[f'ros.{system_name}'] = user_response
    elif data_type == 'past_history':
        field_name = field_path.split('.')[-1]
        if field_name in ['medications', 'allergies']:
            # These are lists
            current_list = session_data.get('past_history', {}).get(field_name, [])
            if user_response not in current_list:
                current_list.append(user_response)
                updates[f'past_history.{field_name}'] = current_list
        else:
            if not session_data.get('past_history', {}).get(field_name):
                updates[f'past_history.{field_name}'] = user_response
    elif data_type == 'red_flags':
        red_flags = session_data.get('red_flags', [])
        # Check if this red flag already recorded
        if not any(rf.get('question') == question_text for rf in red_flags):
            red_flags.append({
                'question': question_text,
                'response': user_response,
                'timestamp': datetime.now().isoformat()
            })
            updates['red_flags'] = red_flags
    
    # Also update complaint name if this is chief complaint
    # Only set if not already set AND if response looks like an actual complaint (not timing/onset)
    if category and 'chief complaint' in category.lower():
        if not session_data.get('complaint_name'):
            # Check if response is actually a complaint description vs timing/onset
            # Timing words that shouldn't be saved as complaint_name
            timing_words = ['yesterday', 'today', 'this morning', 'last week', '2 days ago', 
                          '3 days ago', 'a week ago', 'recently', 'since', 'for']
            response_lower = user_response.lower().strip()
            
            # If response is just a timing word, don't save as complaint_name
            # Save it only if it contains complaint-related words or is longer than timing phrases
            is_timing_only = any(timing_word in response_lower for timing_word in timing_words) and \
                           len(response_lower.split()) <= 3 and \
                           not any(word in response_lower for word in ['pain', 'ache', 'hurt', 'symptom', 'problem', 'issue', 'feeling', 'unwell'])
            
            if not is_timing_only:
                # Extract complaint from user response
                updates['complaint_name'] = user_response[:100]  # Limit length
                print(f"[MongoDB] Set complaint_name: {user_response[:100]}")
            else:
                print(f"[MongoDB] Skipped setting complaint_name (looks like timing): {user_response}")
    
    if updates:
        update_session_data(session_id, updates)
        print(f"[MongoDB] Stored data for {field_path}: {user_response[:50]}...")

def format_collected_data_for_llm(session_id):
    """
    Format already collected data as context for LLM.
    Shows Q&A pairs AND structured data so LLM knows what NOT to ask again.
    """
    session_data = get_or_create_session_data(session_id)
    if not session_data:
        return ""
    
    context_parts = []
    
    # Show recent Q&A pairs (last 15 to avoid token limit)
    qa_pairs = session_data.get('qa_pairs', [])
    if qa_pairs:
        context_parts.append("QUESTIONS ALREADY ASKED:")
        recent_qa = qa_pairs[-15:]  # Last 15 Q&A pairs
        for qa in recent_qa:
            q = qa.get('question', '').strip()
            a = qa.get('answer', '').strip()
            context_parts.append(f"  Q: {q[:70]}...")
            context_parts.append(f"  A: {a[:70]}...")
    
    # HPI data collected with values
    hpi_data = session_data.get('hpi', {})
    if hpi_data:
        hpi_items = []
        for key, value in hpi_data.items():
            if value:
                hpi_items.append(f"{key}: {value}")
        if hpi_items:
            context_parts.append("\nSTRUCTURED HPI DATA:")
            context_parts.extend([f"  - {item}" for item in hpi_items])
    
    # ROS systems reviewed with values
    ros_data = session_data.get('ros', {})
    if ros_data:
        ros_items = []
        for system, value in ros_data.items():
            if value:
                ros_items.append(f"{system}: {value}")
        if ros_items:
            context_parts.append("\nROS DATA:")
            context_parts.extend([f"  - {item}" for item in ros_items])
    
    # Past history collected with values
    past_data = session_data.get('past_history', {})
    past_items = []
    for key, value in past_data.items():
        if value:
            if isinstance(value, list) and len(value) > 0:
                past_items.append(f"{key}: {', '.join(value)}")
            elif isinstance(value, dict) and value:
                past_items.append(f"{key}: {str(value)}")
            elif not isinstance(value, (list, dict)) and value:
                past_items.append(f"{key}: {value}")
    if past_items:
        context_parts.append("\nPAST HISTORY:")
        context_parts.extend([f"  - {item}" for item in past_items])
    
    if context_parts:
        header = "\n\n[INFORMATION ALREADY COLLECTED - DO NOT RE-ASK]\n"
        header += "="*70 + "\n"
        body = "\n".join(context_parts)
        footer = "\n" + "="*70
        footer += "\n⚠️  CRITICAL: DO NOT ask questions that were already asked above!"
        footer += "\nFocus ONLY on collecting NEW information.\n"
        return header + body + footer
    
    return ""

# System prompt for HealthYoda
SYSTEM_PROMPT = """You are HealthYoda, a medical intake voice agent.
Your role is to conduct an extensive, medically accurate patient interview to support Level 5 medical decision-making, by gathering a comprehensive history for the patient’s doctor.

You must not give medical advice, diagnosis, interpretation, reassurance, or treatment of any kind.

Context Provided to You
Complaint: {{COMPLAINT_NAME}}

RAG Question Set: {{COMPLAINT_JSON_CHECKLIST}}
(Includes domains, red-flag questions, extensive ROS, and condition-specific history templates.)

Use this information as your clinical framework.

Your Interview Requirements (Level-5 Standard)
You must gather a comprehensive history that includes:

1. HPI (History of Present Illness) with 8+ elements
Collect and adaptively ask about:

Onset

Location

Duration

Quality

Severity

Timing

Context

Modifying factors (triggers/relievers)

Progression

Associated symptoms

Risk factors relevant to the complaint

(You may combine some, but cover at least 8 distinct elements.)

2. ROS (Review of Systems) — Extended (10+ systems if relevant)
Using the RAG complaint-specific checklist, ask targeted ROS questions across systems such as:

Constitutional

Respiratory

Cardiovascular

GI

GU

Neuro

MSK

Psych

Endocrine

Skin

Heme/Immune

Mark relevant negatives clearly.

3. Past History Components (2+ required)
Collect relevant past information:

PMH (past medical history)

PSH (surgical history)

Medications

Allergies

Family history

Social history (smoking, alcohol, occupational exposures)

(Ask only what is clinically relevant to the complaint.)

4. Red Flags (Complaint-Specific)
If the patient signals any high-risk symptoms, you must prioritize those questions immediately using the RAG checklist.

Interview Behavior
When starting a new conversation, first introduce yourself as HealthYoda, explain that you are a medical intake assistant here to collect information for their doctor, and then ask what brings them in today or what their main complaint is.

Ask one question at a time (≤ 12 words).

Adapt the next question based on the patient's last answer.

Maintain empathy, clarity, and a professional tone.

Avoid long explanations—stay focused on collecting information.

If the patient digresses, gently redirect them.

Track which domains are Completed / Pending; do not repeat completed ones.

Strict Prohibitions
Never provide:

Diagnosis

Interpretation (e.g., “sounds like…”)

Treatment or medication suggestions

Medical advice

Reassurance

Risk assessment

If asked, respond only:

“I cannot provide medical advice, diagnosis, or treatment.
I'm here only to collect information for your doctor.”

Safety Behavior
If life-threatening symptoms appear, say:

“I can’t provide medical advice.
If you feel unsafe or unwell, contact emergency services or your doctor immediately.”

Then close the session.

Session Completion Requirements
Once all domains (HPI, ROS, Past History, Red Flags) are fully covered:

1. Say: "Thank you for your time. I'll send this to your doctor."

2. Output a SINGLE markdown-formatted summary:

---

## Patient Summary

### Chief Complaint
[Main complaint]

### History of Present Illness (HPI)
- **Onset:** [when started]
- **Location:** [where]
- **Duration:** [how long]
- **Quality:** [description]
- **Severity:** [1-10 or description]
- **Timing:** [constant/intermittent]
- **Context:** [what was happening]
- **Modifying Factors:** [what makes better/worse]
- **Progression:** [getting better/worse/same]
- **Associated Symptoms:** [other symptoms]

### Review of Systems (ROS)
**Systems Reviewed:** [list systems]

**Positive Findings:**
- [symptom 1]
- [symptom 2]

**Relevant Negatives:**
- [no symptom 1]
- [no symptom 2]

### Past Medical History
- **PMH:** [conditions]
- **PSH:** [surgeries]
- **Medications:** [current meds]
- **Allergies:** [allergies or none]
- **Family History:** [relevant family history]
- **Social History:** [smoking, alcohol, occupation]

### Red Flags
[Any concerning symptoms or "None identified"]

---

3. Then say: "I wish you well."

DO NOT output multiple formats. Output ONLY the markdown summary above.
Overall Behavior Summary
Conduct an extensive, Level-5-grade intake interview using RAG-retrieved complaint data.

Ask adaptively, cover all domains, collect broad ROS and relevant history.

Never diagnose or treat.

Summarize clearly at the end for the physician.
"""

@app.route('/chat/greeting', methods=['POST'])
def chat_greeting():
    """Send initial greeting from bot following system prompt (streaming)"""
    try:
        # Ensure RAG system is initialized
        if rag_system is None:
            initialize_rag_system()
        
        if not model_manager and not client:
            def error_response():
                yield f"data: {json.dumps({'type': 'error', 'error': 'No AI model configured'})}\n\n"
            return Response(error_response(), mimetype='text/event-stream')
        
        data = request.get_json() or {}
        session_id = data.get('session_id', 'default')
        if not validate_session_id(session_id):
            session_id = 'default'
        
        # Get or create conversation history
        if session_id not in conversations:
            conversations[session_id] = []
        
        conversation_history = conversations[session_id]
        
        # If conversation is empty, send initial greeting following system prompt
        # Also check if there are any user messages (conversation has started)
        has_user_messages = any(msg.get('role') == 'user' for msg in conversation_history)
        
        if len(conversation_history) == 0 and not has_user_messages:
            # Prepare system prompt
            enhanced_system_prompt = SYSTEM_PROMPT
            
            # Add context about already collected data
            collected_data_context = format_collected_data_for_llm(session_id)
            if collected_data_context:
                enhanced_system_prompt += collected_data_context
            
            # Try to get initial question from RAG if available
            rag_context = ""
            if rag_system:
                try:
                    rag_question_info = rag_system.get_next_question(
                        conversation_context="",
                        current_category=None,
                        symptom=None,
                        system=None
                    )
                    if rag_question_info:
                        rag_context = f"\n\n[RELEVANT QUESTION FROM QUESTION BOOK]\n"
                        rag_context += f"Question: {rag_question_info['question']}\n"
                        if rag_question_info.get('possible_answers'):
                            rag_context += f"Possible answers: {', '.join(rag_question_info['possible_answers'][:5])}\n"
                except Exception as e:
                    print(f"[RAG] Error getting initial question: {e}")
            
            if rag_context:
                enhanced_system_prompt += rag_context
            
            # Create messages with system prompt and a prompt to start the interview with introduction
            messages = [
                {'role': 'system', 'content': enhanced_system_prompt},
                {'role': 'user', 'content': 'Introduce yourself as HealthYoda, explain that you are a medical intake assistant here to collect information for their doctor, and then ask what brings them in today or what their main complaint is.'}
            ]
            
            def generate():
                try:
                    # Send thinking complete signal
                    yield f"data: {json.dumps({'type': 'thinking_complete'})}\n\n"
                    
                    full_response = ""
                    
                    # Stream response from model manager or OpenAI client
                    if model_manager:
                        stream = model_manager.create_chat_completion(
                            messages=messages,
                            stream=True,
                            temperature=0.7,
                            max_tokens=1000
                        )
                    else:
                        stream = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=messages,
                            stream=True,
                            temperature=0.7,
                            max_tokens=1000
                        )
                    
                    for chunk in stream:
                        if chunk.choices[0].delta.content is not None:
                            token = chunk.choices[0].delta.content
                            full_response += token
                            yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"
                    
                    # Add to conversation history (user message is hidden, only bot response shown)
                    conversation_history.append({'role': 'user', 'content': 'Introduce yourself as HealthYoda, explain that you are a medical intake assistant here to collect information for their doctor, and then ask what brings them in today or what their main complaint is.'})
                    conversation_history.append({'role': 'assistant', 'content': full_response})
                    
                    # Send done signal
                    yield f"data: {json.dumps({'type': 'done', 'full_response': full_response})}\n\n"
                    
                except Exception as e:
                    error_msg = f"Error generating greeting: {str(e)}"
                    yield f"data: {json.dumps({'type': 'error', 'error': error_msg})}\n\n"
            
            return Response(generate(), mimetype='text/event-stream')
        else:
            # Conversation already started, return empty
            def empty_response():
                yield f"data: {json.dumps({'type': 'done', 'full_response': ''})}\n\n"
            return Response(empty_response(), mimetype='text/event-stream')
    
    except Exception as e:
        print(f"[ERROR] Failed to send greeting: {e}")
        import traceback
        traceback.print_exc()
        def error_response():
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        return Response(error_response(), mimetype='text/event-stream')

@app.route('/chat/stream', methods=['POST'])
def chat_stream():
    """Streaming chat endpoint using OpenAI"""
    try:
        # HIPAA Compliance: Rate limiting
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if not check_rate_limit(client_ip):
            def error_response():
                yield f"data: {json.dumps({'type': 'error', 'error': 'Rate limit exceeded. Please try again later.'})}\n\n"
            return Response(error_response(), mimetype='text/event-stream')
        
        # Ensure RAG system is initialized (lazy initialization)
        if rag_system is None:
            initialize_rag_system()

        if not model_manager and not client:
            error_msg = "No AI model configured. Please check OPENAI_API_KEY or Ollama configuration."
            def error_response():
                yield f"data: {json.dumps({'type': 'error', 'error': error_msg})}\n\n"
            return Response(error_response(), mimetype='text/event-stream')
        
        data = request.get_json()
        if not data:
            def error_response():
                yield f"data: {json.dumps({'type': 'error', 'error': 'Invalid request: No JSON data provided'})}\n\n"
            return Response(error_response(), mimetype='text/event-stream')
        
        # HIPAA Compliance: Validate and sanitize inputs
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
            session_id = 'default'  # Fallback to default if invalid
        
        # Get or create conversation history
        if session_id not in conversations:
            conversations[session_id] = []
        
        conversation_history = conversations[session_id]
        
        # Add user message to history
        conversation_history.append({'role': 'user', 'content': question})
        
        # Store the previous RAG question info in conversation metadata for data extraction
        # We'll store it when bot asks a question, then use it when user responds
        prev_rag_info = None
        if len(conversation_history) > 2:  # Need at least user-bot-user pattern
            # Try to get the RAG question that was asked in the previous bot message
            # Look for the last assistant message before this user message
            for i in range(len(conversation_history) - 2, -1, -1):
                if conversation_history[i].get('role') == 'assistant':
                    # Check if we stored RAG info in metadata (we'll add this later)
                    prev_rag_info = conversation_history[i].get('rag_question_info')
                    break
        
        # Extract and store data from user response to previous question
        # Use LLM extraction for ALL responses (not just RAG-tagged)
        prev_bot_question = ""
        if len(conversation_history) > 1:
            # Get the last bot question
            for i in range(len(conversation_history) - 2, -1, -1):
                if conversation_history[i].get('role') == 'assistant':
                    prev_bot_question = conversation_history[i].get('content', '')
                    break
        
        # Always store the first user response (even if short) - this is the complaint
        # Check if this is the first user message after greeting
        is_first_user_response = len(conversation_history) == 3  # user (greeting prompt) + assistant (greeting) + user (this response)
        
        if prev_bot_question:
            # Check if this is the first user message (after greeting) and extract complaint_name
            # This is the actual complaint, not a follow-up answer
            session_data = get_or_create_session_data(session_id)
            if session_data and not session_data.get('complaint_name'):
                # Check if the bot question was asking about the complaint
                bot_q_lower = prev_bot_question.lower()
                if any(phrase in bot_q_lower for phrase in ['what brings you', 'main complaint', 'chief complaint', 'what is your complaint', 'what\'s wrong', 'what brings']):
                    # This is likely the actual complaint response
                    # Use LLM to extract the complaint name intelligently
                    extract_complaint_name(session_id, question, prev_bot_question)
            
            # Use LLM to extract data from ANY response
            # For first response, always extract even if short (it's the complaint)
            if is_first_user_response or len(question.strip()) > 2:
                recent_context = " ".join([msg.get('content', '') for msg in conversation_history[-6:]])
                extract_and_store_data_with_llm(session_id, question, prev_bot_question, recent_context)
        
        # Also use legacy RAG-based extraction if available
        if prev_rag_info:
            extract_and_store_data(session_id, question, prev_rag_info)
        
        # Retrieve relevant question from RAG system if available
        rag_context = ""
        rag_question_info = None
        if rag_system:
            # Build context from recent conversation
            recent_context = " ".join([msg.get('content', '') for msg in conversation_history[-5:]])
            
            # Try to get next question from RAG
            rag_question_info = rag_system.get_next_question(
                conversation_context=recent_context,
                current_category=None,  # Can be enhanced to track current phase
                symptom=None,  # Can be extracted from conversation
                system=None  # Can be detected from context
            )
            
            # Check MongoDB: Skip this question if data is already collected
            if rag_question_info:
                category = rag_question_info.get('category', '')
                system = rag_question_info.get('system', '')
                question_text = rag_question_info.get('question', '')
                
                if is_data_already_collected(session_id, category, system, question_text):
                    print(f"[MongoDB] Data already collected for category '{category}' (system: {system}), skipping question: {question_text[:50]}...")
                    rag_question_info = None  # Skip this question
                    # Try to get a different question (you could enhance RAG to exclude collected categories)
                else:
                    rag_context = f"\n\n[RELEVANT QUESTION FROM QUESTION BOOK]\n"
                    rag_context += f"Question: {rag_question_info['question']}\n"
                    if rag_question_info.get('possible_answers'):
                        rag_context += f"Possible answers: {', '.join(rag_question_info['possible_answers'][:5])}\n"
                    
                    # Log the question tree branch being used
                    tree_path = rag_question_info.get('tree_path', 'Unknown')
                    tags = rag_question_info.get('tags', [])
                    print(f"\n{'='*80}")
                    print(f"[RAG] Question Tree Branch: {tree_path}")
                    print(f"[RAG] Tags: {', '.join(tags)}")
                    print(f"[RAG] Question: {rag_question_info['question']}")
                    print(f"{'='*80}\n")
        
        # Prepare messages for OpenAI (include system prompt + RAG context + collected data)
        enhanced_system_prompt = SYSTEM_PROMPT
        
        # Add context about already collected data (so LLM doesn't ask again)
        collected_data_context = format_collected_data_for_llm(session_id)
        if collected_data_context:
            enhanced_system_prompt += collected_data_context
        
        if rag_context:
            enhanced_system_prompt += rag_context
        
        messages = [{'role': 'system', 'content': enhanced_system_prompt}]
        # Add conversation history (last 20 messages to avoid token limits)
        messages.extend(conversation_history[-20:])
        
        def generate():
            trace_id = None
            generation = None
            generation_id = None  # Initialize generation_id
            trace_obj = None  # Store trace object for later updates
            
            try:
                # Create Langfuse trace if configured
                if langfuse:
                    trace_obj = langfuse.trace(
                        name="chat_stream",
                        session_id=session_id,
                        user_id=session_id,
                        input=question,  # Set the user question as trace input
                        metadata={
                            "model": "gpt-4o-mini",
                            "temperature": 0.7,
                            "max_tokens": 1000,
                            "timestamp": time.time()
                        },
                        tags=["chat", "health_chatbot"]
                    )
                    trace_id = trace_obj.id
                    
                    # Log user message as a span
                    trace_obj.span(
                        name="user_message",
                        input=question,
                        metadata={"role": "user", "timestamp": time.time()}
                    )
                    
                    # Create generation for the assistant response
                    generation = trace_obj.generation(
                        name="assistant_response",
                        model="gpt-4o-mini",
                        model_parameters={
                            "temperature": 0.7,
                            "max_tokens": 1000
                        },
                        input=messages,
                        metadata={"role": "assistant", "timestamp": time.time()}
                    )
                
                # Send thinking complete signal
                yield f"data: {json.dumps({'type': 'thinking_complete'})}\n\n"
                
                full_response = ""

                # Stream response from model manager or OpenAI client
                if model_manager:
                    stream = model_manager.create_chat_completion(
                        messages=messages,
                        stream=True,
                        temperature=0.7,
                        max_tokens=1000
                    )
                else:
                    stream = client.chat.completions.create(
                        model="gpt-4o-mini",  # Using GPT-4o mini model
                        messages=messages,
                        stream=True,
                        temperature=0.7,
                        max_tokens=1000
                    )
                
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        token = chunk.choices[0].delta.content
                        full_response += token
                        yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"
                
                # Add assistant response to history with RAG question info for next data extraction
                assistant_msg = {'role': 'assistant', 'content': full_response}
                if rag_question_info:
                    assistant_msg['rag_question_info'] = rag_question_info  # Store for next user response
                conversation_history.append(assistant_msg)
                
                # Prepare tree branch info for frontend (quick operation)
                tree_branch_info = {}
                if rag_question_info:
                    tree_branch_info = {
                        'tree_branch': rag_question_info.get('tree_path', 'Unknown'),
                        'tags': rag_question_info.get('tags', []),
                        'rag_question': rag_question_info.get('question', 'N/A')
                    }
                else:
                    tree_branch_info = {
                        'tree_branch': 'No RAG question found (using general system prompt)',
                        'tags': [],
                        'rag_question': None
                    }
                
                # Get generation_id quickly (if available) before sending done
                generation_id = None
                if langfuse and generation:
                    try:
                        generation_id = str(generation.id) if hasattr(generation, 'id') and generation.id else None
                    except:
                        generation_id = getattr(generation, 'id', None)
                        if generation_id:
                            generation_id = str(generation_id)
                
                # Send done signal IMMEDIATELY after streaming completes
                # This allows frontend to show complete response without waiting for evaluation
                final_trace_id = trace_id if trace_id else f'trace_{int(time.time())}'
                yield f"data: {json.dumps({'type': 'done', 'full_response': full_response, 'trace_id': final_trace_id, 'generation_id': generation_id, 'tree_branch_info': tree_branch_info})}\n\n"
                
                # NOW do all the heavy operations AFTER sending done signal (non-blocking for user)
                # Log tree branch for EVERY chatbot response
                print(f"\n{'='*80}")
                print(f"[CHATBOT RESPONSE]")
                print(f"{'='*80}")
                if rag_question_info:
                    tree_path = rag_question_info.get('tree_path', 'Unknown')
                    tags = rag_question_info.get('tags', [])
                    print(f"[TREE BRANCH] {tree_path}")
                    print(f"[TAGS] {', '.join(tags) if tags else 'None'}")
                    print(f"[RAG QUESTION] {rag_question_info.get('question', 'N/A')[:100]}...")
                else:
                    print(f"[TREE BRANCH] No RAG question found (using general system prompt)")
                    print(f"[TAGS] None")
                    print(f"[RAG QUESTION] None")
                print(f"[USER] {question[:100]}...")
                print(f"[BOT] {full_response[:150]}...")
                print(f"{'='*80}\n")
                
                # ===================================================================
                # DUAL EVALUATION: HealthBench + HELM in parallel (runs AFTER done signal)
                # ===================================================================
                eval_results = None
                helm_results = None
                eval_start_time = time.time()
                
                # Get medical context from RAG
                medical_context = rag_question_info.get('tree_path') if rag_question_info else None
                
                # HEALTHBENCH EVALUATION
                if live_evaluator and live_evaluator.enabled:
                    try:
                        print("[EVALUATION] Starting HealthBench evaluation...")
                        
                        # Evaluate the bot's response
                        eval_results = live_evaluator.evaluate(
                            conversation_history=conversation_history[:-1],  # Exclude the response we're evaluating
                            bot_question=full_response,
                            medical_context=medical_context
                        )
                        
                        if eval_results:
                            # Display evaluation results
                            print(f"[EVALUATION] [OK] Overall Score: {eval_results.overall_score:.2f} "
                                  f"({eval_results.metrics.get('rubrics_passed', 0)}/"
                                  f"{eval_results.metrics.get('num_rubrics_evaluated', 0)} passed)")
                            
                            # Display safety score
                            safety_score = eval_results.safety_score
                            print(f"[EVALUATION] [OK] Safety Score: {safety_score:.2f}")
                            
                            # Display tag scores
                            if eval_results.tag_scores:
                                tag_scores_str = ", ".join([f"{tag}: {score:.2f}" 
                                                            for tag, score in eval_results.tag_scores.items()])
                                print(f"[EVALUATION] Tag Scores: {tag_scores_str}")
                            
                            # Display red flags if any
                            if eval_results.red_flags:
                                print(f"[EVALUATION] [WARNING] {len(eval_results.red_flags)} RED FLAG(S) DETECTED:")
                                for flag in eval_results.red_flags:
                                    print(f"[EVALUATION]   [{flag['severity']}] {flag['criterion']}")
                                    print(f"[EVALUATION]   Reason: {flag['explanation'][:100]}...")
                            
                            # Display critical failure alert
                            if eval_results.critical_failure:
                                print(f"[EVALUATION] [ALERT] CRITICAL SAFETY VIOLATION DETECTED!")
                            
                            # Log scores to Langfuse
                            if langfuse_scorer and trace_id:
                                langfuse_scorer.log_scores(
                                    trace_id=trace_id,
                                    generation_id=generation_id,
                                    eval_results=eval_results,
                                    medical_context=medical_context
                                )
                        else:
                            print("[EVALUATION] [WARNING] Evaluation returned no results")
                            
                    except Exception as eval_error:
                        print(f"[EVALUATION] [WARNING] HealthBench evaluation failed: {eval_error}")
                        import traceback
                        traceback.print_exc()
                
                # HELM EVALUATION (in parallel)
                if helm_evaluator and helm_evaluator.enabled:
                    try:
                        print("[HELM] Starting HELM evaluation...")
                        
                        # Evaluate with HELM criteria
                        helm_results = helm_evaluator.evaluate(
                            conversation_history=conversation_history[:-1],
                            bot_response=full_response,
                            medical_context=medical_context
                        )
                        
                        if helm_results:
                            print(f"[HELM] [OK] Overall: {helm_results.overall_helm_score:.2f}/5.0")
                            print(f"[HELM] Accuracy: {helm_results.accuracy_score}/5, "
                                  f"Completeness: {helm_results.completeness_score}/5, "
                                  f"Clarity: {helm_results.clarity_score}/5")
                            print(f"[HELM] Empathy: {helm_results.empathy_score}/5, "
                                  f"Safety: {helm_results.safety_score}/5, "
                                  f"Relevance: {helm_results.relevance_score}/5")
                        else:
                            print("[HELM] [WARNING] HELM evaluation returned no results")
                    
                    except Exception as helm_error:
                        print(f"[HELM] [WARNING] HELM evaluation failed: {helm_error}")
                        import traceback
                        traceback.print_exc()
                
                # Calculate total evaluation time
                eval_end_time = time.time()
                eval_duration = eval_end_time - eval_start_time
                
                # Send evaluation complete event with timing to frontend
                # Note: This is sent after 'done' signal, but frontend should still be reading
                if (live_evaluator and live_evaluator.enabled) or (helm_evaluator and helm_evaluator.enabled):
                    try:
                        yield f"data: {json.dumps({'type': 'evaluation_complete', 'duration': round(eval_duration, 2)})}\n\n"
                    except:
                        pass  # Ignore if connection is already closed
                
                # Save combined results to storage
                if results_storage and (eval_results or helm_results):
                    try:
                        # Combine HealthBench and HELM results
                        combined_eval = {}
                        
                        if eval_results:
                            combined_eval = eval_results.to_dict()
                        
                        if helm_results:
                            combined_eval['helm'] = helm_results.to_dict()
                        
                        results_storage.save_evaluation(
                            eval_result=combined_eval,
                            conversation_id=session_id,
                            user_message=question,
                            bot_response=full_response,
                            medical_context=medical_context
                        )
                    except Exception as storage_error:
                        print(f"[WARNING] Failed to save combined results: {storage_error}")
                # ===================================================================
                
                # Update Langfuse generation with the complete response (AFTER done signal)
                if langfuse and generation:
                    try:
                        # Update the generation with the output
                        generation.update(
                            output=full_response
                        )
                        # Update trace with final output
                        if trace_obj:
                            try:
                                # Update the trace object directly
                                trace_obj.update(output=full_response)
                            except Exception as trace_error:
                                print(f"[ERROR] Failed to update trace output: {trace_error}")
                        langfuse.flush()  # Ensure data is sent to Langfuse
                        if generation_id:
                            print(f"[LANGFUSE] Generation ID: {generation_id}")
                    except Exception as e:
                        print(f"[ERROR] Failed to update Langfuse trace: {e}")
                        import traceback
                        traceback.print_exc()
                
            except Exception as e:
                error_msg = f"Error calling OpenAI API: {str(e)}"
                
                # Log error to Langfuse if configured
                if langfuse and generation:
                    generation.update(
                        output=None,
                        level="ERROR",
                        status_message=error_msg
                    )
                    langfuse.flush()
                
                yield f"data: {json.dumps({'type': 'error', 'error': error_msg})}\n\n"
        
        return Response(generate(), mimetype='text/event-stream')
    
    except Exception as e:
        # Capture error message before defining nested function (Python 3.13+ scope issue)
        error_msg = str(e)
        def error_response():
            yield f"data: {json.dumps({'type': 'error', 'error': error_msg})}\n\n"
        return Response(error_response(), mimetype='text/event-stream')

@app.route('/chat/history/<user_id>', methods=['GET'])
def get_chat_history(user_id):
    """Get chat history (simplified - no auth required)"""
    # HIPAA Compliance: Validate user_id and session_id
    if not validate_session_id(str(user_id)):
        return jsonify({'error': 'Invalid user ID format'}), 400
    
    session_id = request.args.get('session_id', 'default')
    if not validate_session_id(session_id):
        return jsonify({'error': 'Invalid session ID format'}), 400
    
    if session_id in conversations:
        history = conversations[session_id]
        return jsonify({'history': history})
    
    return jsonify({'history': []})

@app.route('/chat/history/<user_id>', methods=['DELETE'])
def delete_chat_history(user_id):
    """Clear chat history"""
    # HIPAA Compliance: Validate user_id and session_id
    if not validate_session_id(str(user_id)):
        return jsonify({'error': 'Invalid user ID format'}), 400
    
    session_id = request.args.get('session_id', 'default')
    if not validate_session_id(session_id):
        return jsonify({'error': 'Invalid session ID format'}), 400
    
    if session_id in conversations:
        conversations[session_id] = []
    
    return jsonify({'message': 'History cleared'})

@app.route('/feedback', methods=['POST'])
def submit_feedback():
    """Submit user feedback (thumbs up/down) to Langfuse"""
    try:
        # HIPAA Compliance: Rate limiting
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if not check_rate_limit(client_ip):
            return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request: No JSON data provided'}), 400
        
        trace_id = data.get('trace_id')
        if trace_id and not validate_session_id(str(trace_id)):
            return jsonify({'error': 'Invalid trace_id format'}), 400
        
        generation_id = data.get('generation_id')  # Optional generation ID
        if generation_id and not validate_session_id(str(generation_id)):
            return jsonify({'error': 'Invalid generation_id format'}), 400
        
        rating = data.get('rating')  # 'thumbs_up' or 'thumbs_down'
        comment = data.get('comment', '')
        if comment:
            comment = sanitize_input(comment, max_length=500)
        
        print(f"[FEEDBACK] Received feedback request: trace_id={trace_id}, generation_id={generation_id}, rating={rating}")
        print(f"[FEEDBACK] Trace ID type: {type(trace_id)}, value: '{trace_id}'")
        
        if not trace_id or not rating:
            print(f"[FEEDBACK] Missing required fields: trace_id={trace_id}, rating={rating}")
            return jsonify({'error': 'trace_id and rating are required'}), 400
        
        if rating not in ['thumbs_up', 'thumbs_down']:
            print(f"[FEEDBACK] Invalid rating: {rating}")
            return jsonify({'error': 'rating must be "thumbs_up" or "thumbs_down"'}), 400
        
        # Use the tracker to add feedback
        success = langfuse_tracker.add_feedback(trace_id, rating, comment, generation_id)
        
        if success:
            print(f"[FEEDBACK] Successfully logged feedback for trace_id={trace_id}")
            return jsonify({'message': 'Feedback submitted successfully', 'trace_id': trace_id})
        else:
            print(f"[FEEDBACK] Failed to log feedback for trace_id={trace_id}")
            return jsonify({'error': 'Failed to submit feedback'}), 500
            
    except Exception as e:
        print(f"[FEEDBACK] Exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/models', methods=['GET'])
def get_available_models():
    """Get list of available models"""
    if not model_manager:
        return jsonify({'error': 'Model manager not available'}), 503

    models = model_manager.get_available_models()
    active_model = model_manager.get_active_model()

    return jsonify({
        'models': models,
        'active_model': active_model
    })

@app.route('/models/active', methods=['GET'])
def get_active_model():
    """Get currently active model"""
    if not model_manager:
        return jsonify({'error': 'Model manager not available'}), 503

    active_model = model_manager.get_active_model()
    config = model_manager.get_model_config(active_model)

    return jsonify({
        'active_model': active_model,
        'config': config
    })

@app.route('/models/active', methods=['POST'])
def set_active_model():
    """Set active model"""
    if not model_manager:
        return jsonify({'error': 'Model manager not available'}), 503

    data = request.get_json()
    if not data or 'model_id' not in data:
        return jsonify({'error': 'model_id is required'}), 400

    model_id = data['model_id']
    success = model_manager.set_active_model(model_id)

    if success:
        print(f"🔄 Active model changed to: {model_id}")
        return jsonify({
            'success': True,
            'active_model': model_id,
            'message': f'Active model set to {model_id}'
        })
    else:
        return jsonify({
            'success': False,
            'error': f'Model {model_id} not available'
        }), 400

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

@app.route('/rag/rebuild', methods=['POST'])
def rebuild_vector_store():
    """Rebuild the RAG vector store incrementally"""
    global rag_system

    try:
        # Check if RAG system exists
        if rag_system is None:
            return jsonify({'error': 'RAG system not initialized'}), 503

        # Check if rebuild is allowed via environment variable
        rebuild_allowed = os.getenv('REBUILD_VECTORSTORE', 'false').lower() == 'true'
        if not rebuild_allowed:
            return jsonify({
                'error': 'Vector store rebuild not enabled',
                'message': 'Set REBUILD_VECTORSTORE=true in environment to enable rebuilds'
            }), 403

        # Get rebuild model from environment
        rebuild_model = os.getenv('RAG_REBUILD_MODEL', 'text-embedding-3-small')

        print(f"[RAG] Starting incremental rebuild using model: {rebuild_model}")

        # Force rebuild embeddings incrementally
        rag_system.create_embeddings(force_rebuild=True, rebuild_model=rebuild_model)

        # Get updated stats
        count = rag_system.collection.count() if rag_system.collection else 0

        return jsonify({
            'success': True,
            'message': f'Vector store rebuilt successfully',
            'embeddings_count': count,
            'questions_count': len(rag_system.questions),
            'rebuild_model': rebuild_model
        })

    except Exception as e:
        print(f"[RAG] Rebuild failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Rebuild failed: {str(e)}'}), 500

@app.route('/rag/status', methods=['GET'])
def get_rag_status():
    """Get RAG system status"""
    if rag_system is None:
        return jsonify({
            'initialized': False,
            'questions_count': 0,
            'embeddings_count': 0
        })

    count = rag_system.collection.count() if rag_system.collection else 0
    return jsonify({
        'initialized': True,
        'questions_count': len(rag_system.questions),
        'embeddings_count': count,
        'collection_name': rag_system.collection.name if rag_system.collection else None
    })

@app.route('/session/<session_id>/data', methods=['GET'])
def get_session_data(session_id):
    """
    Get structured medical data for a session (for doctor/provider access).
    Returns only structured data, NOT full chat history.
    
    Each session_id has its own unique data document in MongoDB.
    FUTURE: After auth, this endpoint will use user_id instead of session_id.
    
    Args:
        session_id: Unique session identifier
    
    Returns:
        JSON with structured medical data (HPI, ROS, Past History, Red Flags)
    """
    # HIPAA Compliance: Validate session_id
    if not validate_session_id(session_id):
        return jsonify({'error': 'Invalid session ID format'}), 400
    
    session_data = get_or_create_session_data(session_id)
    if not session_data:
        return jsonify({'error': 'Session not found'}), 404
    
    # Remove MongoDB internal fields and convert datetime to ISO format
    response_data = {
        'session_id': session_data.get('session_id'),
        'complaint_name': session_data.get('complaint_name'),
        'hpi': session_data.get('hpi', {}),
        'ros': session_data.get('ros', {}),
        'past_history': session_data.get('past_history', {}),
        'red_flags': session_data.get('red_flags', []),
        'created_at': session_data.get('created_at').isoformat() if isinstance(session_data.get('created_at'), datetime) else session_data.get('created_at'),
        'updated_at': session_data.get('updated_at').isoformat() if isinstance(session_data.get('updated_at'), datetime) else session_data.get('updated_at')
    }
    
    return jsonify(response_data)

@app.route('/voice/transcribe', methods=['POST', 'OPTIONS'])
def transcribe_voice():
    """
    Transcribe audio to text using Whisper.
    HIPAA Compliant: Audio processed locally, deleted immediately after.
    """
    # Handle OPTIONS preflight request
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        # HIPAA Compliance: Rate limiting
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if not check_rate_limit(client_ip):
            return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429
        
        # Check if voice is available
        if not VOICE_AVAILABLE:
            return jsonify({'error': 'Voice processing not available'}), 503
        
        stt_available, _ = voice_processor.is_voice_available()
        if not stt_available:
            return jsonify({'error': 'Speech-to-text not available'}), 503
        
        # Check if audio file is present
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'error': 'Empty audio file'}), 400
        
        # Validate session_id
        session_id = request.form.get('session_id', 'default')
        if not validate_session_id(session_id):
            return jsonify({'error': 'Invalid session ID format'}), 400
        
        # Save uploaded audio to temp file
        import tempfile
        temp_fd, temp_audio_path = tempfile.mkstemp(suffix='.webm')
        os.close(temp_fd)
        
        try:
            # Save uploaded file
            audio_file.save(temp_audio_path)
            
            # Check file size (max 10MB for safety)
            file_size = os.path.getsize(temp_audio_path)
            max_size = int(os.getenv('MAX_AUDIO_SIZE', '10485760'))  # 10MB default
            if file_size > max_size:
                return jsonify({'error': 'Audio file too large'}), 413
            
            # Transcribe audio
            transcription = voice_processor.transcribe_audio(temp_audio_path)
            
            if transcription is None:
                return jsonify({'error': 'Transcription failed'}), 500
            
            # Log voice usage (HIPAA: metadata only, no PHI)
            print(f"[Voice] Transcription for session {session_id}: {len(transcription)} chars")
            
            return jsonify({
                'text': transcription,
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            })
            
        finally:
            # HIPAA Compliance: Delete temp file immediately
            voice_processor.cleanup_temp_file(temp_audio_path)
    
    except Exception as e:
        print(f"[Voice] Transcription error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/voice/synthesize', methods=['POST', 'OPTIONS'])
def synthesize_voice():
    """
    Convert text to speech using pyttsx3.
    HIPAA Compliant: Audio generated locally, no storage.
    """
    # Handle OPTIONS preflight request
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        print(f"[Voice] TTS endpoint called")
        
        # HIPAA Compliance: Rate limiting
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if not check_rate_limit(client_ip):
            return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429
        
        # Check if voice is available
        if not VOICE_AVAILABLE:
            return jsonify({'error': 'Voice processing not available'}), 503
        
        _, tts_available = voice_processor.is_voice_available()
        if not tts_available:
            return jsonify({'error': 'Text-to-speech not available'}), 503
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        text = data.get('text', '')
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        # Sanitize and validate text
        text = sanitize_input(text, max_length=5000)
        if not text:
            return jsonify({'error': 'Invalid text format'}), 400
        
        # Validate session_id
        session_id = data.get('session_id', 'default')
        if not validate_session_id(session_id):
            return jsonify({'error': 'Invalid session ID format'}), 400
        
        # Synthesize speech
        audio_bytes = voice_processor.synthesize_speech(text)
        
        if audio_bytes is None:
            return jsonify({'error': 'Speech synthesis failed'}), 500
        
        # Log voice usage (HIPAA: metadata only, no PHI)
        print(f"[Voice] TTS for session {session_id}: {len(text)} chars -> {len(audio_bytes)} bytes")
        
        # Return audio file
        import io
        audio_io = io.BytesIO(audio_bytes)
        audio_io.seek(0)
        
        return send_file(
            audio_io,
            mimetype='audio/wav',
            as_attachment=False,
            download_name='speech.wav'
        )
    
    except Exception as e:
        print(f"[Voice] TTS error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/voice/status', methods=['GET'])
def voice_status():
    """Get voice processing system status"""
    if not VOICE_AVAILABLE:
        return jsonify({
            'available': False,
            'error': 'Voice processing not available'
        })
    
    status = voice_processor.get_voice_status()
    return jsonify(status)

@app.route('/healthbench/results', methods=['GET'])
def get_healthbench_results():
    """
    API endpoint to get HealthBench evaluation results for dashboard.
    
    Query Parameters:
        limit (int): Maximum number of results to return (default: 50)
        
    Returns:
        JSON with evaluation results and statistics
    """
    try:
        if not results_storage:
            return jsonify({
                'error': 'HealthBench evaluation not available',
                'results': [],
                'statistics': {}
            }), 503
        
        # Get limit from query parameters
        limit = request.args.get('limit', 50, type=int)
        
        # Get recent results
        recent_results = results_storage.get_recent_evaluations(limit=limit)
        
        # Get statistics
        statistics = results_storage.get_statistics()
        
        # Create response with cache-busting headers
        response = jsonify({
            'success': True,
            'results': recent_results,
            'statistics': statistics,
            'total_count': len(recent_results)
        })
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    
    except Exception as e:
        print(f"[ERROR] Failed to retrieve HealthBench results: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'results': [],
            'statistics': {}
        }), 500


@app.route('/healthbench/dashboard', methods=['GET'])
def healthbench_dashboard():
    """
    Serve the HealthBench evaluation dashboard HTML page.
    """
    try:
        # Serve the V3 dashboard with all scores displayed prominently
        dashboard_path = Path(__file__).parent / 'healthbench_dashboard_v3.html'
        
        if not dashboard_path.exists():
            dashboard_path = Path(__file__).parent / 'healthbench_dashboard_clean.html'
        
        if not dashboard_path.exists():
            dashboard_path = Path(__file__).parent / 'healthbench_dashboard.html'
        
        if not dashboard_path.exists():
            return f"<h1>Dashboard not found</h1><p>Please ensure dashboard file exists in the HYoda folder.</p>", 404
        
        # Send file with cache-busting headers to prevent browser caching
        response = send_file(dashboard_path)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        # Override CSP for dashboard to allow inline styles and scripts
        # Dashboard is internal tool, not patient-facing, so this is acceptable
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline'; connect-src 'self' https://167.71.238.114 http://127.0.0.1:8002 http://localhost:8002"
        
        return response
    
    except Exception as e:
        print(f"[ERROR] Failed to serve dashboard: {e}")
        import traceback
        traceback.print_exc()
        return f"<h1>Error</h1><p>{str(e)}</p>", 500

@app.route('/', methods=['GET'])
def index():
    """
    Landing page with links to chatbot and dashboard.
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>HealthYoda - Medical Chatbot System</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
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
            .links {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 30px;
            }
            .link-card {
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                padding: 40px 30px;
                border-radius: 15px;
                text-decoration: none;
                transition: transform 0.3s, box-shadow 0.3s;
                border: 2px solid transparent;
            }
            .link-card:hover {
                transform: translateY(-10px);
                box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
                border-color: #667eea;
            }
            .link-card h2 {
                font-size: 32px;
                margin-bottom: 15px;
            }
            .link-card p {
                color: #34495e;
                font-size: 16px;
                margin-bottom: 0;
            }
            .chatbot-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }
            .chatbot-card h2, .chatbot-card p {
                color: white;
            }
            .dashboard-card h2 {
                color: #667eea;
            }
            @media (max-width: 768px) {
                .links {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏥 HealthYoda</h1>
            <p>AI-Powered Medical Interview Assistant with Real-Time Quality Evaluation</p>
            
            <div class="links">
                <a href="/index.html" class="link-card chatbot-card">
                    <h2>🤖 Chatbot</h2>
                    <p>Start medical interview</p>
                </a>
                
                <a href="/healthbench/dashboard" class="link-card dashboard-card">
                    <h2>📊 Dashboard</h2>
                    <p>View evaluation results</p>
                </a>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Create response with modified CSP headers to allow inline styles and marked.js CDN
    from flask import make_response
    response = make_response(html_content)
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline'; connect-src 'self' https://167.71.238.114 http://127.0.0.1:8002 http://localhost:8002"
    return response

@app.route('/index.html', methods=['GET'])
def chatbot_interface():
    """
    Serve the main chatbot interface HTML page.
    """
    try:
        chatbot_path = Path(__file__).parent / 'index.html'
        
        if not chatbot_path.exists():
            return f"<h1>Chatbot Interface not found</h1><p>Please ensure index.html exists in the HYoda folder.</p>", 404
        
        # Send file with cache-busting and relaxed CSP headers
        response = send_file(chatbot_path)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        # Allow inline styles and scripts for chatbot UI, and marked.js CDN
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline'; connect-src 'self' https://167.71.238.114 http://127.0.0.1:8002 http://localhost:8002; img-src 'self' data: blob:; media-src 'self' blob:"
        
        return response
    
    except Exception as e:
        print(f"[ERROR] Failed to serve chatbot interface: {e}")
        import traceback
        traceback.print_exc()
        return f"<h1>Error</h1><p>{str(e)}</p>", 500

if __name__ == '__main__':
    # Only print startup messages once (not on reload)
    # RAG system is initialized above based on process detection
    
    if not hasattr(app, '_startup_printed'):
        print("Starting HealthYoda chatbot server...")
        print("Server will run on http://127.0.0.1:8002")
        print("-" * 50)
        
        if not openai_api_key:
            print("\n[WARNING] OPENAI_API_KEY not set!")
            print("Set it using: export OPENAI_API_KEY='your-api-key'")
            print("Or create a .env file with OPENAI_API_KEY=your-api-key")
            print("The chatbot will not work without an API key.\n")
        else:
            print("[OK] OpenAI API key found!")
        
        if not langfuse:
            print("[WARNING] Langfuse keys not found. Traces will not be logged.")
            print("Set LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, and LANGFUSE_HOST in .env")
        else:
            print("[OK] Langfuse configured! Traces will be logged.")
            print(f"   Using Langfuse tracker module for observability")
        
        # Show HealthBench dashboard status
        if results_storage:
            print("[OK] HealthBench Dashboard: http://127.0.0.1:8002/healthbench/dashboard")
            print("   View real-time evaluation scores and metrics")
        
        if not mongodb_connected:
            print("⚠️  MongoDB not connected. Session data will not be persisted.")
            print("   Set MONGODB_URI in .env to enable MongoDB (e.g., mongodb://localhost:27017/)")
            print("   Bot will still work but won't prevent duplicate questions.")
        else:
            print("✅ MongoDB connected! Session data will be persisted.")
            print(f"   Database: {os.getenv('MONGODB_DB', 'healthyoda')}")
            print(f"   Collection: patient_sessions")
        
        # Voice status
        if VOICE_AVAILABLE:
            stt_ok, tts_ok = voice_processor.is_voice_available()
            if stt_ok and tts_ok:
                print("✅ Voice processing enabled! (STT + TTS)")
            elif stt_ok:
                print("⚠️  Voice processing partially enabled (STT only)")
            elif tts_ok:
                print("⚠️  Voice processing partially enabled (TTS only)")
            else:
                print("⚠️  Voice processing available but not initialized")
                print("   Set VOICE_ENABLED=true in .env to enable")
        else:
            print("⚠️  Voice processing not available")
            print("   Install: pip install faster-whisper piper-tts")
        
        print("-" * 50)
        app._startup_printed = True
    
    app.run(host='127.0.0.1', port=8002, debug=False)

