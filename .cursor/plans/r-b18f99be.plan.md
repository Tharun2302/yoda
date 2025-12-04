---
name: TTS Latency Optimization Plan
overview: ""
todos:
  - id: fab58742-3737-4a73-8392-160fda50bf02
    content: Analyze all 3 text files to understand complete structure patterns
    status: completed
  - id: 47c9ea7c-99be-47f2-8dbc-fd243db6a31d
    content: Rewrite text processor with specialized parsers for each content type
    status: completed
  - id: 474b2a20-459a-44b8-b307-ccdb154068ca
    content: Remove docx-specific category mapping from RAG and app.py
    status: completed
  - id: 53bec8a7-2131-4996-9b31-d0b7f1204bd6
    content: Implement new flexible schema for clinical patterns
    status: completed
  - id: 068463b8-cd0a-413f-b530-e4d09435da73
    content: Implement priority-based retrieval (red flags first)
    status: completed
  - id: 158b22e5-7d50-4d26-8260-fd5bb6196273
    content: Test extraction on all 3 files and verify data quality
    status: completed
---

# TTS Latency Optimization Plan

## Current TTS Analysis

**Current Setup**: pyttsx3 (local, offline)
- **Latency**: 0.32s (actually very good!)
- **Quality**: Basic system voices
- **Problem**: Waits for FULL response before speaking
- **User Experience**: Feels slow because they wait 9+ seconds

## The Real Problem

TTS itself is fast (0.32s), but the **perceived latency** is high because:

1. Wait for full LLM response (~1-2s)
2. THEN convert entire text to speech (0.32s)
3. THEN play audio

**User waits**: 1-2s + 0.32s = ~2.3s before hearing ANYTHING

## Solution: Streaming TTS

Convert text to speech **as tokens arrive** from LLM, not after!

```
Current:
LLM: "Hello, I'm..." → Wait → "...HealthYoda..." → Wait → "...how can I help?"
TTS: [silence... silence... silence...] → SPEAK EVERYTHING
User: 😴 (waiting 2.3 seconds)

Streaming:
LLM: "Hello, I'm" → TTS: "Hello, I'm" → User: 👂 (hears immediately!)
LLM: "HealthYoda" → TTS: "HealthYoda" → User: 👂 (hears 0.1s later)
LLM: "how can I help?" → TTS: "how can I help?" → User: 👂 (continuous)
User: 😊 (feels instant!)
```

## Phase 1: Streaming TTS Architecture (Quick Win)

### Current Flow:
```python
# app.py - Current
full_response = ""
for token in llm_stream:
    full_response += token
    yield token  # Send to UI

# After streaming completes
audio = text_to_speech(full_response)  # Convert ALL at once
send_audio(audio)
```

### Optimized Flow:
```python
# app.py - Optimized
sentence_buffer = ""
for token in llm_stream:
    yield token  # Send to UI
    sentence_buffer += token
    
    # Convert to speech after each sentence
    if token in ['.', '!', '?']:
        audio_chunk = text_to_speech(sentence_buffer)
        yield audio_chunk  # Stream audio immediately
        sentence_buffer = ""
```

**Expected Improvement**: 
- First audio chunk: 0.1-0.2s (vs 2.3s)
- **Perceived latency: <0.2s** 🎯

### Implementation

**File**: [`app.py`](app.py) lines 1468-1520

Add sentence-based streaming:

```python
def generate():
    full_response = ""
    sentence_buffer = ""
    
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            token = chunk.choices[0].delta.content
            full_response += token
            sentence_buffer += token
            
            # Send token to UI
            yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"
            
            # Check for sentence boundaries
            if token in ['.', '!', '?', '\n'] and len(sentence_buffer.strip()) > 10:
                # Convert sentence to speech immediately
                audio_chunk = synthesize_speech_chunk(sentence_buffer.strip())
                
                # Send audio chunk to UI
                yield f"data: {json.dumps({'type': 'audio_chunk', 'audio': audio_chunk})}\n\n"
                
                sentence_buffer = ""
```

## Phase 2: Client-Side Audio Buffering

**Problem**: Network delays between audio chunks cause gaps

**Solution**: Buffer and smooth playback on client

**File**: [`index.html`](index.html) - Add audio queue

```javascript
class AudioQueue {
    constructor() {
        this.queue = [];
        this.isPlaying = false;
    }
    
    add(audioData) {
        this.queue.push(audioData);
        if (!this.isPlaying) {
            this.playNext();
        }
    }
    
    async playNext() {
        if (this.queue.length === 0) {
            this.isPlaying = false;
            return;
        }
        
        this.isPlaying = true;
        const audioData = this.queue.shift();
        
        // Play audio
        const audio = new Audio(audioData);
        audio.onended = () => this.playNext();
        await audio.play();
    }
}

const audioQueue = new AudioQueue();

// In message handler
if (data.type === 'audio_chunk') {
    audioQueue.add(data.audio);  // Queue immediately
}
```

**Expected Improvement**: Smooth, continuous playback with no gaps

## Phase 3: Faster TTS Service (Optional)

If pyttsx3 is still too slow (0.32s per sentence), consider:

### Option A: ElevenLabs (Streaming API) - BEST QUALITY

**Pros**:
- **Streaming**: True word-by-word synthesis
- **Latency**: ~100-150ms first word
- **Quality**: Best-in-class natural voices
- **Medical vocabulary**: Handles medical terms well

**Cons**:
- **Cost**: $0.30 per 1000 characters (~$0.15 per conversation)
- **Requires API key**

**Implementation**