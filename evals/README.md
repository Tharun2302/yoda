# HealthBench Integration Package

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set API Key
```bash
# Windows PowerShell
$env:OPENAI_API_KEY = "your-api-key-here"

# Linux/Mac
export OPENAI_API_KEY="your-api-key-here"
```

### 3. Run Evaluation
```bash
# Test with 5 examples (debug mode)
python run_healthbench.py --model gpt-4o --debug

# Full evaluation
python run_healthbench.py --model gpt-4o
```

---

## 📂 Package Contents

```
healthbench_integration_package/
├── README.md                          # This file
├── requirements.txt                   # Dependencies
├── run_healthbench.py                 # Runner script ⭐
├── healthbench_eval.py                # Main evaluation
├── healthbench_meta_eval.py           # Meta-evaluation
├── healthbench_eval_test.py           # Tests
├── healthbench_meta_eval_test.py      # Tests
├── types.py                           # Base classes
├── common.py                          # Utilities
└── samplers/
    ├── __init__.py
    └── chat_completion_sampler.py     # OpenAI API wrapper
```

---

## 🎯 Usage Examples

### Standard Evaluation
```bash
# Evaluate GPT-4o
python run_healthbench.py --model gpt-4o

# Evaluate GPT-3.5 Turbo
python run_healthbench.py --model gpt-3.5-turbo

# Hard subset
python run_healthbench.py --model gpt-4o --subset hard

# Consensus subset
python run_healthbench.py --model gpt-4o --subset consensus

# Limited examples
python run_healthbench.py --model gpt-4o --examples 50
```

### Meta-Evaluation
```bash
# Evaluate how well GPT-4.1 performs as a grader
python run_healthbench.py --model gpt-4.1-2025-04-14 --mode meta
```

---

## 📊 Output

Results are saved to `healthbench_results/` directory:

1. **HTML Report**: Visual report with conversations and scores
2. **Metrics JSON**: Numerical metrics
3. **Full Results JSON**: Complete data including conversations

---

## 🔧 Integration into Your Project

### Option 1: Copy Files Directly
1. Copy all files to your project directory
2. Install requirements: `pip install -r requirements.txt`
3. Run: `python run_healthbench.py`

### Option 2: Import as Module
```python
from healthbench_eval import HealthBenchEval
from samplers.chat_completion_sampler import ChatCompletionSampler, OPENAI_SYSTEM_MESSAGE_API

# Set up grader
grader = ChatCompletionSampler(
    model="gpt-4.1-2025-04-14",
    system_message=OPENAI_SYSTEM_MESSAGE_API,
    max_tokens=2048,
)

# Set up model to evaluate
model = ChatCompletionSampler(
    model="gpt-4o",
    system_message=OPENAI_SYSTEM_MESSAGE_API,
    max_tokens=2048,
)

# Create and run evaluation
eval_obj = HealthBenchEval(
    grader_model=grader,
    num_examples=10,  # or None for all
)
result = eval_obj(model)

print(f"Score: {result.score:.4f}")
```

---

## 🧪 Testing

Run unit tests:
```bash
python healthbench_eval_test.py
python healthbench_meta_eval_test.py
```

---

## ⚙️ Configuration Options

### HealthBenchEval Parameters

```python
HealthBenchEval(
    grader_model=grader,        # Model used to grade rubrics
    num_examples=None,          # Number of examples (None = all)
    n_repeats=1,                # Repeat each sample N times
    n_threads=120,              # Parallel threads (reduce if rate limited)
    subset_name=None,           # None, "hard", or "consensus"
    physician_completions_mode=None,  # Evaluate physician completions
    run_reference_completions=False,  # Evaluate reference completions
)
```

### Common Issues

**Rate Limits**: Reduce `n_threads` to 10-20
```python
eval_obj = HealthBenchEval(grader_model=grader, n_threads=10)
```

**API Errors**: Check your API key and billing
```python
import os
print(os.environ.get("OPENAI_API_KEY"))
```

---

## 📚 Understanding Scores

- **0.0 - 0.4**: Poor performance
- **0.4 - 0.6**: Fair performance  
- **0.6 - 0.8**: Good performance
- **0.8 - 1.0**: Excellent performance

Scores are calculated from rubric-based criteria evaluated by GPT-4.1.

---

## 🔗 Resources

- **Dataset**: Automatically loaded from Azure blob storage
- **License**: MIT License
- **Paper**: [OpenAI HealthBench](https://openai.com/index/healthbench)

---

## 💡 Tips

1. **Start small**: Use `--debug` to test with 5 examples
2. **Monitor costs**: Grading uses GPT-4.1 (expensive)
3. **Check HTML reports**: Very useful for understanding failures
4. **Compare models**: Run same eval on multiple models

---

## ❓ Need Help?

Check the full integration guide: `HEALTHBENCH_INTEGRATION_GUIDE.md`

Or examine the test files for usage examples.

