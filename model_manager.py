"""
Model Manager for HealthYoda
Supports switching between OpenAI, Ollama, and Google Gemini models
"""
import os
import json
from typing import Dict, Any, Optional, List
from openai import OpenAI

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    print("⚠️  ollama package not installed - Ollama models disabled")

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  google-generativeai package not installed - Gemini models disabled")

class ModelManager:
    """
    Manages multiple AI models (OpenAI, Ollama) with easy switching
    """

    def __init__(self):
        self.openai_client = None
        self.ollama_client = None
        self.gemini_client = None
        self.available_models = {}
        self.active_model = None
        self.model_configs = {}

        self._initialize_clients()
        self._load_model_configs()
        self._set_default_model()

    def _initialize_clients(self):
        """Initialize OpenAI, Ollama, and Gemini clients"""
        # Initialize OpenAI client
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            try:
                self.openai_client = OpenAI(api_key=openai_key)
                print("✅ OpenAI client initialized")
            except Exception as e:
                print(f"⚠️  OpenAI client initialization failed: {e}")

        # Initialize Gemini client
        if GEMINI_AVAILABLE:
            gemini_key = os.getenv('GEMINI_API_KEY')
            if gemini_key:
                try:
                    genai.configure(api_key=gemini_key)
                    self.gemini_client = genai
                    print("✅ Gemini client initialized")
                except Exception as e:
                    print(f"⚠️  Gemini client initialization failed: {e}")
            else:
                print("⚠️  GEMINI_API_KEY not found in environment")

        # Initialize Ollama client
        if OLLAMA_AVAILABLE:
            try:
                ollama_base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
                ollama_api_key = os.getenv('OLLAMA_API_KEY', 'ollama')

                # Configure Ollama client
                self.ollama_client = ollama.Client(host=ollama_base_url, headers={'Authorization': f'Bearer {ollama_api_key}'})

                # Test connection
                self.ollama_client.list()
                print("✅ Ollama client initialized")
            except Exception as e:
                print(f"⚠️  Ollama client initialization failed: {e}")
                self.ollama_client = None

    def _load_model_configs(self):
        """Load available model configurations - GPT-4o Mini, Gemini models, and MedGemma"""
        self.model_configs = {
            # GPT-4o Mini from OpenAI
            'gpt-4o-mini': {
                'provider': 'openai',
                'model_name': 'gpt-4o-mini',
                'display_name': 'GPT-4o Mini (OpenAI)',
                'context_window': 128000,
                'supports_embeddings': False,
                'supports_chat': True
            }
        }

        # Add Gemini models if available
        if self.gemini_client:
            # Gemini 3 Pro - Fastest, free tier 300M tokens
            self.model_configs['gemini-3-pro-preview'] = {
                'provider': 'gemini',
                'model_name': 'gemini-3-pro-preview',
                'display_name': 'Gemini 3 Pro (Google) - FREE 300M',
                'context_window': 1000000,  # 1M tokens
                'supports_embeddings': False,
                'supports_chat': True
            }
            self.available_models['gemini-3-pro-preview'] = self.model_configs['gemini-3-pro-preview']
            print("✅ Gemini 3 Pro added to available models")
            
            # Gemini 1.5 Flash - Cheapest & Fast
            self.model_configs['gemini-1.5-flash'] = {
                'provider': 'gemini',
                'model_name': 'gemini-1.5-flash',
                'display_name': 'Gemini 1.5 Flash (Google) - Cheapest',
                'context_window': 1000000,  # 1M tokens
                'supports_embeddings': False,
                'supports_chat': True
            }
            self.available_models['gemini-1.5-flash'] = self.model_configs['gemini-1.5-flash']
            print("✅ Gemini 1.5 Flash added to available models")

        # Add MedGemma from Ollama if available
        if self.ollama_client:
            try:
                ollama_models = self.ollama_client.list()
                medgemma_found = False
                for model_info in ollama_models.get('models', []):
                    model_name = model_info['name']
                    # Only add MedGemma model
                    if 'medgemma' in model_name.lower():
                        self.model_configs[model_name] = {
                            'provider': 'ollama',
                            'model_name': model_name,
                            'display_name': f'MedGemma (Ollama)',
                            'context_window': 4096,  # Default, can be overridden
                            'supports_embeddings': False,  # Ollama doesn't have built-in embeddings
                            'supports_chat': True
                        }
                        # Add to available models since it's a chat model
                        self.available_models[model_name] = self.model_configs[model_name]
                        print(f"✅ Found MedGemma model: {model_name}")
                        medgemma_found = True
                        break  # Only add one MedGemma model

                if not medgemma_found:
                    expected_model = os.getenv('OLLAMA_MODEL', 'alibayram/medgemma:4b')
                    print(f"⚠️  MedGemma model not found in Ollama. Expected model: {expected_model}")
                    print("   Make sure Ollama is running and the model is installed:")
                    print(f"   1. Pull model: ollama pull {expected_model}")
                    print("   2. List models: ollama list")

            except Exception as e:
                ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
                print(f"⚠️  Cannot connect to Ollama at {ollama_url}")
                print(f"   Error: {e}")
                print("   For development, you can:")
                print("   1. Install Ollama locally: https://ollama.com/download")
                print("   2. Start Ollama: ollama serve")
                print(f"   3. Pull model: ollama pull {os.getenv('OLLAMA_MODEL', 'alibayram/medgemma:4b')}")
                print("   4. Or deploy to server where Ollama is running")

        # Filter available models based on initialized clients
        self.available_models = {}
        for model_id, config in self.model_configs.items():
            if config['provider'] == 'openai' and self.openai_client:
                self.available_models[model_id] = config
            elif config['provider'] == 'gemini' and self.gemini_client:
                self.available_models[model_id] = config
            elif config['provider'] == 'ollama' and self.ollama_client:
                self.available_models[model_id] = config

        # Always add text-embedding-3-small if OpenAI is available (for internal RAG use only)
        # This model is NOT exposed to users in the UI - it's only used internally for embeddings
        if self.openai_client:
            embedding_config = {
                'provider': 'openai',
                'model_name': 'text-embedding-3-small',
                'display_name': 'Text Embedding 3 Small (OpenAI)',
                'context_window': 8191,
                'supports_embeddings': True,
                'supports_chat': False
            }
            self.model_configs['text-embedding-3-small'] = embedding_config
            # NOTE: NOT adding to available_models - this is internal only

        print(f"📋 Available models: {list(self.available_models.keys())}")

    def _set_default_model(self):
        """Set default active model - prefer GPT-4o Mini, fallback to Gemini models"""
        # Try to set from environment variable
        default_model = os.getenv('DEFAULT_MODEL', 'gpt-4o-mini')

        # If the requested default is available, use it
        if default_model in self.available_models:
            self.active_model = default_model
            print(f"🎯 Default model set to: {self.active_model}")
        else:
            # Fallback priority: GPT-4o Mini > Gemini 1.5 Flash > Gemini 3 Pro > MedGemma
            if 'gpt-4o-mini' in self.available_models:
                self.active_model = 'gpt-4o-mini'
                print(f"🎯 Default model set to: {self.active_model}")
            elif 'gemini-1.5-flash' in self.available_models:
                self.active_model = 'gemini-1.5-flash'
                print(f"🎯 Default model set to: {self.active_model} (Cheapest & Fast!)")
            elif 'gemini-3-pro-preview' in self.available_models:
                self.active_model = 'gemini-3-pro-preview'
                print(f"🎯 Default model set to: {self.active_model} (FREE 300M tokens!)")
            elif any('medgemma' in model_id.lower() for model_id in self.available_models):
                medgemma_model = next(model_id for model_id in self.available_models if 'medgemma' in model_id.lower())
                self.active_model = medgemma_model
                print(f"🎯 Default model set to: {self.active_model}")
            elif self.available_models:
                self.active_model = list(self.available_models.keys())[0]
                print(f"🎯 Fallback model set to: {self.active_model}")
            else:
                print("⚠️  No models available!")
                self.active_model = None

    def get_available_models(self) -> Dict[str, Dict]:
        """Get list of available models"""
        return self.available_models

    def get_active_model(self) -> Optional[str]:
        """Get currently active model"""
        return self.active_model

    def set_active_model(self, model_id: str) -> bool:
        """Set active model"""
        if model_id in self.available_models:
            self.active_model = model_id
            print(f"🔄 Active model changed to: {model_id}")
            return True
        return False

    def get_model_config(self, model_id: Optional[str] = None) -> Optional[Dict]:
        """Get configuration for a specific model"""
        model_id = model_id or self.active_model
        return self.available_models.get(model_id)

    def create_chat_completion(self, messages: List[Dict], **kwargs) -> Any:
        """Create chat completion using active model"""
        if not self.active_model:
            raise ValueError("No active model set")

        config = self.get_model_config()
        if not config:
            raise ValueError(f"Model config not found for {self.active_model}")

        if config['provider'] == 'openai':
            return self._openai_chat_completion(config, messages, **kwargs)
        elif config['provider'] == 'gemini':
            return self._gemini_chat_completion(config, messages, **kwargs)
        elif config['provider'] == 'ollama':
            return self._ollama_chat_completion(config, messages, **kwargs)
        else:
            raise ValueError(f"Unsupported provider: {config['provider']}")

    def create_embeddings(self, texts: List[str], **kwargs) -> Any:
        """Create embeddings using available embedding model (always uses text-embedding-3-small)"""
        # For embeddings, always use text-embedding-3-small if available
        # regardless of the active chat model
        embedding_config = self.model_configs.get('text-embedding-3-small')

        if not embedding_config or not self.openai_client:
            raise ValueError("Embedding model (text-embedding-3-small) not available. OpenAI client required for embeddings.")

        return self._openai_embeddings(embedding_config, texts, **kwargs)

    def _openai_chat_completion(self, config: Dict, messages: List[Dict], **kwargs) -> Any:
        """OpenAI chat completion"""
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized")

        # Set default parameters
        params = {
            'model': config['model_name'],
            'messages': messages,
            'temperature': kwargs.get('temperature', 0.7),
            'max_tokens': kwargs.get('max_tokens', 1000),
            'stream': kwargs.get('stream', False)
        }

        # Add optional parameters
        if 'stream' in kwargs:
            params['stream'] = kwargs['stream']

        return self.openai_client.chat.completions.create(**params)

    def _gemini_chat_completion(self, config: Dict, messages: List[Dict], **kwargs) -> Any:
        """Gemini chat completion"""
        if not self.gemini_client:
            raise ValueError("Gemini client not initialized")

        # Convert OpenAI format to Gemini format
        gemini_messages = []
        system_instruction = None
        
        for msg in messages:
            if msg['role'] == 'system':
                system_instruction = msg['content']
            elif msg['role'] == 'user':
                gemini_messages.append({
                    'role': 'user',
                    'parts': [msg['content']]
                })
            elif msg['role'] == 'assistant':
                gemini_messages.append({
                    'role': 'model',
                    'parts': [msg['content']]
                })

        # Create Gemini model instance
        model = self.gemini_client.GenerativeModel(
            model_name=config['model_name'],
            system_instruction=system_instruction
        )

        # Check if streaming
        if kwargs.get('stream', False):
            # Streaming response
            generation_config = {
                'temperature': kwargs.get('temperature', 0.7),
                'max_output_tokens': kwargs.get('max_tokens', 1000),
            }
            
            response = model.generate_content(
                gemini_messages,
                generation_config=generation_config,
                stream=True
            )
            
            # Create OpenAI-compatible streaming response
            return self._gemini_to_openai_stream(response)
        else:
            # Non-streaming response
            generation_config = {
                'temperature': kwargs.get('temperature', 0.7),
                'max_output_tokens': kwargs.get('max_tokens', 1000),
            }
            
            response = model.generate_content(
                gemini_messages,
                generation_config=generation_config
            )
            
            # Create OpenAI-compatible response
            return self._gemini_to_openai_response(response)

    def _gemini_to_openai_stream(self, gemini_stream):
        """Convert Gemini streaming response to OpenAI format"""
        try:
            for chunk in gemini_stream:
                try:
                    if chunk.text:
                        # Create OpenAI-compatible chunk
                        yield type('obj', (object,), {
                            'choices': [type('obj', (object,), {
                                'delta': type('obj', (object,), {
                                    'content': chunk.text
                                })(),
                                'index': 0,
                                'finish_reason': None
                            })()]
                        })()
                except Exception as chunk_error:
                    print(f"[GEMINI STREAM] Error processing chunk: {chunk_error}")
                    # Check if chunk has error info
                    if hasattr(chunk, 'candidates') and chunk.candidates:
                        print(f"[GEMINI STREAM] Chunk candidates: {chunk.candidates}")
                    continue  # Skip this chunk and continue
        except Exception as stream_error:
            print(f"[GEMINI STREAM] Stream error: {stream_error}")
            import traceback
            traceback.print_exc()

    def _gemini_to_openai_response(self, gemini_response):
        """Convert Gemini response to OpenAI format"""
        return type('obj', (object,), {
            'choices': [type('obj', (object,), {
                'message': type('obj', (object,), {
                    'content': gemini_response.text,
                    'role': 'assistant'
                })(),
                'index': 0,
                'finish_reason': 'stop'
            })()],
            'model': 'gemini-2.0-flash-exp'
        })()

    def _ollama_chat_completion(self, config: Dict, messages: List[Dict], **kwargs) -> Any:
        """Ollama chat completion"""
        if not self.ollama_client:
            raise ValueError("Ollama client not initialized")

        # Convert OpenAI format to Ollama format
        ollama_messages = []
        for msg in messages:
            ollama_messages.append({
                'role': msg['role'],
                'content': msg['content']
            })

        params = {
            'model': config['model_name'],
            'messages': ollama_messages,
            'stream': kwargs.get('stream', False),
            'options': {
                'temperature': kwargs.get('temperature', 0.7),
                'num_predict': kwargs.get('max_tokens', 1000),
            }
        }

        return self.ollama_client.chat(**params)

    def _openai_embeddings(self, config: Dict, texts: List[str], **kwargs) -> Any:
        """OpenAI embeddings"""
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized")

        return self.openai_client.embeddings.create(
            model=config['model_name'],
            input=texts
        )


# Global instance
model_manager = ModelManager()

def get_model_manager() -> ModelManager:
    """Get the global model manager instance"""
    return model_manager
