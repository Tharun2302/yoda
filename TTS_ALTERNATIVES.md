# TTS Alternatives for Voice Output

**Issue:** Piper TTS requires additional setup/configuration that wasn't compatible with the simple import approach.

**Current Status:**
- ✅ **STT (Speech-to-Text) works** - faster-whisper is working perfectly
- ⚠️ **TTS (Text-to-Speech) needs alternative** - Piper setup complex

---

## Quick Solutions

### Option 1: Browser Web Speech API (Easiest, Free)

**Frontend-only TTS using browser's built-in speech synthesis**

**Pros:**
- ✅ Free
- ✅ No backend changes needed
- ✅ Works immediately
- ✅ Good voice quality

**Cons:**
- ⚠️ Not fully HIPAA compliant (audio processed by browser/OS)
- Different voices on different browsers/OS
- Requires internet for some browsers

**Implementation:**

Add to `index.html` in the `speakText` function:

```javascript
async function speakText(text) {
  if (!voiceEnabled || isSpeaking) return;
  
  try {
    isSpeaking = true;
    micBtn.classList.add('disabled');
    voiceStatus.textContent = '🔊 Bot speaking...';
    voiceStatus.classList.add('show', 'speaking');
    
    // Use browser's Speech Synthesis API
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;
    
    // Get a good voice (prefer female, clear voice)
    const voices = speechSynthesis.getVoices();
    const preferredVoice = voices.find(v => v.lang.startsWith('en') && v.name.includes('Female')) 
                        || voices.find(v => v.lang.startsWith('en'));
    if (preferredVoice) {
      utterance.voice = preferredVoice;
    }
    
    utterance.onend = () => {
      stopSpeaking();
      if (voiceEnabled) {
        micBtn.classList.remove('disabled');
        voiceStatus.textContent = '🎤 Your turn';
        voiceStatus.classList.add('show');
        setTimeout(() => voiceStatus.classList.remove('show'), 2000);
      }
    };
    
    utterance.onerror = (error) => {
      console.error('[Voice] Speech synthesis error:', error);
      stopSpeaking();
    };
    
    speechSynthesis.speak(utterance);
    console.log('[Voice] Speaking with browser TTS');
    
  } catch (error) {
    console.error('[Voice] TTS error:', error);
    stopSpeaking();
  }
}
```

**Time to implement:** 5 minutes  
**Cost:** $0  
**HIPAA:** Partial (audio processed locally but by browser/OS)

---

### Option 2: OpenAI TTS API (Best Quality, HIPAA Compliant)

**Use OpenAI's TTS API - same provider as your chat**

**Pros:**
- ✅ HIPAA compliant with BAA
- ✅ Excellent voice quality
- ✅ Fast (<1 second)
- ✅ Easy integration
- ✅ Same provider as chat (already have API key)

**Cons:**
- 💰 Costs money (~$15/1M characters = ~$0.015/response)
- Requires OpenAI API key (you already have)

**Implementation:**

Update `voice_processor.py`:

```python
def synthesize_speech_openai(text: str, client) -> Optional[bytes]:
    """Use OpenAI TTS API"""
    try:
        from openai import OpenAI
        
        response = client.audio.speech.create(
            model="tts-1",  # or "tts-1-hd" for higher quality
            voice="nova",  # alloy, echo, fable, onyx, nova, shimmer
            input=text
        )
        
        return response.content
    except Exception as e:
        print(f"OpenAI TTS error: {e}")
        return None
```

**Cost for 100 sessions:** ~$1.50  
**Time to implement:** 10 minutes  
**HIPAA:** ✅ Full compliance with BAA

---

### Option 3: gTTS (Google Text-to-Speech, Simple)

**Use Google's TTS library (free, simple)**

**Pros:**
- ✅ Free
- ✅ Simple to use
- ✅ Good quality
- ✅ Works immediately

**Cons:**
- ⚠️ Not HIPAA compliant (uses Google servers)
- Requires internet
- Slower than local

**Implementation:**

```bash
pip install gtts
```

```python
from gtts import gTTS

def synthesize_speech_gtts(text: str) -> Optional[bytes]:
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        return audio_bytes.getvalue()
    except Exception as e:
        print(f"gTTS error: {e}")
        return None
```

**Cost:** $0  
**Time:** 5 minutes  
**HIPAA:** ❌ No (uses Google servers)

---

### Option 4: pyttsx3 (Offline, Local)

**Local TTS using system voices**

**Pros:**
- ✅ Free
- ✅ Fully offline
- ✅ HIPAA compliant
- ✅ No model downloads

**Cons:**
- Voice quality lower (robotic)
- Different voices on different OS
- May sound less natural

**Implementation:**

```bash
pip install pyttsx3
```

```python
import pyttsx3

def initialize_pyttsx3():
    global tts_engine
    try:
        tts_engine = pyttsx3.init()
        tts_engine.setProperty('rate', 150)  # Speed
        tts_engine.setProperty('volume', 1.0)
        return True
    except:
        return False

def synthesize_speech_pyttsx3(text: str) -> Optional[bytes]:
    try:
        temp_file = tempfile.mktemp(suffix='.wav')
        tts_engine.save_to_file(text, temp_file)
        tts_engine.runAndWait()
        
        with open(temp_file, 'rb') as f:
            audio_data = f.read()
        
        os.remove(temp_file)
        return audio_data
    except Exception as e:
        print(f"pyttsx3 error: {e}")
        return None
```

**Cost:** $0  
**Time:** 10 minutes  
**HIPAA:** ✅ Full compliance

---

## My Recommendation

### For Development/Testing: **Option 1 (Browser API)**
- Free, works immediately
- Good enough for testing
- Just frontend changes

### For Production: **Option 2 (OpenAI TTS)**
- HIPAA compliant with BAA
- Best quality
- Same provider as chat
- Worth the small cost (~$1.50 per 100 sessions)

### For Budget/Offline: **Option 4 (pyttsx3)**
- Free, HIPAA compliant
- Lower quality but functional
- Fully local

---

## Current Status

**Working:**
✅ STT (Speech-to-Text) - faster-whisper working perfectly  
✅ Voice recording UI  
✅ Push-to-talk functionality  
✅ Transcription (2-5 second delay)  
✅ Text review before sending  

**Not Working:**
❌ TTS (Text-to-Speech) - Piper failed to initialize  

**Quick Fix Options:**
1. Use browser TTS (5 minutes, free, works now)
2. Use OpenAI TTS (10 minutes, small cost, best quality)
3. Use pyttsx3 (10 minutes, free, lower quality)

---

## Which Option Do You Want?

**Quick decision:**
- Want to test NOW → Option 1 (Browser API)
- Want best quality → Option 2 (OpenAI TTS)
- Want free + HIPAA → Option 4 (pyttsx3)

Let me know which option and I'll implement it immediately!

