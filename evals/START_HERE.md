# 🎯 START HERE - HealthBench Integration Package

## ✅ What You Have

You now have a **complete, ready-to-use HealthBench integration package** that can be dropped into any Python project!

---

## 📦 Package Contents

```
healthbench_integration_package/
│
├── 📖 START_HERE.md                      ← You are here!
├── 📖 README.md                           Quick reference guide
├── 📖 SETUP_INSTRUCTIONS.md               Step-by-step setup (READ THIS NEXT!)
├── 📖 HEALTHBENCH_INTEGRATION_GUIDE.md    Comprehensive guide
│
├── ⚙️ requirements.txt                    Dependencies to install
├── 🚀 run_healthbench.py                  Main runner script
│
├── 🧠 healthbench_eval.py                 Core evaluation logic (619 lines)
├── 🔬 healthbench_meta_eval.py            Meta-evaluation (337 lines)
├── 🧪 healthbench_eval_test.py            Unit tests
├── 🧪 healthbench_meta_eval_test.py       Meta-eval tests
│
├── 📋 types.py                            Base classes
├── 🛠️ common.py                           Utility functions
├── 📁 __init__.py                         Package init
│
└── samplers/
    ├── 🤖 chat_completion_sampler.py      OpenAI API wrapper
    └── 📁 __init__.py                     Samplers init
```

---

## 🚀 3-Minute Quickstart

### Step 1: Install Dependencies (1 minute)
```bash
cd healthbench_integration_package
pip install -r requirements.txt
```

### Step 2: Set API Key (30 seconds)
```bash
# Windows PowerShell:
$env:OPENAI_API_KEY = "sk-your-api-key"

# Linux/Mac:
export OPENAI_API_KEY="sk-your-api-key"
```

### Step 3: Run Test (1-2 minutes)
```bash
python run_healthbench.py --model gpt-4o --debug
```

**That's it!** 🎉

If this works, you're ready to run full evaluations.

---

## 📚 What to Read Next

### If you want to:

**Just get it working quickly:**
→ Read `SETUP_INSTRUCTIONS.md`

**Understand how everything works:**
→ Read `HEALTHBENCH_INTEGRATION_GUIDE.md`

**Quick command reference:**
→ Read `README.md`

**Customize or integrate into your code:**
→ Read `HEALTHBENCH_INTEGRATION_GUIDE.md` (Customization section)

---

## 🎓 What is HealthBench?

HealthBench is a medical AI evaluation framework that:

✅ **Evaluates medical LLMs** on real patient conversation scenarios  
✅ **Uses rubric-based grading** with multiple criteria per conversation  
✅ **Employs LLM-as-judge** (GPT-4.1) to score responses  
✅ **Provides detailed feedback** on what went right/wrong  
✅ **Includes statistical rigor** (bootstrap std, repeats)  
✅ **Supports meta-evaluation** to validate grader quality  

**Published by:** OpenAI  
**Dataset:** Automatically downloaded from Azure  
**License:** MIT  

---

## 🔥 Key Features

### 1. Easy to Use
```bash
python run_healthbench.py --model gpt-4o --debug
```

### 2. Multiple Evaluation Modes
- **Standard**: Full HealthBench dataset
- **Hard**: More challenging subset
- **Consensus**: High physician agreement subset
- **Meta**: Evaluate the grader itself

### 3. Rich Output
- 📊 HTML reports with conversations
- 📈 JSON metrics with statistics
- 💾 Full results with all data

### 4. Flexible Integration
- Use as standalone tool
- Import as Python module
- Customize for your needs

---

## 💰 Cost Estimation

**Debug Mode (5 examples):** ~$0.50  
**Partial Eval (50 examples):** ~$5.00  
**Full Evaluation (~250 examples):** ~$20-30  

*Costs vary based on response length and model chosen*

**Note:** The grader always uses GPT-4.1 (necessary for accurate evaluation)

---

## ⚡ Common Usage Patterns

### Pattern 1: Quick Test
```bash
python run_healthbench.py --model gpt-4o --debug
```

### Pattern 2: Evaluate Your Model
```bash
python run_healthbench.py --model gpt-4o
```

### Pattern 3: Compare Models
```bash
python run_healthbench.py --model gpt-4o
python run_healthbench.py --model gpt-3.5-turbo
python run_healthbench.py --model gpt-4-turbo-2024-04-09
```

### Pattern 4: Hard Cases Only
```bash
python run_healthbench.py --model gpt-4o --subset hard
```

### Pattern 5: Limited Budget
```bash
python run_healthbench.py --model gpt-4o --examples 20
```

---

## 🎯 Success Checklist

Before running full evaluation:

- [ ] Installed dependencies (`pip install -r requirements.txt`)
- [ ] Set API key in environment variable
- [ ] Ran debug mode successfully
- [ ] Checked output in `healthbench_results/` folder
- [ ] Opened HTML report in browser
- [ ] Reviewed JSON metrics
- [ ] Understand costs (see above)

---

## 🔧 Integration into Another Project

### Option A: Copy Entire Folder
```bash
# Copy to your project
cp -r healthbench_integration_package your_project/

# Use it
cd your_project/healthbench_integration_package
python run_healthbench.py --model your-model
```

### Option B: Import as Module
```python
import sys
sys.path.insert(0, 'path/to/healthbench_integration_package')

from healthbench_eval import HealthBenchEval
from samplers.chat_completion_sampler import ChatCompletionSampler

# Your code here...
```

### Option C: Merge into Existing Codebase
1. Copy files to your source directory
2. Update imports (remove relative imports)
3. Install requirements
4. Adapt runner script to your needs

---

## 📊 Example Output

```
====================================================================
🏥 HEALTHBENCH EVALUATION
====================================================================

📝 Setting up grader model...
🤖 Setting up model to evaluate: gpt-4o

⚙️  Creating HealthBench evaluation...

🚀 Running evaluation on 5 examples...
⏳ This may take a while...

✅ HTML report saved to: healthbench_results/healthbench_gpt-4o_20251119_210530.html
✅ Metrics saved to: healthbench_results/healthbench_gpt-4o_20251119_210530.json
✅ Full results saved to: healthbench_results/healthbench_gpt-4o_20251119_210530_full.json

====================================================================
📊 RESULTS FOR GPT-4O
====================================================================

🎯 Overall Score: 0.7543

Detailed Metrics:
  • overall_score:mean: 0.7543
  • overall_score:bootstrap_std: 0.0234
  • overall_score:n_samples: 5
  • medical_accuracy: 0.8100
  • empathy: 0.7200
  • safety: 0.9100

====================================================================

✨ Evaluation complete!
```

---

## ❓ FAQ

**Q: Do I need to download the dataset?**  
A: No! It's automatically downloaded from Azure blob storage.

**Q: Can I use models other than OpenAI?**  
A: The current implementation is OpenAI-specific, but you can adapt the `SamplerBase` class for other APIs.

**Q: How long does a full evaluation take?**  
A: Usually 30-60 minutes depending on API speed and threading.

**Q: Can I stop and resume?**  
A: No, but you can run with `--examples N` to evaluate in chunks.

**Q: What if I hit rate limits?**  
A: Edit `run_healthbench.py` and reduce `n_threads` from 120 to 10-20.

---

## 🚨 Troubleshooting

**Issue:** Module import errors  
**Fix:** Make sure you're in the correct directory and have `__init__.py` files

**Issue:** API rate limits  
**Fix:** Reduce `n_threads` in `run_healthbench.py`

**Issue:** High costs  
**Fix:** Use `--debug` or `--examples 20` for testing

**Issue:** Slow execution  
**Fix:** Check your internet connection and API tier

---

## 🎉 You're Ready!

**Next steps:**

1. Read `SETUP_INSTRUCTIONS.md` for detailed setup
2. Run `python run_healthbench.py --debug` to test
3. Run full evaluation: `python run_healthbench.py --model gpt-4o`
4. Check results in `healthbench_results/` folder

**Happy Evaluating! 🏥✨**

---

*Need more details? Check the other documentation files in this package.*

