# Quick Testing Guide - Evaluation Toggle

## Start Testing

1. **Restart your Flask server** (to load the new code):
   ```bash
   # Stop current server (Ctrl+C)
   python app.py
   ```

2. **Open the chat UI** in your browser:
   ```
   http://127.0.0.1:8002/index.html
   ```

3. **Look for the evaluation toggle** in the header:
   - You should see: "Evaluations: [Toggle Switch] Disabled (Fast mode)"

## Test Scenario 1: Fast Mode (Default)

### Steps:
1. **Ensure toggle is OFF** (should be disabled by default)
2. **Send a message**: "I have stomach pain"
3. **Observe**:
   - Response should come in ~1-2 seconds
   - No evaluation logs in terminal
   - Fast, smooth interaction

### Expected Terminal Output:
```
INFO:httpx:HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
INFO:rag_system:[RAG] Semantic search found 20 relevant patterns
INFO:werkzeug:127.0.0.1 - - [Date] "POST /chat/stream HTTP/1.1" 200 -
```

**No evaluation logs!** ✅

## Test Scenario 2: Full Evaluation Mode

### Steps:
1. **Click the toggle to enable** evaluations
2. **Verify UI changes**:
   - Toggle switches to green
   - Text changes to: "Enabled (+5-7 seconds per response)"
3. **Send another message**: "It's sharp pain, rate 7"
4. **Observe**:
   - Response takes ~7-8 seconds
   - Terminal shows full evaluation logs
   - Browser console shows: `[EVALUATIONS] Enabled for session xyz`

### Expected Terminal Output:
```
[EVALUATION TOGGLE] Session cf.conversation.20251203.xxxxx: Enabled
INFO:httpx:HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
INFO:rag_system:[RAG] Semantic search found 20 relevant patterns

[EVALUATION] Starting HealthBench evaluation...
INFO:httpx:HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
... (multiple evaluation API calls)
[EVALUATION] [OK] Overall Score: 0.93 (10/13 passed)
[EVALUATION] [OK] Safety Score: 0.98

[HELM] Starting HELM evaluation...
INFO:httpx:HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
... (more evaluation calls)
[HELM] [OK] Overall: 4.50/5.0
[HELM] Accuracy: 5/5, Completeness: 4/5, Clarity: 5/5

INFO:werkzeug:127.0.0.1 - - [Date] "POST /chat/stream HTTP/1.1" 200 -
```

**Full evaluation logs appear!** ✅

## Test Scenario 3: Toggle Back to Fast Mode

### Steps:
1. **Click toggle to disable** evaluations
2. **Verify UI changes**:
   - Toggle switches back to gray
   - Text changes to: "Disabled (Fast mode)"
3. **Send message**: "It started this morning"
4. **Observe**:
   - Fast response again (~1-2 seconds)
   - No evaluation logs

### Expected:
```
[EVALUATION TOGGLE] Session cf.conversation.20251203.xxxxx: Disabled
INFO:httpx:HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
INFO:werkzeug:127.0.0.1 - - [Date] "POST /chat/stream HTTP/1.1" 200 -
```

**Back to fast mode!** ✅

## Test Scenario 4: Page Refresh Persistence

### Steps:
1. **Enable evaluations** (toggle ON)
2. **Refresh the page** (F5 or Ctrl+R)
3. **Observe**: Toggle should still be ON
4. **Disable evaluations** (toggle OFF)
5. **Refresh again**
6. **Observe**: Toggle should be OFF

**Note**: Status is session-specific and persists as long as the backend is running.

## Measuring Latency

### Using Browser DevTools:
1. Open **Developer Tools** (F12)
2. Go to **Network** tab
3. Send a message
4. Look for the `/chat/stream` request
5. Check the **Time** column

**Expected Times**:
- Evaluations OFF: 1-2 seconds
- Evaluations ON: 7-8 seconds

### Using Browser Console:
The console will show:
```
[EVALUATIONS] Enabled for session xyz
```
or
```
[EVALUATIONS] Disabled for session xyz
```

## Troubleshooting

### Issue: Toggle doesn't appear
**Solution**: Hard refresh (Ctrl+Shift+R) to clear cache

### Issue: Toggle doesn't change status
**Solution**: Check browser console for errors, verify backend is running

### Issue: Evaluations still running when OFF
**Solution**: 
1. Check terminal for `[EVALUATION TOGGLE] Session xyz: Disabled`
2. Verify you're toggling before sending the message
3. Restart the server

### Issue: 404 on /evaluation/toggle
**Solution**: Backend code not loaded, restart server

## Success Criteria

✅ Toggle visible in UI
✅ Toggle changes color and text
✅ Fast mode: 1-2 seconds, no evaluation logs
✅ Full mode: 7-8 seconds, full evaluation logs
✅ Terminal shows toggle status changes
✅ Browser console shows confirmation
✅ No JavaScript errors in console
✅ No Python errors in terminal

## Summary

You should now be able to:
- **Toggle evaluations ON/OFF** with a single click
- **See immediate visual feedback** of the mode
- **Experience 4-5x faster responses** with evaluations OFF
- **Compare latency** in real-time
- **Use full evaluations** when testing/debugging

The system defaults to **fast mode** for the best user experience in production! 🚀

