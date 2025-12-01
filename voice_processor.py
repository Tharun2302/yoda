"""
Voice Processing Module for HealthYoda
Handles Speech-to-Text (STT) and Text-to-Speech (TTS) using local models
HIPAA Compliant: All processing done locally, no third-party services
"""
import os
import tempfile
import io
import subprocess
from pathlib import Path
from typing import Optional, Tuple
import wave
import threading

try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("[WARNING] faster-whisper not available - voice transcription disabled")

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    print("[WARNING] pyttsx3 not available - voice synthesis disabled")

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    # pydub not available, but we can use ffmpeg directly

# Cache for ffmpeg path (found at runtime)
_ffmpeg_path = None

def find_ffmpeg_path() -> Optional[str]:
    """Find ffmpeg executable path. Returns path if found, None otherwise."""
    global _ffmpeg_path
    
    # Return cached path if already found
    if _ffmpeg_path and os.path.exists(_ffmpeg_path):
        return _ffmpeg_path
    
    # Try to find ffmpeg in PATH using shell
    try:
        # On Windows, use 'where' command to find ffmpeg
        result = subprocess.run(
            'where ffmpeg' if os.name == 'nt' else 'which ffmpeg',
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            path = result.stdout.strip().split('\n')[0].strip()
            if os.path.exists(path):
                _ffmpeg_path = path
                return path
    except Exception:
        pass
    
    # Fallback: Check common installation paths
    common_paths = [
        r"C:\Users\SudityaNimmala\Downloads\ffmpeg-8.0.1-essentials_build\ffmpeg-8.0.1-essentials_build\bin\ffmpeg.exe",
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            _ffmpeg_path = path
            return path
    
    return None

# Function to check if ffmpeg is available (called at runtime, not import time)
def check_ffmpeg_available() -> bool:
    """Check if ffmpeg is available."""
    return find_ffmpeg_path() is not None

# Check at startup (but will re-check at runtime if needed)
FFMPEG_AVAILABLE = check_ffmpeg_available()
if FFMPEG_AVAILABLE:
    print("[OK] ffmpeg found in PATH - audio preprocessing enabled")
else:
    print("[WARNING] ffmpeg not found in PATH - audio preprocessing will be limited")

# Global variables for models (loaded once at startup)
whisper_model = None
tts_engine = None
voice_initialized = False
tts_lock = threading.Lock()  # Thread safety for pyttsx3

def initialize_whisper(model_size: str = "tiny.en") -> bool:
    """
    Initialize Whisper model for speech-to-text.
    
    Args:
        model_size: Model size (tiny.en, base.en, small.en, medium.en, large)
                   tiny.en: Fastest, ~1-2s on CPU
                   base.en: Good balance, ~3-5s on CPU
    
    Returns:
        True if successful, False otherwise
    """
    global whisper_model
    
    if not WHISPER_AVAILABLE:
        print("[WARNING] Whisper not available")
        return False
    
    try:
        print(f"Loading Whisper model '{model_size}'...")
        # Use CPU with int8 for faster inference
        whisper_model = WhisperModel(
            model_size, 
            device="cpu",
            compute_type="int8"  # Faster on CPU
        )
        print(f"[OK] Whisper model '{model_size}' loaded successfully")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to load Whisper model: {e}")
        whisper_model = None
        return False

def initialize_pyttsx3() -> bool:
    """
    Initialize pyttsx3 TTS engine for text-to-speech.
    Uses system voices (Windows SAPI, Mac NSSpeechSynthesizer, etc.)
    
    Returns:
        True if successful, False otherwise
    """
    global tts_engine
    
    if not PYTTSX3_AVAILABLE:
        print("[WARNING] pyttsx3 not available")
        return False
    
    try:
        print(f"Loading pyttsx3 TTS engine...")
        
        # Initialize pyttsx3 engine
        tts_engine = pyttsx3.init()
        
        # Configure speech properties
        tts_engine.setProperty('rate', 150)  # Speed (words per minute, default 200)
        tts_engine.setProperty('volume', 1.0)  # Volume (0.0 to 1.0)
        
        # Try to set a better voice if available (Windows SAPI voices)
        voices = tts_engine.getProperty('voices')
        if voices:
            # Prefer female voice or clearest voice
            for voice in voices:
                if 'zira' in voice.name.lower() or 'david' in voice.name.lower():
                    tts_engine.setProperty('voice', voice.id)
                    print(f"   Using voice: {voice.name}")
                    break
            else:
                # Use first available voice
                tts_engine.setProperty('voice', voices[0].id)
                print(f"   Using voice: {voices[0].name}")
        
        print(f"[OK] pyttsx3 TTS engine loaded successfully")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to load pyttsx3 engine: {e}")
        tts_engine = None
        return False

def initialize_voice_system(whisper_model_size: str = None) -> Tuple[bool, bool]:
    """
    Initialize both Whisper and pyttsx3 systems.
    
    Args:
        whisper_model_size: Whisper model size (default from env or tiny.en)
    
    Returns:
        Tuple of (whisper_success, tts_success)
    """
    global voice_initialized
    
    # Get model names from environment or use defaults
    whisper_size = whisper_model_size or os.getenv('WHISPER_MODEL', 'tiny.en')
    
    print("Initializing voice processing system...")
    print(f"Whisper model: {whisper_size}")
    print(f"TTS engine: pyttsx3 (system voices)")
    
    whisper_ok = initialize_whisper(whisper_size)
    tts_ok = initialize_pyttsx3()
    
    voice_initialized = whisper_ok or tts_ok
    
    if whisper_ok and tts_ok:
        print("[OK] Voice system fully initialized (STT + TTS)")
    elif whisper_ok:
        print("[WARNING] Voice system partially initialized (STT only)")
    elif tts_ok:
        print("[WARNING] Voice system partially initialized (TTS only)")
    else:
        print("[ERROR] Voice system initialization failed")
    
    return whisper_ok, tts_ok

def preprocess_audio(audio_file_path: str) -> Optional[str]:
    """
    Preprocess audio file for better transcription accuracy using ffmpeg.
    - Converts WebM/Opus to WAV format
    - Normalizes audio volume
    - Converts to mono channel
    - Sets sample rate to 16kHz (Whisper's optimal)
    
    Args:
        audio_file_path: Path to input audio file
    
    Returns:
        Path to preprocessed WAV file, or original path if preprocessing fails
    """
    # Try pydub first (if available and working)
    if PYDUB_AVAILABLE:
        try:
            print(f"[Preprocess] Using pydub for preprocessing: {audio_file_path}")
            
            # Load audio file (pydub handles WebM, MP3, WAV, etc.)
            audio = AudioSegment.from_file(audio_file_path)
            
            # Get original properties
            original_channels = audio.channels
            original_sample_rate = audio.frame_rate
            original_dBFS = audio.dBFS
            
            print(f"[Preprocess] Original: {original_channels}ch, {original_sample_rate}Hz, {original_dBFS:.1f}dBFS")
            
            # Convert to mono if stereo
            if original_channels > 1:
                audio = audio.set_channels(1)
                print(f"[Preprocess] Converted to mono")
            
            # Normalize audio (prevent too quiet/loud)
            # Target: -20dBFS (good balance, not too loud)
            target_dBFS = -20.0
            change_in_dBFS = target_dBFS - audio.dBFS
            if abs(change_in_dBFS) > 1.0:  # Only normalize if difference is significant
                audio = audio.apply_gain(change_in_dBFS)
                print(f"[Preprocess] Normalized: {audio.dBFS:.1f}dBFS")
            
            # Convert to 16kHz sample rate (Whisper's optimal)
            target_sample_rate = 16000
            if original_sample_rate != target_sample_rate:
                audio = audio.set_frame_rate(target_sample_rate)
                print(f"[Preprocess] Converted to {target_sample_rate}Hz")
            
            # Create temporary WAV file for preprocessed audio
            temp_fd, preprocessed_path = tempfile.mkstemp(suffix='.wav')
            os.close(temp_fd)
            
            # Export as WAV (16-bit PCM, mono, 16kHz)
            audio.export(preprocessed_path, format="wav", parameters=["-ac", "1", "-ar", "16000"])
            
            file_size = os.path.getsize(preprocessed_path)
            print(f"[Preprocess] Preprocessed audio saved: {file_size} bytes")
            
            return preprocessed_path
        except Exception as e:
            print(f"[WARNING] pydub preprocessing failed: {e}, falling back to ffmpeg")
    
    # Fallback to ffmpeg directly (works without pydub)
    # Re-check ffmpeg availability at runtime (in case PATH was updated)
    ffmpeg_available = check_ffmpeg_available()
    if ffmpeg_available:
        try:
            print(f"[Preprocess] Using ffmpeg for preprocessing: {audio_file_path}")
            
            # Create temporary WAV file for preprocessed audio
            temp_fd, preprocessed_path = tempfile.mkstemp(suffix='.wav')
            os.close(temp_fd)
            
            # Find ffmpeg path
            ffmpeg_path = find_ffmpeg_path()
            if not ffmpeg_path:
                print("[WARNING] ffmpeg path not found")
                return audio_file_path
            
            # ffmpeg command to:
            # - Convert to WAV format
            # - Convert to mono (-ac 1)
            # - Set sample rate to 16kHz (-ar 16000)
            # - Normalize audio (loudnorm filter for better quality)
            # - Use 16-bit PCM encoding
            ffmpeg_cmd = [
                ffmpeg_path,
                '-i', audio_file_path,  # Input file
                '-ac', '1',             # Mono channel
                '-ar', '16000',         # 16kHz sample rate
                '-af', 'loudnorm=I=-20:TP=-1.5:LRA=11',  # Normalize to -20dBFS
                '-sample_fmt', 's16',    # 16-bit PCM
                '-y',                   # Overwrite output file
                preprocessed_path       # Output file
            ]
            
            result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )
            
            if result.returncode == 0:
                file_size = os.path.getsize(preprocessed_path)
                print(f"[Preprocess] Preprocessed audio saved: {file_size} bytes")
                return preprocessed_path
            else:
                print(f"[WARNING] ffmpeg preprocessing failed: {result.stderr}")
                return audio_file_path
                
        except subprocess.TimeoutExpired:
            print(f"[WARNING] ffmpeg preprocessing timed out")
            return audio_file_path
        except Exception as e:
            print(f"[WARNING] ffmpeg preprocessing error: {e}")
            return audio_file_path
    
    # No preprocessing available
    print("[INFO] No preprocessing available (pydub and ffmpeg both unavailable)")
    return audio_file_path

def transcribe_audio(audio_file_path: str, language: str = "en") -> Optional[str]:
    """
    Transcribe audio file to text using Whisper with optimized parameters.
    
    Args:
        audio_file_path: Path to audio file (WAV, MP3, WebM, etc.)
        language: Language code (default: en for English)
    
    Returns:
        Transcribed text or None if failed
    """
    if not whisper_model:
        print("[ERROR] Whisper model not initialized")
        return None
    
    preprocessed_path = None
    
    try:
        print(f"[STT] Transcribing audio: {audio_file_path}")
        
        # Preprocess audio for better accuracy
        preprocessed_path = preprocess_audio(audio_file_path)
        transcription_path = preprocessed_path if preprocessed_path != audio_file_path else audio_file_path
        
        # Transcribe with optimized Whisper parameters
        segments, info = whisper_model.transcribe(
            transcription_path,
            language=language,
            beam_size=10,  # Increased from 5 for better accuracy
            temperature=0.0,  # Deterministic, more accurate results
            condition_on_previous_text=False,  # Prevent hallucination from context
            vad_filter=True,  # Voice activity detection to filter silence
            vad_parameters=dict(
                min_silence_duration_ms=500,  # Minimum silence to split segments
                threshold=0.5  # VAD threshold (0.0-1.0, higher = more aggressive)
            )
        )
        
        # Combine all segments into one text
        transcription = " ".join([segment.text for segment in segments]).strip()
        
        print(f"[STT] Transcription: {transcription[:100]}...")
        return transcription
        
    except Exception as e:
        print(f"[ERROR] Transcription error: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        # Clean up preprocessed file if it was created
        if preprocessed_path and preprocessed_path != audio_file_path:
            try:
                if os.path.exists(preprocessed_path):
                    os.remove(preprocessed_path)
                    print(f"[Cleanup] Deleted preprocessed temp file")
            except Exception as e:
                print(f"[WARNING] Failed to cleanup preprocessed file: {e}")

def strip_markdown_for_tts(text: str) -> str:
    """
    Strip markdown formatting from text for TTS.
    Converts markdown to plain text that sounds natural when spoken.
    
    Args:
        text: Text with markdown formatting
    
    Returns:
        Plain text without markdown symbols
    """
    import re
    
    if not text:
        return ''
    
    # Remove horizontal rules
    text = re.sub(r'^---+$', '', text, flags=re.MULTILINE)
    
    # Remove markdown headers (# ## ###)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    
    # Remove bold/italic markers
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    
    # Remove code blocks
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    # Remove links [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # Remove images ![alt](url) -> alt
    text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', r'\1', text)
    
    # Clean up list markers (convert to natural speech)
    text = re.sub(r'^[\s]*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)
    
    # Remove extra whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = text.strip()
    
    # Convert common markdown patterns to natural speech
    text = re.sub(r'\*\*([^*:]+):\*\*', r'\1:', text)
    
    # Add pauses for better speech flow
    text = re.sub(r'\n\n', '. ', text)
    text = re.sub(r'\n', '. ', text)
    text = re.sub(r'\.\s*\.', '.', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text

def synthesize_speech(text: str, output_format: str = "wav") -> Optional[bytes]:
    """
    Convert text to speech using pyttsx3.
    Thread-safe with locking to prevent conflicts.
    Automatically strips markdown formatting for natural speech.
    
    Args:
        text: Text to convert to speech (may contain markdown)
        output_format: Audio format (wav)
    
    Returns:
        Audio bytes or None if failed
    """
    if not tts_engine:
        print("[ERROR] TTS engine not initialized")
        return None
    
    # Strip markdown formatting before TTS
    plain_text = strip_markdown_for_tts(text)
    
    if not plain_text or len(plain_text.strip()) == 0:
        print("[WARNING] No text to speak after markdown stripping")
        return None
    
    # Use lock for thread safety (pyttsx3 is not thread-safe)
    with tts_lock:
        try:
            print(f"[TTS] Synthesizing speech: {plain_text[:100]}...")
            
            # Create temporary file for audio output
            temp_fd, temp_audio_path = tempfile.mkstemp(suffix='.wav')
            os.close(temp_fd)
            
            try:
                # Reset engine before each synthesis
                try:
                    tts_engine.stop()
                except:
                    pass  # May fail if nothing playing
                
                # Generate speech to file (using plain text, not markdown)
                tts_engine.save_to_file(plain_text, temp_audio_path)
                tts_engine.runAndWait()
                
                # Verify file was created
                if not os.path.exists(temp_audio_path):
                    print(f"[ERROR] Audio file not created: {temp_audio_path}")
                    return None
                
                file_size = os.path.getsize(temp_audio_path)
                print(f"[TTS] Audio file created: {file_size} bytes")
                
                if file_size == 0:
                    print(f"[ERROR] Audio file is empty")
                    return None
                
                # Read audio file
                with open(temp_audio_path, 'rb') as f:
                    audio_data = f.read()
                
                print(f"[TTS] Successfully generated {len(audio_data)} bytes of audio")
                return audio_data
                
            except Exception as inner_e:
                print(f"[ERROR] TTS generation failed: {inner_e}")
                import traceback
                traceback.print_exc()
                return None
                
            finally:
                # Clean up temp file
                if os.path.exists(temp_audio_path):
                    try:
                        os.remove(temp_audio_path)
                        print(f"[TTS] Cleaned up temp file")
                    except:
                        pass
            
        except Exception as e:
            print(f"[ERROR] Speech synthesis error: {e}")
            import traceback
            traceback.print_exc()
            return None

def save_audio_to_temp(audio_bytes: bytes, format: str = "wav") -> Optional[str]:
    """
    Save audio bytes to a temporary file.
    
    Args:
        audio_bytes: Audio data
        format: Audio format extension
    
    Returns:
        Path to temporary file or None if failed
    """
    try:
        # Create temporary file
        temp_fd, temp_path = tempfile.mkstemp(suffix=f".{format}")
        os.close(temp_fd)
        
        # Write audio data
        with open(temp_path, 'wb') as f:
            f.write(audio_bytes)
        
        return temp_path
        
    except Exception as e:
        print(f"[ERROR] Error saving audio to temp file: {e}")
        return None

def cleanup_temp_file(file_path: str) -> bool:
    """
    Delete temporary audio file (HIPAA compliance).
    
    Args:
        file_path: Path to file to delete
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"[Cleanup] Deleted temp file: {file_path}")
            return True
        return False
    except Exception as e:
        print(f"[ERROR] Error deleting temp file: {e}")
        return False

def is_voice_available() -> Tuple[bool, bool]:
    """
    Check if voice features are available.
    
    Returns:
        Tuple of (stt_available, tts_available)
    """
    return (whisper_model is not None, tts_engine is not None)

def get_voice_status() -> dict:
    """
    Get status of voice processing system.
    
    Returns:
        Dictionary with status information
    """
    stt_available, tts_available = is_voice_available()
    
    return {
        'initialized': voice_initialized,
        'stt_available': stt_available,
        'tts_available': tts_available,
        'whisper_model': os.getenv('WHISPER_MODEL', 'tiny.en') if stt_available else None,
        'tts_engine': 'pyttsx3 (system voices)' if tts_available else None
    }

# Auto-initialize on import if voice is enabled
if os.getenv('VOICE_ENABLED', 'false').lower() == 'true':
    print("Voice processing enabled, initializing...")
    initialize_voice_system()
else:
    print("Voice processing disabled (set VOICE_ENABLED=true to enable)")

