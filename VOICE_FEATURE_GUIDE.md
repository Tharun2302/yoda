# Voice Feature Guide

**Date:** November 20, 2024  
**Status:** ✅ **Implemented**

---

## Overview

HealthYoda now supports voice input and output using **faster-whisper** (STT) and **Piper TTS** (speech synthesis). All processing is done locally on your server for HIPAA compliance.

---

## How It Works

### Architecture

```
User speaks → Browser records → Backend transcribes → Text to chat
Bot responds → Text generates → Backend synthesizes → Browser plays audio
```

### Key Features

1. **Voice Toggle**: Enable/disable voice mode from header
2. **Push-to-Talk**: Hold mic button to record, release to transcribe
3. **Auto-Mic Enable**: Mic activates automatically after bot finishes speaking
4. **Text Review**: Transcribed text appears in input box for user to review/edit before sending
5. **Text Chat Still Works**: Can type anytime, voice is optional overlay

---

## User Flow

### With Voice Mode Enabled:

1. **User clicks "Voice Off" button** in header
   - Button turns green: "Voice On"
   - Mic button becomes active
   - Permission prompt appears (first time)

2. **Bot asks question** (streaming as normal)
   - Text appears in chat
   - TTS converts to speech
   - Audio plays automatically
   - Status: "🔊 Bot speaking..."

3. **Bot finishes speaking**
   - Status: "🎤 Your turn"
   - Mic button pulses (ready)

4. **User holds mic button**
   - Recording starts
   - Status: "🔴 Recording..."
   - Mic button turns red with pulse animation

5. **User releases mic button**
   - Recording stops
   - Status: "⏳ Transcribing..." (2-5 seconds)
   - Audio sent to backend

6. **Transcription complete**
   - Transcribed text appears in input box
   - User can review/edit
   - User presses Enter or Send button

7. **Cycle repeats**

---

## Backend Components

### 1. `voice_processor.py`

**Whisper Initialization:**
- Model: `tiny.en` (fast) or `base.en` (better quality)
- CPU mode with int8 quantization
- ~400MB RAM usage
- 1-5 second transcription time

**Piper TTS Initialization:**
- Voice: `en_US-lessac-medium` (clear, professional)
- ~100MB RAM usage
- Near-instant synthesis (<1 second)

**Functions:**
- `initialize_voice_system()` - Load models
- `transcribe_audio(file_path)` - STT
- `synthesize_speech(text)` - TTS
- `cleanup_temp_file(path)` - HIPAA compliance

### 2. `app.py` - New Endpoints

**POST `/voice/transcribe`**
- Accepts: Audio file (WebM/WAV)
- Returns: `{"text": "transcribed text", "session_id": "...", "timestamp": "..."}`
- Rate limited (same as chat endpoints)
- Audio deleted immediately after processing

**POST `/voice/synthesize`**
- Accepts: `{"text": "message to speak", "session_id": "..."}`
- Returns: WAV audio file
- Rate limited
- No audio storage

**GET `/voice/status`**
- Returns: Voice system availability status
- Used by frontend to enable/disable voice toggle

---

## Frontend Components

### UI Elements Added:

1. **Voice Toggle Button** (header)
   - Icon: Microphone
   - Text: "Voice Off" / "Voice On"
   - Color: Gray (off) / Green (on)

2. **Mic Button** (input area)
   - Push-to-talk control
   - Disabled when voice off
   - Red + pulsing when recording

3. **Voice Status Indicator** (above input)
   - "🔴 Recording..."
   - "⏳ Transcribing..."
   - "🔊 Bot speaking..."
   - "🎤 Your turn"

### JavaScript Functions Added:

- `checkVoiceAvailability()` - Check if backend supports voice
- `toggleVoiceMode()` - Enable/disable voice
- `startRecording()` - Start audio recording
- `stopRecording()` - Stop and transcribe
- `transcribeAudio(blob)` - Send audio to backend
- `speakText(text)` - TTS for bot responses
- `stopSpeaking()` - Stop audio playback

---

## Configuration

### Environment Variables

Add to `.env`:

```bash
# Voice Processing
VOICE_ENABLED=true
WHISPER_MODEL=tiny.en
PIPER_VOICE=en_US-lessac-medium
MAX_AUDIO_DURATION=60
MAX_AUDIO_SIZE=10485760
```

### Model Options

**Whisper Models (STT):**
- `tiny.en`: Fastest (~1-2s), good quality
- `base.en`: Balanced (~3-5s), better quality
- `small.en`: Slow (~5-10s), best quality

**Piper Voices (TTS):**
- `en_US-lessac-medium`: Clear, professional (recommended)
- `en_US-amy-medium`: Warmer, conversational
- `en_GB-alba-medium`: British accent

---

## HIPAA Compliance

### Measures Implemented:

1. **Local Processing**
   - All audio processed on YOUR server
   - No third-party services
   - No external API calls for voice

2. **No Audio Storage**
   - Temp files deleted immediately after processing
   - Audio files in `.gitignore`
   - No audio logging

3. **Secure Transmission**
   - Audio transmitted over HTTPS only
   - Existing security headers apply
   - Rate limiting prevents abuse

4. **Audit Logging**
   - Logs: session_id, timestamp, action type
   - NO audio content logged
   - NO PHI in logs

5. **Access Control**
   - Same rate limiting as chat
   - Session validation
   - Input sanitization

### Compliance Checklist:

- [x] Audio processed locally (not sent to third parties)
- [x] Temp files deleted after processing
- [x] No audio storage/archiving
- [x] Audit logging (metadata only)
- [x] HTTPS transmission
- [x] Rate limiting
- [x] Input validation
- [x] Audio files in .gitignore

---

## Testing

### Test Voice Status:

1. Start app: `python app.py`
2. Look for:
   ```
   ✅ Voice processing enabled! (STT + TTS)
   ```

3. Check endpoint: `GET http://127.0.0.1:8002/voice/status`
   ```json
   {
     "initialized": true,
     "stt_available": true,
     "tts_available": true,
     "whisper_model": "tiny.en",
     "piper_voice": "en_US-lessac-medium"
   }
   ```

### Test Voice Flow:

1. Open http://127.0.0.1:8000
2. Click "Voice Off" → Should turn green "Voice On"
3. Browser asks for mic permission → Allow
4. Type and send a question (text)
5. Bot responds → Should hear voice reading response
6. After bot finishes → Mic should be ready
7. Hold mic button → Should see "🔴 Recording..."
8. Release mic button → Should see "⏳ Transcribing..."
9. Wait 2-5 seconds → Transcribed text appears in input
10. Review text → Press Enter → Bot responds

### Test Error Handling:

1. **No mic permission**: Should fall back to text input
2. **Voice disabled in .env**: Button should be disabled
3. **Backend offline**: Should show error gracefully
4. **Long audio**: Should auto-stop at 60 seconds
5. **Network error**: Should show error message, allow retry

### Test HIPAA Compliance:

1. Record audio → Check temp files deleted:
   ```powershell
   Get-ChildItem -Path . -Filter *.webm
   # Should be empty
   ```

2. Check logs → Should NOT contain audio content
3. Check MongoDB → Should NOT contain audio data
4. Verify rate limiting works for voice endpoints

---

## Performance

### Expected (Laptop CPU):

- **TTS**: 0.5-1 second (near instant)
- **STT**: 2-5 seconds (tiny model) or 3-7 seconds (base model)
- **Model Loading**: 5-10 seconds at startup (one-time)
- **Memory**: +500MB RAM (Whisper ~400MB, Piper ~100MB)

### Tips for Better Performance:

1. **Use tiny.en model** for fastest transcription
2. **Keep responses short** for faster TTS
3. **Close other applications** to free RAM
4. **Upgrade to base.en** only if accuracy issues

---

## Troubleshooting

### "Voice processing not available"

**Check:**
1. Dependencies installed: `pip list | findstr faster-whisper`
2. `VOICE_ENABLED=true` in `.env`
3. Models downloaded (happens on first use)

**Fix:**
```bash
pip install faster-whisper piper-tts pydub
```

### "Microphone permission denied"

**Browser:**
- Chrome: Settings → Privacy → Site Settings → Microphone
- Firefox: Permissions → Microphone → Allow
- Edge: Settings → Cookies and site permissions → Microphone

**Fix:** Allow microphone access for localhost

### "Transcription failed"

**Causes:**
- Audio format not supported
- Audio too long (>60s)
- Backend processing error

**Fix:**
- Check backend logs
- Try shorter recording
- Verify Whisper model loaded

### "Bot not speaking"

**Check:**
1. Voice mode enabled (green button)
2. Backend TTS available: `/voice/status`
3. Browser audio not muted
4. Check console for errors

**Fix:**
- Check if Piper voice loaded in logs
- Verify browser audio playback works
- Check network tab for /voice/synthesize errors

### "Slow transcription"

**Current:** 2-5 seconds is normal for CPU

**Options:**
1. Accept delay (free)
2. Switch to OpenAI Whisper API (faster, costs money)
3. Get GPU-enabled server (much faster)
4. Use base model instead of tiny (better accuracy, slightly slower)

---

## Keyboard Shortcuts

- **Enter**: Send message (text mode)
- **Hold Mic Button**: Record (voice mode)
- **Release Mic Button**: Stop and transcribe

---

## Browser Compatibility

### Tested:
- ✅ Chrome/Edge (recommended)
- ✅ Firefox
- ⚠️ Safari (may have audio format issues)

### Requirements:
- MediaRecorder API support
- getUserMedia API support
- Audio playback support

---

## Future Enhancements

### Planned:

1. **Voice Activity Detection**
   - Auto-stop recording after silence
   - No need to release button

2. **Continuous Conversation Mode**
   - Bot speaks → Auto-start recording
   - Hands-free conversation

3. **Noise Cancellation**
   - Filter background noise
   - Improve transcription accuracy

4. **Custom Wake Word**
   - "Hey HealthYoda" to activate
   - Voice-only interface

5. **Multiple Voices**
   - Choose TTS voice (male/female)
   - Adjust speed/pitch

6. **Real-time Transcription**
   - Show text as user speaks
   - Live feedback

---

## Cost Analysis

### Current (Free):

- **faster-whisper**: Free, open source
- **Piper TTS**: Free, open source
- **Cost**: Only server resources (CPU, RAM)
- **Per session**: $0.00

### Alternative (OpenAI):

- **Whisper API**: $0.006/minute
- **TTS API**: $15/1M characters (~$0.015/minute)
- **Per 10-minute session**: ~$0.21

**Savings**: 100% free with current solution

---

## Summary

✅ **Voice input** - Push-to-talk recording with transcription  
✅ **Voice output** - Auto-play bot responses  
✅ **Text fallback** - Can still type anytime  
✅ **HIPAA compliant** - All processing local, no storage  
✅ **Free** - No API costs  
✅ **CPU-optimized** - Works on laptops  
✅ **User-friendly** - Simple toggle, visual feedback  
✅ **Error handling** - Graceful degradation  

---

## Quick Start

1. Add to `.env`:
   ```bash
   VOICE_ENABLED=true
   ```

2. Start app:
   ```bash
   python app.py
   ```

3. Look for:
   ```
   ✅ Voice processing enabled! (STT + TTS)
   ```

4. Open http://127.0.0.1:8000

5. Click "Voice Off" → "Voice On"

6. Allow microphone permission

7. Chat normally (text), bot will speak responses

8. Hold mic button to speak your response

9. Review transcribed text, press Enter

Done! 🎉

---

**Files Modified:**
- `requirements.txt` - Added voice dependencies
- `voice_processor.py` - Voice processing logic
- `app.py` - Voice endpoints
- `index.html` - Voice UI and controls
- `.gitignore` - Audio file exclusions

**Voice is now fully integrated and HIPAA compliant!**

