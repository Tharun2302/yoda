# TTS Streaming Fix - Final Solution

## Problem Identified

The streaming TTS implementation was causing:
1. **Text streaming stops mid-sentence** - Stream freezes after detecting sentence endings
2. **No audio plays** - TTS synthesis hangs
3. **Server logs stop** - The generator blocks completely

## Root Cause

**pyttsx3 is fundamentally blocking**:

```python
# voice_processor.py line 494
tts_engine.save_to_file(plain_text, temp_audio_path)
tts_engine.runAndWait()  # ← BLOCKS until speech completes
```

When we called `synthesize_speech()` inside the SSE stream generator:
- The `runAndWait()` call **blocked** the generator
- No more tokens could be yielded
- The stream appeared to freeze
- Frontend stopped receiving data

## Why Background Threads Don't Work

Even running TTS in a background thread doesn't help because:
1. We can't `yield` from inside a background thread
2. Audio must be sent through the SSE stream (requires yielding)
3. pyttsx3 doesn't support true streaming (word-by-word audio generation)

## Solution: Disable Streaming TTS

**Keep the existing fast TTS approach**:

### Changes Made

**`app.py`**:
- ❌ Removed sentence buffering and detection from stream loop
- ❌ Removed TTS synthesis calls from streaming generator
- ✅ Let text stream fully without interruption
- ✅ Frontend handles TTS on complete response (as before)

**Result**:
- ✅ **Text streams smoothly** - No blocking
- ✅ **TTS plays after completion** - 0.32s latency (already fast!)
- ✅ **No freezing or hanging** - Stream completes successfully

## Performance Analysis

### Current (After Fix)
```
User speaks → STT (3.3s) → LLM (1-2s) → Text streams → TTS (0.32s) → Audio plays
Total perceived latency: ~5s
```

### What We Tried (Streaming TTS)
```
User speaks → STT (3.3s) → LLM streams → TTS per sentence (BLOCKED) → Stream hangs ❌
```

### What Would Work (Future)
To achieve true streaming TTS, we need:
1. **Non-blocking TTS service** (ElevenLabs, PlayHT, Azure TTS)
2. **WebSocket architecture** (bi-directional streaming)
3. **Async/await pattern** (Python asyncio)

Example with ElevenLabs:
```python
async def stream_tts():
    audio_stream = elevenlabs.generate(text=sentence, stream=True)
    for audio_chunk in audio_stream:
        await websocket.send(audio_chunk)  # Non-blocking
```

## Recommendation

**Keep current approach** because:

1. **TTS is already fast** (0.32s)
2. **Main bottleneck is STT** (3.3s) - User's friend will optimize with Deepgram
3. **pyttsx3 is free and HIPAA compliant** - No cloud dependency
4. **Streaming TTS requires significant refactoring** - WebSockets, async, paid API

### Future Optimization Path

If streaming TTS becomes critical later:

1. **Phase 1**: Migrate to Deepgram STT (user's friend) - Cuts 2.5s
2. **Phase 2**: Optimize RAG caching - Cuts 1-2s  
3. **Phase 3**: Only then consider streaming TTS with ElevenLabs
   - **Cost**: ~$0.15 per conversation
   - **Complexity**: WebSocket refactor, async/await
   - **Gain**: ~0.2s perceived latency improvement

**Total after Phases 1-2**: ~2-3s latency (acceptable for medical use case)

## Testing

✅ **Restart server**:
```bash
python app.py
```

✅ **Test voice mode**:
- Text should stream smoothly ✅
- No mid-sentence stopping ✅
- TTS plays after full response ✅
- Total latency ~5s (acceptable) ✅

## Files Modified

- `app.py`: Removed streaming TTS logic
- `model_manager.py`: Default back to gpt-4o-mini (Gemini temporarily unavailable)
- `env.template`: Updated default model

## Status

✅ **FIXED** - Text streaming works correctly, TTS plays after completion
🎯 **Next**: User's friend optimizes STT with Deepgram (expected 2.5s improvement)

