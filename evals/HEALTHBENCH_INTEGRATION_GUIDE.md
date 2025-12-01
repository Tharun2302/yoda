# HealthBench Integration Guide

## Complete Step-by-Step Guide to Integrate HealthBench into Your Project

This guide will help you integrate the complete HealthBench evaluation system into any Python project.

---

## 📋 **What You're Getting**

HealthBench is a medical LLM evaluation framework that:
- Uses **rubric-based grading** with LLM-as-judge
- Evaluates medical conversation quality
- Supports positive and negative scoring criteria
- Provides statistical robustness (bootstrap std, repeats)
- Includes meta-evaluation for grader validation

---

## 📦 **Required Files**

You need to copy these files to your project:

### **Core Files:**
1. `healthbench_eval.py` - Main evaluation logic (619 lines)
2. `healthbench_meta_eval.py` - Meta-evaluation (337 lines)
3. `types.py` - Data types and base classes (67 lines)
4. `common.py` - Utility functions (409 lines)
5. `chat_completion_sampler.py` - OpenAI API wrapper (97 lines)

### **Test Files (Optional but Recommended):**
6. `healthbench_eval_test.py` - Unit tests for scoring
7. `healthbench_meta_eval_test.py` - Unit tests for meta-eval

---

## 🔧 **Step-by-Step Integration**

### **STEP 1: Install Dependencies**

```bash
pip install openai>=1.0.0
pip install blobfile
pip install pandas
pip install numpy
pip install jinja2
pip install tqdm
pip install requests
```

### **STEP 2: Create Project Structure**

```
your_project/
├── evals/
│   ├── __init__.py
│   ├── types.py                          # Copy from simple-evals
│   ├── common.py                         # Copy from simple-evals
│   ├── healthbench_eval.py               # Copy from simple-evals
│   ├── healthbench_meta_eval.py          # Copy from simple-evals
│   ├── healthbench_eval_test.py          # Copy from simple-evals (optional)
│   ├── healthbench_meta_eval_test.py     # Copy from simple-evals (optional)
│   └── samplers/
│       ├── __init__.py
│       └── chat_completion_sampler.py    # Copy from simple-evals
└── run_healthbench.py                    # Your runner script (we'll create this)
```

### **STEP 3: Set Environment Variable**

```bash
# Windows PowerShell:
$env:OPENAI_API_KEY = "your-api-key-here"

# Linux/Mac:
export OPENAI_API_KEY="your-api-key-here"

# Or in Python:
import os
os.environ["OPENAI_API_KEY"] = "your-api-key-here"
```

### **STEP 4: Fix Import Paths**

After copying files, update the imports in each file:

#### In `healthbench_eval.py`:
```python
# Change from:
from . import common
from .sampler.chat_completion_sampler import ...
from .types import ...

# To:
from evals import common
from evals.samplers.chat_completion_sampler import ...
from evals.types import ...
```

#### In `healthbench_meta_eval.py`:
```python
# Change from:
from . import common
from .healthbench_eval import ...
from .types import ...

# To:
from evals import common
from evals.healthbench_eval import ...
from evals.types import ...
```

#### In `chat_completion_sampler.py`:
```python
# Change from:
from ..types import ...

# To:
from evals.types import ...
```

### **STEP 5: Create Runner Script**

Create `run_healthbench.py`:

```python
"""
Runner script for HealthBench evaluation
"""
import os
from datetime import datetime
from pathlib import Path
import json

from evals.healthbench_eval import HealthBenchEval
from evals.healthbench_meta_eval import HealthBenchMetaEval
from evals.samplers.chat_completion_sampler import (
    ChatCompletionSampler,
    OPENAI_SYSTEM_MESSAGE_API,
)
from evals import common

def run_healthbench_standard(model_name="gpt-4o", num_examples=None):
    """Run standard HealthBench evaluation"""
    
    # Set up the grader model (used to grade rubrics)
    grading_sampler = ChatCompletionSampler(
        model="gpt-4.1-2025-04-14",
        system_message=OPENAI_SYSTEM_MESSAGE_API,
        max_tokens=2048,
    )
    
    # Set up the model to be evaluated
    model_sampler = ChatCompletionSampler(
        model=model_name,
        system_message=OPENAI_SYSTEM_MESSAGE_API,
        max_tokens=2048,
    )
    
    # Create the evaluation
    eval_obj = HealthBenchEval(
        grader_model=grading_sampler,
        num_examples=num_examples,  # None = all examples
        n_repeats=1,
        n_threads=120,
        subset_name=None,  # or "hard" or "consensus"
    )
    
    # Run the evaluation
    print(f"Running HealthBench evaluation on {model_name}...")
    result = eval_obj(model_sampler)
    
    # Save results
    now = datetime.now()
    date_str = now.strftime("%Y%m%d_%H%M%S")
    
    # Save HTML report
    report_filename = f"healthbench_{model_name}_{date_str}.html"
    Path(report_filename).write_text(common.make_report(result))
    print(f"✅ Report saved to {report_filename}")
    
    # Save metrics JSON
    metrics = result.metrics | {"score": result.score}
    metrics = dict(sorted(metrics.items()))
    result_filename = f"healthbench_{model_name}_{date_str}.json"
    Path(result_filename).write_text(json.dumps(metrics, indent=2))
    print(f"✅ Metrics saved to {result_filename}")
    
    # Print results
    print(f"\n📊 Results for {model_name}:")
    print(f"Score: {result.score:.4f}")
    for key, value in metrics.items():
        if key != "score":
            print(f"  {key}: {value}")
    
    return result

def run_healthbench_meta(model_name="gpt-4o", num_examples=None):
    """Run HealthBench meta-evaluation (evaluates the evaluator)"""
    
    grading_sampler = ChatCompletionSampler(
        model=model_name,
        system_message=OPENAI_SYSTEM_MESSAGE_API,
        max_tokens=2048,
    )
    
    eval_obj = HealthBenchMetaEval(
        grader_model=grading_sampler,
        num_examples=num_examples,
        n_repeats=1,
        n_threads=120,
    )
    
    # Create a dummy sampler (not used in meta-eval)
    from evals.types import SamplerBase
    dummy_sampler = SamplerBase()
    
    print(f"Running HealthBench meta-evaluation on {model_name}...")
    result = eval_obj(dummy_sampler)
    
    # Save results
    now = datetime.now()
    date_str = now.strftime("%Y%m%d_%H%M%S")
    
    report_filename = f"healthbench_meta_{model_name}_{date_str}.html"
    Path(report_filename).write_text(common.make_report(result))
    print(f"✅ Report saved to {report_filename}")
    
    metrics = result.metrics | {"score": result.score}
    result_filename = f"healthbench_meta_{model_name}_{date_str}.json"
    Path(result_filename).write_text(json.dumps(metrics, indent=2))
    print(f"✅ Metrics saved to {result_filename}")
    
    print(f"\n📊 Meta-Evaluation Results for {model_name}:")
    print(f"Score: {result.score:.4f}")
    
    return result

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run HealthBench Evaluation")
    parser.add_argument("--model", type=str, default="gpt-4o", help="Model to evaluate")
    parser.add_argument("--mode", type=str, choices=["standard", "meta"], default="standard", 
                       help="Evaluation mode")
    parser.add_argument("--examples", type=int, default=None, 
                       help="Number of examples (None = all)")
    parser.add_argument("--debug", action="store_true", 
                       help="Debug mode (5 examples)")
    
    args = parser.parse_args()
    
    num_examples = 5 if args.debug else args.examples
    
    if args.mode == "standard":
        run_healthbench_standard(args.model, num_examples)
    else:
        run_healthbench_meta(args.model, num_examples)
```

---

## 🚀 **Usage Examples**

### **Run Standard HealthBench Evaluation:**
```bash
# Evaluate GPT-4o on all examples
python run_healthbench.py --model gpt-4o --mode standard

# Debug mode (5 examples only)
python run_healthbench.py --model gpt-4o --mode standard --debug

# Specific number of examples
python run_healthbench.py --model gpt-4o --mode standard --examples 50
```

### **Run Meta-Evaluation:**
```bash
python run_healthbench.py --model gpt-4.1-2025-04-14 --mode meta
```

### **Evaluate Different Models:**
```bash
# GPT-3.5
python run_healthbench.py --model gpt-3.5-turbo

# GPT-4 Turbo
python run_healthbench.py --model gpt-4-turbo-2024-04-09

# GPT-4.1
python run_healthbench.py --model gpt-4.1-2025-04-14
```

---

## 🧪 **Testing the Integration**

Run the unit tests:

```bash
# Test score calculation
python -m evals.healthbench_eval_test

# Test meta-evaluation metrics
python -m evals.healthbench_meta_eval_test
```

---

## 📊 **Understanding the Output**

### **Output Files:**

1. **HTML Report** (`healthbench_*.html`)
   - Visual report with conversation history
   - Rubric scores and explanations
   - Individual sample results

2. **Metrics JSON** (`healthbench_*.json`)
   - `overall_score`: Main metric (0-1)
   - `overall_score:mean`: Average score
   - `overall_score:bootstrap_std`: Statistical uncertainty
   - `overall_score:n_samples`: Number of samples
   - Tag-specific scores (e.g., medical accuracy, empathy, etc.)

### **Score Interpretation:**
- **0.0 - 0.4**: Poor performance
- **0.4 - 0.6**: Fair performance
- **0.6 - 0.8**: Good performance
- **0.8 - 1.0**: Excellent performance

---

## 🔄 **Customization Options**

### **1. Use Different Subsets:**

```python
# Hard subset (more challenging cases)
eval_obj = HealthBenchEval(
    grader_model=grading_sampler,
    subset_name="hard",
)

# Consensus subset (high inter-rater agreement)
eval_obj = HealthBenchEval(
    grader_model=grading_sampler,
    subset_name="consensus",
)
```

### **2. Adjust Threading:**

```python
# Fewer threads for API rate limits
eval_obj = HealthBenchEval(
    grader_model=grading_sampler,
    n_threads=10,  # Default: 120
)
```

### **3. Multiple Repeats (for variance):**

```python
eval_obj = HealthBenchEval(
    grader_model=grading_sampler,
    n_repeats=3,  # Run each sample 3 times
)
```

### **4. Evaluate Physician Completions:**

```python
eval_obj = HealthBenchEval(
    grader_model=grading_sampler,
    physician_completions_mode="Group 1",  # or "Group 2", "Group 3"
    run_reference_completions=False,
)
```

---

## ⚠️ **Common Issues & Solutions**

### **Issue 1: API Rate Limits**
**Solution:** Reduce `n_threads`:
```python
eval_obj = HealthBenchEval(grader_model=grader, n_threads=5)
```

### **Issue 2: Import Errors**
**Solution:** Make sure your project structure matches exactly:
```
evals/__init__.py  # Must exist!
evals/samplers/__init__.py  # Must exist!
```

### **Issue 3: "types.py conflicts with standard library"**
**Solution:** Rename to `eval_types.py` and update all imports

### **Issue 4: Missing Data Files**
**Solution:** Data is fetched from URL automatically via `blobfile`

---

## 📚 **Key Files Explained**

### **1. `types.py`**
Defines base classes:
- `SamplerBase`: Interface for any LLM
- `Eval`: Interface for any evaluation
- `EvalResult`: Results container
- `SingleEvalResult`: Single sample result

### **2. `common.py`**
Utility functions:
- `map_with_progress()`: Parallel processing
- `aggregate_results()`: Metrics aggregation
- `make_report()`: HTML report generation

### **3. `healthbench_eval.py`**
Main evaluation:
- `HealthBenchEval`: Main evaluation class
- `RubricItem`: Rubric criterion class
- `calculate_score()`: Scoring logic
- `GRADER_TEMPLATE`: LLM grading prompt

### **4. `healthbench_meta_eval.py`**
Meta-evaluation:
- `HealthBenchMetaEval`: Evaluates the evaluator
- Computes agreement metrics with physicians
- Calculates precision, recall, F1

---

## 🎯 **Quick Start Checklist**

- [ ] Install dependencies (`pip install openai blobfile pandas numpy jinja2 tqdm`)
- [ ] Create `evals/` directory structure
- [ ] Copy 5 core files (types, common, healthbench_eval, meta_eval, sampler)
- [ ] Create `__init__.py` files in `evals/` and `evals/samplers/`
- [ ] Fix import paths in copied files
- [ ] Set `OPENAI_API_KEY` environment variable
- [ ] Create `run_healthbench.py` runner script
- [ ] Test with debug mode: `python run_healthbench.py --debug`
- [ ] Run full evaluation: `python run_healthbench.py --model gpt-4o`

---

## 💡 **Tips for Success**

1. **Start Small**: Use `--debug` flag to test with 5 examples first
2. **Monitor Costs**: HealthBench uses GPT-4.1 as grader (expensive)
3. **Check Logs**: Watch for API errors or rate limits
4. **Save Results**: HTML reports are very useful for understanding failures
5. **Compare Models**: Run same eval on multiple models to compare

---

## 🔗 **Resources**

- **Original Paper**: [OpenAI HealthBench Blog Post](https://openai.com/index/healthbench)
- **Dataset**: Loaded automatically from Azure blob storage
- **License**: MIT License

---

## ✅ **Verification**

After integration, verify everything works:

```python
# Quick test script
from evals.healthbench_eval import RubricItem, calculate_score

# Test scoring
rubric_items = [
    RubricItem(criterion="test1", points=10, tags=[]),
    RubricItem(criterion="test2", points=5, tags=[]),
]
grading = [{"criteria_met": True}, {"criteria_met": False}]
score = calculate_score(rubric_items, grading)
print(f"Test score: {score}")  # Should print: 0.6666...

print("✅ Integration successful!")
```

---

**Need help? Check the test files for usage examples!**

