<!-- af693928-1994-4659-a4bb-6f155c911a06 5b2c77cf-3ea8-4d9a-b49b-f95f317f0003 -->
# Hands-Free Voice Mode Implementation Plan (HIPAA Compliant)

## Architecture Decision: HTTP/SSE (Current) vs WebSockets

**Decision: Keep HTTP/SSE approach** - No additional cost, simpler implementation, HIPAA compliant with HTTPS.

- WebSockets would require WSS (WebSocket Secure) for HIPAA
- Current SSE approach works fine for chunked audio uploads
- No cost difference (both are free)
- Easier to maintain and debug

## HIPAA Compliance Requirements

All implementations must ensure:

1. **Encryption in Transit**: All connections use HTTPS (WSS if WebSockets used)
2. **No Persistent Audio Storage**: Audio chunks processed and discarded immediately after transcription
3. **Secure Session Management**: Session IDs properly managed
4. **Access Controls**: Existing authentication mechanisms remain in place
5. **Audit Logging**: Voice interactions logged (already implemented)

## 1. Add Hands-Free Confirmation Modal

Modify `index.html` to include a modal dialog that appears when enabling voice mode.

- **HTML**: Add a modal structure (`div.modal`, `div.modal-content`) with:
- Warning message: "Voice mode keeps the microphone always on. Your audio is processed securely and not stored."
- Buttons: "Continue" (Enables Hands-Free) and "Switch to Chat" (Cancels).
- **CSS**: Add styles for the modal (centered, overlay, buttons).

## 2. Implement Silence Detection (VAD) - Client-Side Only

Add a `detectSilence` function in `index.html` using the Web Audio API to monitor microphone volume.

- **Logic**: 
- Create an `AudioContext` and `AnalyserNode` attached to the media stream.
- Monitor volume levels in a loop (client-side only - no data sent until speech detected).
- If volume exceeds a threshold, mark as "speaking".
- If volume drops below threshold for 2.0 seconds *after* speaking has started, trigger `stopRecording()`.
- Add a max recording limit (e.g., 60s) as a fallback.
- **HIPAA Note**: All audio processing happens client-side until user speaks - no continuous streaming to server.

## 3. Update Voice Logic (`index.html`)

Refactor the voice handling functions:

- **`toggleVoiceMode()`**:
- Instead of immediately enabling voice, show the Confirmation Modal.
- If "Continue" is clicked: Set `voiceEnabled = true`, `isHandsFree = true`, and call `startRecording()`.
- If "Switch to Chat" is clicked: Keep `voiceEnabled = false`.
- **`startRecording()`**:
- Integrate the `detectSilence` function when recording starts.
- Ensure it doesn't start if the bot is speaking.
- **`transcribeAudio()`**:
- If `isHandsFree` is true:
- Automatically call `sendMessage()` after transcription (if text is not empty and meets minimum length).
- Audio blob is sent via HTTPS POST (encrypted in transit).
- **`speakText()`**:
- In the `onend` event (after bot finishes speaking):
- If `isHandsFree` is true, automatically call `startRecording()` after a short delay (e.g., 500ms) to listen for the user's response.

## 4. Backend HIPAA Compliance (`app.py`)

Ensure `/voice/transcribe` endpoint:

- Processes audio immediately and discards the file after transcription
- No persistent storage of audio files
- Transcription text handled according to existing HIPAA policies
- All connections require HTTPS in production

## 5. Safeguards

- Prevent auto-sending if the transcription is empty, too short, or just noise.
- Ensure the user can still manually stop recording or disable voice mode (clicking "Voice On" button toggles it off).
- Add visual indicator when microphone is always-on (different from push-to-talk).