# ⚡ QUICK SETUP INSTRUCTIONS

## Step 1: Copy Files to Your Project

Copy the entire `healthbench_integration_package` folder to your project directory.

```
your_project/
└── healthbench_integration_package/  # Paste this entire folder here
```

---

## Step 2: Install Dependencies

Open terminal in the `healthbench_integration_package` directory and run:

```bash
pip install -r requirements.txt
```

**Dependencies installed:**
- `openai` - OpenAI API
- `blobfile` - For loading datasets
- `pandas` - Data processing
- `numpy` - Numerical operations
- `jinja2` - HTML report generation
- `tqdm` - Progress bars
- `requests` - HTTP requests

---

## Step 3: Set Your OpenAI API Key

### Windows (PowerShell):
```powershell
$env:OPENAI_API_KEY = "sk-your-api-key-here"
```

### Linux/Mac (Bash):
```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

### In Python Script:
```python
import os
os.environ["OPENAI_API_KEY"] = "sk-your-api-key-here"
```

---

## Step 4: Test the Installation

Run a quick test with 5 examples:

```bash
python run_healthbench.py --model gpt-4o --debug
```

**Expected output:**
```
====================================================================
🏥 HEALTHBENCH EVALUATION
====================================================================

📝 Setting up grader model...
🤖 Setting up model to evaluate: gpt-4o

⚙️  Creating HealthBench evaluation...

🚀 Running evaluation on 5 examples...
⏳ This may take a while...
```

After completion, check the `healthbench_results/` folder for output files.

---

## Step 5: Run Full Evaluation

Once testing works, run the full evaluation:

```bash
python run_healthbench.py --model gpt-4o
```

**This will:**
- Evaluate your model on all HealthBench examples
- Take 30-60 minutes depending on API speed
- Cost approximately $10-20 in API fees (GPT-4.1 grading is expensive)
- Generate HTML and JSON reports in `healthbench_results/`

---

## 🎯 Common Commands

### Evaluate Different Models
```bash
# GPT-4o
python run_healthbench.py --model gpt-4o

# GPT-3.5 Turbo
python run_healthbench.py --model gpt-3.5-turbo

# GPT-4 Turbo
python run_healthbench.py --model gpt-4-turbo-2024-04-09
```

### Use Different Subsets
```bash
# Hard subset (more challenging)
python run_healthbench.py --model gpt-4o --subset hard

# Consensus subset (high agreement)
python run_healthbench.py --model gpt-4o --subset consensus
```

### Limited Evaluation
```bash
# Evaluate only 50 examples
python run_healthbench.py --model gpt-4o --examples 50
```

### Meta-Evaluation (Evaluate the Grader)
```bash
python run_healthbench.py --model gpt-4.1-2025-04-14 --mode meta
```

---

## 📊 Understanding the Output

### Files Generated

After running, check `healthbench_results/` folder:

1. **`healthbench_gpt-4o_YYYYMMDD_HHMMSS.html`**
   - Interactive HTML report
   - Shows conversations, rubric scores, explanations
   - Open in browser to view

2. **`healthbench_gpt-4o_YYYYMMDD_HHMMSS.json`**
   - Numerical metrics
   - Overall score and breakdown by tags
   - Bootstrap standard deviation

3. **`healthbench_gpt-4o_YYYYMMDD_HHMMSS_full.json`**
   - Complete results
   - All conversations
   - All rubric evaluations
   - Token usage stats

### Score Interpretation

| Score Range | Performance Level |
|-------------|-------------------|
| 0.8 - 1.0   | Excellent ⭐⭐⭐⭐⭐ |
| 0.6 - 0.8   | Good ⭐⭐⭐⭐ |
| 0.4 - 0.6   | Fair ⭐⭐⭐ |
| 0.0 - 0.4   | Poor ⭐⭐ |

---

## 🔧 Troubleshooting

### Problem: "Module not found" error

**Solution:** Make sure you're running from the correct directory:
```bash
cd healthbench_integration_package
python run_healthbench.py --debug
```

### Problem: API rate limit errors

**Solution:** Reduce the number of parallel threads:

Edit `run_healthbench.py` line containing `n_threads=120` and change to:
```python
n_threads=10,  # Reduced from 120
```

### Problem: "OPENAI_API_KEY not set" error

**Solution:** Set the environment variable:
```bash
# Check if it's set
echo $env:OPENAI_API_KEY  # Windows
echo $OPENAI_API_KEY       # Linux/Mac

# Set it
$env:OPENAI_API_KEY = "your-key"  # Windows
export OPENAI_API_KEY="your-key"   # Linux/Mac
```

### Problem: Evaluation taking too long

**Solution 1:** Use fewer examples:
```bash
python run_healthbench.py --model gpt-4o --examples 20
```

**Solution 2:** Use debug mode (5 examples):
```bash
python run_healthbench.py --model gpt-4o --debug
```

### Problem: High API costs

**Tips to reduce costs:**
1. Use `--debug` mode for testing (5 examples)
2. Use `--examples 20` for partial evaluation
3. Consider using cheaper models like `gpt-3.5-turbo` for testing
4. Note: The grader always uses GPT-4.1 (expensive but necessary for accuracy)

---

## 📈 Next Steps

### Integrate into Your Own Code

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path("healthbench_integration_package")))

from healthbench_eval import HealthBenchEval
from samplers.chat_completion_sampler import ChatCompletionSampler, OPENAI_SYSTEM_MESSAGE_API

# Your custom evaluation logic here
grader = ChatCompletionSampler(
    model="gpt-4.1-2025-04-14",
    system_message=OPENAI_SYSTEM_MESSAGE_API,
    max_tokens=2048,
)

model = ChatCompletionSampler(
    model="gpt-4o",
    system_message=OPENAI_SYSTEM_MESSAGE_API,
    max_tokens=2048,
)

eval_obj = HealthBenchEval(grader_model=grader, num_examples=10)
result = eval_obj(model)

print(f"Score: {result.score:.4f}")
```

### Customize the Evaluation

See `HEALTHBENCH_INTEGRATION_GUIDE.md` for detailed customization options:
- Different subsets
- Custom scoring
- Physician completion modes
- Adjusting threads and repeats

---

## ✅ Verification Checklist

Before running full evaluation, verify:

- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] API key set (`$env:OPENAI_API_KEY` or `export OPENAI_API_KEY`)
- [ ] Debug mode works (`python run_healthbench.py --debug`)
- [ ] Output directory created (`healthbench_results/`)
- [ ] HTML report opens in browser
- [ ] JSON metrics are readable

---

## 💡 Pro Tips

1. **Start with debug mode** (`--debug`) to test everything works
2. **Monitor your OpenAI usage** at https://platform.openai.com/usage
3. **Save the HTML reports** - they're very useful for analysis
4. **Compare multiple models** by running the same eval on different models
5. **Use version control** to track results over time

---

## 📞 Need More Help?

- Read `HEALTHBENCH_INTEGRATION_GUIDE.md` for comprehensive documentation
- Check `README.md` for quick reference
- Examine test files for usage examples
- Review the source code comments

---

**You're all set! 🎉**

Run `python run_healthbench.py --debug` to get started!

