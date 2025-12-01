# Voice Feature Testing Guide

**Status:** Ready for testing

---

## Setup Before Testing

### 1. Enable Voice in .env

Add these lines to your `.env` file:

```bash
# Voice Processing Configuration
VOICE_ENABLED=true
WHISPER_MODEL=tiny.en
PIPER_VOICE=en_US-lessac-medium
MAX_AUDIO_DURATION=60
MAX_AUDIO_SIZE=10485760
```

### 2. Start the Application

```bash
python app.py
```

### 3. Check Startup Messages

Look for these messages:

```
✅ OpenAI API key found!
✅ Langfuse configured! Traces will be logged.
✅ MongoDB connected! Session data will be persisted.
✅ Voice processing enabled! (STT + TTS)
```

**If you see:**
```
⚠️  Voice processing available but not initialized
   Set VOICE_ENABLED=true in .env to enable
```
→ Voice is disabled, add `VOICE_ENABLED=true` to `.env`

**If you see:**
```
Loading Whisper model 'tiny.en'...
Loading Piper voice 'en_US-lessac-medium'...
```
→ First time setup - models are downloading (1-2 minutes)

---

## Test Checklist

### Basic Functionality

- [ ] **Voice Toggle Button Appears** in header next to "New Chat"
- [ ] **Mic Button Appears** in input area (left of send button)
- [ ] **Click "Voice Off"** → Turns green "Voice On"
- [ ] **Browser Asks for Mic Permission** → Allow
- [ ] **Mic Button Activates** (no longer grayed out)

### Voice Output (TTS)

- [ ] Type "hello" and send
- [ ] Bot responds with text
- [ ] **Bot voice should read response automatically**
- [ ] Status shows "🔊 Bot speaking..."
- [ ] After audio ends, mic button pulses (ready)

### Voice Input (STT)

- [ ] **Hold mic button** → Status shows "🔴 Recording..."
- [ ] **Mic button turns red** with pulse animation
- [ ] **Speak clearly**: "My head hurts"
- [ ] **Release mic button**
- [ ] Status shows "⏳ Transcribing..." (wait 2-5 seconds)
- [ ] **Transcribed text appears in input box**
- [ ] **Text should match what you said**
- [ ] User can edit text before sending
- [ ] Press Enter to send

### Error Handling

- [ ] **Deny mic permission** → Should fall back to text input with alert
- [ ] **Click voice toggle off** while recording → Should stop recording
- [ ] **Hold mic for 60+ seconds** → Should auto-stop
- [ ] **Refresh page** → Voice toggle should be off by default
- [ ] **No network** → Should show error gracefully

### HIPAA Compliance

- [ ] **Check temp files**: Run `Get-ChildItem *.webm` → Should be empty
- [ ] **Check logs**: No audio content in terminal output
- [ ] **Check MongoDB**: No audio data stored (only text)
- [ ] **Rate limiting**: Rapidly click mic → Should be rate-limited after 100 requests

### Performance

- [ ] **TTS latency**: < 1 second delay
- [ ] **STT latency**: 2-5 seconds (acceptable for CPU)
- [ ] **Memory usage**: Check Task Manager → Python ~500-800MB
- [ ] **No crashes**: Use for 5+ minutes continuously

---

## Testing Scenarios

### Scenario 1: Full Voice Conversation

1. Enable voice mode
2. Type: "hello"
3. Bot speaks response
4. Hold mic → Say "I have shoulder pain"
5. Release → Wait for transcription
6. Review text → Send
7. Bot speaks next question
8. Hold mic → Answer with voice
9. Continue for 5-10 exchanges
10. Verify no duplicate questions (MongoDB working)

**Expected:** Smooth voice conversation, no errors, all data stored

### Scenario 2: Mixed Voice and Text

1. Enable voice mode
2. Type message → Bot speaks
3. Hold mic → Speak response
4. Type next message → Bot speaks
5. Continue mixing voice and text

**Expected:** Both input methods work seamlessly

### Scenario 3: Voice Mode Toggle

1. Start with voice off (text chat)
2. Mid-conversation, enable voice
3. Bot speaks next response
4. Disable voice mid-response
5. Continue with text

**Expected:** Graceful transition, no crashes

### Scenario 4: Network Interruption

1. Enable voice, start recording
2. While transcribing, disconnect network briefly
3. Reconnect

**Expected:** Error message, allow retry

### Scenario 5: Long Recording

1. Hold mic for 55 seconds
2. Say a long medical history

**Expected:** Auto-stop at 60s, transcribe full audio

---

## Common Issues & Solutions

### Issue: "Voice processing not available"

**Solution:**
```bash
# Check dependencies
pip list | findstr faster-whisper
pip list | findstr piper-tts

# Reinstall if missing
pip install faster-whisper piper-tts pydub
```

### Issue: Transcription takes >10 seconds

**Solution:**
- Normal for CPU with base/small models
- Switch to `WHISPER_MODEL=tiny.en` for faster
- Or accept delay (still functional)

### Issue: Voice quality poor

**Solution:**
- Switch to `WHISPER_MODEL=base.en` (better accuracy)
- Speak clearly and slowly
- Reduce background noise
- Check microphone settings

### Issue: TTS doesn't play

**Solution:**
- Check browser console for errors
- Verify audio isn't muted
- Check if Piper voice loaded in logs
- Try different browser (Chrome recommended)

### Issue: Mic permission keeps asking

**Solution:**
- Browser settings → Allow microphone for localhost
- Chrome: chrome://settings/content/microphone
- Add localhost:8000 to allowed sites

---

## Manual Testing Commands

### Test Voice Status Endpoint:

```powershell
# PowerShell
Invoke-WebRequest -Uri http://127.0.0.1:8002/voice/status | Select-Object -ExpandProperty Content
```

**Expected:**
```json
{
  "initialized": true,
  "stt_available": true,
  "tts_available": true,
  "whisper_model": "tiny.en",
  "piper_voice": "en_US-lessac-medium"
}
```

### Test Health Endpoint:

```powershell
Invoke-WebRequest -Uri http://127.0.0.1:8002/health | Select-Object -ExpandProperty Content
```

**Expected:**
```json
{"status": "healthy"}
```

---

## Performance Benchmarks

Test on your laptop and note:

**Model Loading Time:**
- First startup: ____ seconds (one-time)
- Subsequent startups: Same (models cached)

**STT Performance:**
- 5-second audio → ____ seconds to transcribe
- 10-second audio → ____ seconds to transcribe
- 30-second audio → ____ seconds to transcribe

**TTS Performance:**
- Short response (50 chars) → ____ seconds
- Medium response (200 chars) → ____ seconds
- Long response (500 chars) → ____ seconds

**Expected (CPU):**
- Model loading: 5-10 seconds
- STT: 2-5 seconds for 10s audio
- TTS: <1 second for typical response

---

## Debug Mode

If issues occur, enable debug output:

### Backend Debug:

In `app.py`, temporarily change:
```python
app.run(host='127.0.0.1', port=8002, debug=True)  # Enable debug
```

### Frontend Debug:

Open browser console (F12) and watch for:
```
[Voice] Voice mode enabled
[Voice] Recording started
[Voice] Recording stopped
[Voice] Transcribed: <text>
[Voice] Playing TTS audio
```

---

## Acceptance Criteria

Voice feature is ready for production when:

✅ Voice toggle works  
✅ Recording works (push-to-talk)  
✅ Transcription works (2-5s delay acceptable)  
✅ TTS works (bot speaks responses)  
✅ Auto-mic-enable after bot speaks  
✅ Text input still works  
✅ No audio files stored  
✅ No crashes or freezes  
✅ HIPAA compliant (audit confirms)  

---

## Next Steps After Testing

If all tests pass:
1. Document any performance issues
2. Adjust Whisper model size if needed (`tiny.en` vs `base.en`)
3. Consider GPU upgrade for faster transcription (optional)
4. Train users on voice interface
5. Monitor usage and performance

If issues found:
1. Check logs for errors
2. Verify all dependencies installed
3. Test on different browsers
4. Review this guide for solutions
5. Contact support if needed

---

## Summary

Voice feature implemented with:
- ✅ Local STT (faster-whisper)
- ✅ Local TTS (Piper)
- ✅ HIPAA compliant
- ✅ Free (no API costs)
- ✅ CPU-optimized
- ✅ User-friendly UI
- ✅ Error handling
- ✅ Fallback to text

**Ready for user testing!**

Start app with `VOICE_ENABLED=true` in `.env` and follow test checklist above.

