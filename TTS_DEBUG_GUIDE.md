# TTS Debugging Guide

**Issue:** TTS shows "Bot speaking..." but no audio plays

---

## Quick Debug Steps

### 1. Restart the App

Stop current app (Ctrl+C) and restart:
```bash
python app.py
```

Look for:
```
[OK] pyttsx3 TTS engine loaded successfully
✅ Voice processing enabled! (STT + TTS)
```

### 2. Open Browser Console

- Press F12 → Console tab
- Clear console
- Enable voice mode
- Send a message

### 3. Check Console Logs

**Look for these messages:**

```javascript
[Voice] Calling TTS endpoint with text: Hello!...
[Voice] TTS response status: 200
[Voice] Audio blob received: 90420 bytes, type: audio/wav
[Voice] Audio URL created: blob:http://...
[Voice] Audio loaded, duration: 3.5 seconds
[Voice] Audio can play
[Voice] Audio playback started
[Voice] Audio playback finished
```

**Common Issues:**

### Issue 1: "Audio play() promise rejected"

**Cause:** Browser autoplay blocking  
**Solution:** User must interact with page first (click/type something)

**Fix:** Add user interaction requirement:
- First time: Type a message to enable autoplay
- Or add a "Click to enable audio" notice

### Issue 2: "TTS response status: 500"

**Cause:** Backend TTS error  
**Check backend logs** for:
```
[ERROR] Speech synthesis error: ...
```

**Fix:** Verify pyttsx3 initialized properly

### Issue 3: "Audio blob received: 0 bytes"

**Cause:** TTS generation failed  
**Fix:** Check backend logs, verify temp file creation

### Issue 4: "Audio error details: MEDIA_ERR_SRC_NOT_SUPPORTED"

**Cause:** Audio format not supported by browser  
**Fix:** Check if WAV format works in your browser:
```javascript
const audio = new Audio();
console.log('Supports WAV:', audio.canPlayType('audio/wav'));
```

---

## Backend Debugging

Check terminal output when TTS is called:

**Expected:**
```
[TTS] Synthesizing speech: Hello! What brings you in today?...
[TTS] Generated 90420 bytes of audio
[TTS] Cleaned up temp file
[Voice] TTS for session ...: 36 chars -> 90420 bytes
```

**If you see:**
```
[ERROR] TTS engine not initialized
```
→ pyttsx3 failed to load. Check:
```powershell
python -c "import pyttsx3; engine = pyttsx3.init(); print('TTS OK')"
```

---

## Manual Test

Test TTS directly in browser console:

```javascript
// Test if audio playback works
const testAudio = new Audio();
testAudio.src = 'data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=';
testAudio.play().then(() => console.log('Audio works!')).catch(e => console.error('Audio blocked:', e));
```

**If blocked:** Browser autoplay is blocking audio  
**Fix:** Require user interaction first

---

## Browser Autoplay Policy

Modern browsers block autoplay unless:
1. User has interacted with page (click, tap, key press)
2. Site is on user's autoplay whitelist
3. Audio is muted (we don't want this)

**Solution:** Ensure user has clicked/typed before TTS plays

**Add to frontend:**
```javascript
let userHasInteracted = false;

// Track first interaction
document.body.addEventListener('click', () => {
  userHasInteracted = true;
}, { once: true });

// In speakText function:
if (!userHasInteracted) {
  console.log('[Voice] Waiting for user interaction before playing audio');
  return;
}
```

---

## Quick Fixes

### Fix 1: Autoplay Issue

Add click-to-enable audio:
```javascript
// Before playing audio
if (!userHasInteracted) {
  alert('Click OK to enable bot voice');
  userHasInteracted = true;
}
currentAudio.play();
```

### Fix 2: Backend Issue

Test backend directly:
```bash
curl -X POST http://127.0.0.1:8002/voice/synthesize \
  -H "Content-Type: application/json" \
  -d "{\"text\":\"Hello test\",\"session_id\":\"test\"}" \
  --output test_audio.wav
```

Play `test_audio.wav` to verify audio generation works.

---

## Expected Console Output

**Working TTS:**
```
[Voice] Calling TTS endpoint with text: Hello! What brings...
[Voice] TTS response status: 200
[Voice] Audio blob received: 90420 bytes, type: audio/wav
[Voice] Audio URL created: blob:http://127.0.0.1:8000/abc123
[Voice] Audio loaded, duration: 3.2 seconds
[Voice] Audio can play
[Voice] Audio playback started
[Voice] Audio playback promise resolved
... (3 seconds later) ...
[Voice] Audio playback finished
```

**Blocked Autoplay:**
```
[Voice] Calling TTS endpoint with text: Hello! What brings...
[Voice] TTS response status: 200
[Voice] Audio blob received: 90420 bytes, type: audio/wav
[Voice] Audio play() promise rejected: NotAllowedError: play() failed because the user didn't interact with the document first
```
→ Need user interaction

---

## Test in Browser Console

When "Bot speaking..." appears, run in console:

```javascript
// Check audio object
console.log('Current audio:', currentAudio);
console.log('Is speaking:', isSpeaking);
console.log('Voice enabled:', voiceEnabled);

// Try to play manually
if (currentAudio) {
  currentAudio.play().then(() => console.log('Manual play worked!')).catch(e => console.error('Manual play failed:', e));
}
```

---

## Solutions Summary

| Issue | Cause | Fix |
|-------|-------|-----|
| Audio doesn't play | Autoplay blocked | Require user click first |
| "TTS failed: 500" | Backend error | Check pyttsx3 init |
| 0 bytes audio | TTS generation failed | Check backend logs |
| Format not supported | Browser compatibility | All modern browsers support WAV |
| isSpeaking stays true | Error in playback | Added better error handling |

---

## Next Steps

1. **Open browser console** (F12)
2. **Enable voice mode**
3. **Send a message**
4. **Check console logs** - Look for the messages above
5. **Share the console output** if issue persists

The detailed logging will show exactly where TTS is failing!


