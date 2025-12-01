# TTS Not Playing - Fixes Applied

**Changes Made:**

1. **Added CORS preflight support** - OPTIONS method for `/voice/synthesize`
2. **Added thread-safety** - Lock around pyttsx3 calls (not thread-safe)
3. **Added debug logging** - More detailed TTS logs
4. **Added error handling** - Better error messages

---

## What to Check Now

### 1. Restart App

The app is restarting in the background. Wait ~10 seconds, then:

### 2. Refresh Browser

- Hard refresh: Ctrl+Shift+R
- Or clear cache and refresh

### 3. Check Backend Logs

When you enable voice and bot responds, look for:

**Terminal output:**
```
[Voice] TTS endpoint called
[TTS] Synthesizing speech: Can you tell me when...
[TTS] Audio file created: 90420 bytes
[TTS] Successfully generated 90420 bytes of audio
[TTS] Cleaned up temp file
[Voice] TTS for session ...: 40 chars -> 90420 bytes
```

**If you DON'T see "[Voice] TTS endpoint called":**
→ Request not reaching backend (CORS/network issue)

**If you see "[ERROR]":**
→ TTS generation failing (check error details)

### 4. Check Browser Console

After bot responds, check console for:

```javascript
[Voice] Calling TTS endpoint with text: ...
[Voice] TTS response status: 200          // Should appear now
[Voice] Audio blob received: 90420 bytes  // Should appear
[Voice] Audio URL created: blob:...        // Should appear
[Voice] Audio loaded, duration: 3.2 seconds
[Voice] Audio playback started
```

**If still stops at "Calling TTS endpoint":**
→ Request is being blocked or timing out

---

## Common Issue: Request Hanging

**If request hangs (no response):**

This happens when pyttsx3 blocks the thread. The lock should fix it, but if not:

**Test manually:**
```powershell
curl -X POST http://127.0.0.1:8002/voice/synthesize `
  -H "Content-Type: application/json" `
  -d '{\"text\":\"Hello test\",\"session_id\":\"test\"}' `
  --output test.wav
```

**Expected:** Creates `test.wav` file  
**If hangs:** pyttsx3 is blocking

---

## Alternative: Browser TTS (If pyttsx3 blocks)

If pyttsx3 continues to block requests, switch to browser TTS:

**Quick fix in index.html:**

Replace the `speakText` function with:

```javascript
async function speakText(text) {
  if (!voiceEnabled || isSpeaking) return;
  
  isSpeaking = true;
  micBtn.classList.add('disabled');
  voiceStatus.textContent = '🔊 Bot speaking...';
  voiceStatus.classList.add('show', 'speaking');
  
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1.0;
  utterance.pitch = 1.0;
  utterance.volume = 1.0;
  
  utterance.onend = () => {
    stopSpeaking();
    if (voiceEnabled) {
      micBtn.classList.remove('disabled');
      voiceStatus.textContent = '🎤 Your turn';
      voiceStatus.classList.add('show');
      setTimeout(() => voiceStatus.classList.remove('show'), 2000);
    }
  };
  
  speechSynthesis.speak(utterance);
  console.log('[Voice] Speaking with browser TTS');
}
```

This uses browser's built-in TTS (no backend call), works immediately.

---

## Next Steps

1. **Wait for app to fully start** (10 seconds)
2. **Refresh browser** (Ctrl+Shift+R)
3. **Enable voice mode**
4. **Send a message**
5. **Check backend logs** - Should see "[Voice] TTS endpoint called"
6. **Check browser console** - Should see response status

If you see "[Voice] TTS endpoint called" in backend → TTS is being called  
If audio still doesn't play → It's a playback/autoplay issue  
If you don't see it → Request is blocked

**Let me know what you see in the logs!**


