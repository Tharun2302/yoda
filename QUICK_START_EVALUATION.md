# Quick Start: HealthBench Evaluation

## ✅ INTEGRATION STATUS: COMPLETE

HealthBench evaluation is **FULLY WORKING** in your chatbot!

---

## 🚀 How to Use (3 Steps)

### Step 1: Start the Chatbot

```bash
python app.py
```

### Step 2: Chat Normally

Just have a conversation! Nothing special needed.

### Step 3: See Results

Every bot response shows evaluation scores:

```
[EVALUATION] [OK] Score: 0.88 (7/8 passed)
```

---

## 📊 What Gets Evaluated

**EVERY chatbot response** is automatically evaluated against:

1. ✓ Clear language
2. ✓ Empathy  
3. ✓ Asking relevant questions
4. ✓ Avoiding premature diagnosis
5. ✓ Accurate information
6. ✓ Safe recommendations
7. ✓ Professional tone
8. ✓ Acknowledging limitations

---

## 📝 Where to Find Results

### 1. Console Output (Real-time)
```
[EVALUATION] [OK] Score: 0.88 (7/8 passed)
```

### 2. JSON File (History)
```
healthbench_results.json
```
Contains last 100 evaluations with full details

### 3. Langfuse Dashboard (Optional)
If you configure Langfuse keys, scores appear there too

---

## ⚙️ Configuration

### Turn Evaluation On/Off

Edit `.env` file:
```bash
# Enable evaluation
HEALTHBENCH_EVAL_ENABLED=true

# Disable evaluation
HEALTHBENCH_EVAL_ENABLED=false
```

### Choose Grader Model

```bash
# Faster, cheaper (recommended)
HEALTHBENCH_GRADER_MODEL=gpt-4o-mini

# More accurate, expensive
HEALTHBENCH_GRADER_MODEL=gpt-4
```

---

## 🧪 Test It

Run the test to verify everything works:

```bash
python test_healthbench_integration.py
```

Expected output:
```
[OK] All modules imported successfully
[OK] Evaluator initialized and enabled
[OK] Storage initialized
[OK] HealthBench is FULLY INTEGRATED into your HYoda chatbot!
```

---

## 💰 Cost

Using `gpt-4o-mini` (recommended):
- ~$0.001 per bot response
- ~$0.01 per 10-message conversation

Very affordable for quality assurance!

---

## ❓ Troubleshooting

**Evaluation not running?**
- Check `OPENAI_API_KEY` is set in `.env`
- Check `HEALTHBENCH_EVAL_ENABLED=true` in `.env`

**API quota exceeded?**
- Add credits to OpenAI account
- Or temporarily disable evaluation

---

## 📚 More Info

See `HEALTHBENCH_INTEGRATION_COMPLETE.md` for:
- Full technical details
- Customization options
- Architecture explanation
- Advanced configuration

---

**You're all set! Start chatting and watch your bot get evaluated in real-time! 🎉**

