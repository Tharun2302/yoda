# Quick Start - HELM + HealthBench Parallel Evaluation

## ✅ What You Have Now

Every chatbot response is evaluated by **TWO systems simultaneously**:

1. **HealthBench** (OpenAI) - Safety & Communication
2. **HELM** (Stanford) - Medical Accuracy & Quality

---

## 🚀 How to Activate

### **Just Restart Your App:**
```bash
python app.py
```

**That's it!** Both systems will automatically evaluate every response.

---

## 📊 What You'll See

### **Console Output:**
```
[EVALUATION] [OK] Overall Score: 0.88 (HealthBench)
[EVALUATION] [OK] Safety Score: 0.95
[HELM] [OK] Overall: 4.2/5.0
[HELM] Accuracy: 4/5, Completeness: 4/5, Clarity: 5/5
```

### **Dashboard:**
- New "Average HELM Score" stat card
- Each evaluation shows both HealthBench AND HELM results
- HELM section with 3 criteria breakdown

---

## 🎯 What Each System Evaluates

### **HealthBench:**
- Safety (avoids harm)
- Empathy (compassionate)
- Communication (clear)
- Red flags (5 dangerous behaviors)
- **Output:** 0.88 (88%)

### **HELM:**
- Accuracy (medical correctness, 1-5)
- Completeness (thoroughness, 1-5)
- Clarity (understandability, 1-5)
- **Output:** 4.2/5.0 (84%)

---

## ⚙️ Configuration

Edit `.env` file:

```bash
# Enable both (default)
HEALTHBENCH_EVAL_ENABLED=true
HELM_EVAL_ENABLED=true

# Disable HELM only (keep HealthBench)
HELM_EVAL_ENABLED=false

# Disable both
HEALTHBENCH_EVAL_ENABLED=false
HELM_EVAL_ENABLED=false
```

---

## 💰 Cost

- HealthBench: ~$0.002 per response
- HELM: ~$0.001 per response
- **Both: ~$0.003 per response**
- **100 conversations: ~$3-5 total**

Very affordable for comprehensive evaluation!

---

## 🧪 Test It

```bash
python test_helm_integration.py
```

Should show:
```
[OK] Both evaluation systems ready
[OK] Statistics calculation works
[OK] HELM + HealthBench integration complete!
```

---

## 📚 Full Documentation

- **HELM_INTEGRATION_COMPLETE.md** - Complete guide
- **RESTART_TO_ACTIVATE.txt** - Quick activation guide
- **test_helm_integration.py** - Test suite

---

**Just restart the app and start chatting!** 

Every response will be evaluated by both HealthBench AND HELM! 🎉

