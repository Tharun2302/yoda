"""
Runner script for HealthBench evaluation

Usage:
    # Standard evaluation
    python run_healthbench.py --model gpt-4o --mode standard
    
    # Debug mode (5 examples)
    python run_healthbench.py --model gpt-4o --mode standard --debug
    
    # Meta-evaluation
    python run_healthbench.py --model gpt-4.1-2025-04-14 --mode meta
"""
import os
import sys
from datetime import datetime
from pathlib import Path
import json

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent))

from healthbench_eval import HealthBenchEval
from healthbench_meta_eval import HealthBenchMetaEval
from samplers.chat_completion_sampler import (
    ChatCompletionSampler,
    OPENAI_SYSTEM_MESSAGE_API,
)
from eval_types import SamplerBase
import common


def run_healthbench_standard(model_name="gpt-4o", num_examples=None, subset_name=None):
    """
    Run standard HealthBench evaluation
    
    Args:
        model_name: Model to evaluate (e.g., "gpt-4o", "gpt-3.5-turbo")
        num_examples: Number of examples to evaluate (None = all)
        subset_name: Subset to use (None, "hard", or "consensus")
    """
    print("=" * 70)
    print("🏥 HEALTHBENCH EVALUATION")
    print("=" * 70)
    
    # Set up the grader model (used to grade rubrics)
    print("\n📝 Setting up grader model...")
    grading_sampler = ChatCompletionSampler(
        model="gpt-4.1-2025-04-14",
        system_message=OPENAI_SYSTEM_MESSAGE_API,
        max_tokens=2048,
    )
    
    # Set up the model to be evaluated
    print(f"🤖 Setting up model to evaluate: {model_name}")
    model_sampler = ChatCompletionSampler(
        model=model_name,
        system_message=OPENAI_SYSTEM_MESSAGE_API,
        max_tokens=2048,
    )
    
    # Create the evaluation
    subset_str = f" ({subset_name} subset)" if subset_name else ""
    print(f"\n⚙️  Creating HealthBench evaluation{subset_str}...")
    eval_obj = HealthBenchEval(
        grader_model=grading_sampler,
        num_examples=num_examples,
        n_repeats=1,
        n_threads=120,  # Adjust if you hit rate limits
        subset_name=subset_name,
    )
    
    # Run the evaluation
    num_str = f"{num_examples} examples" if num_examples else "all examples"
    print(f"\n🚀 Running evaluation on {num_str}...")
    print("⏳ This may take a while...")
    result = eval_obj(model_sampler)
    
    # Save results
    now = datetime.now()
    date_str = now.strftime("%Y%m%d_%H%M%S")
    
    # Create output directory
    output_dir = Path("healthbench_results")
    output_dir.mkdir(exist_ok=True)
    
    # Save HTML report
    subset_suffix = f"_{subset_name}" if subset_name else ""
    report_filename = output_dir / f"healthbench{subset_suffix}_{model_name}_{date_str}.html"
    report_filename.write_text(common.make_report(result))
    print(f"\n✅ HTML report saved to: {report_filename}")
    
    # Save metrics JSON
    metrics = result.metrics | {"score": result.score}
    metrics = dict(sorted(metrics.items()))
    result_filename = output_dir / f"healthbench{subset_suffix}_{model_name}_{date_str}.json"
    result_filename.write_text(json.dumps(metrics, indent=2))
    print(f"✅ Metrics saved to: {result_filename}")
    
    # Save full results (including conversations and metadata)
    full_result_dict = {
        "score": result.score,
        "metrics": result.metrics,
        "htmls": result.htmls,
        "convos": result.convos,
        "metadata": result.metadata,
    }
    full_result_filename = output_dir / f"healthbench{subset_suffix}_{model_name}_{date_str}_full.json"
    full_result_filename.write_text(json.dumps(full_result_dict, indent=2))
    print(f"✅ Full results saved to: {full_result_filename}")
    
    # Print results
    print("\n" + "=" * 70)
    print(f"📊 RESULTS FOR {model_name.upper()}")
    print("=" * 70)
    print(f"\n🎯 Overall Score: {result.score:.4f}")
    print("\nDetailed Metrics:")
    for key, value in sorted(metrics.items()):
        if key != "score":
            print(f"  • {key}: {value:.4f}" if isinstance(value, float) else f"  • {key}: {value}")
    print("\n" + "=" * 70)
    
    return result


def run_healthbench_meta(model_name="gpt-4o", num_examples=None):
    """
    Run HealthBench meta-evaluation (evaluates the evaluator)
    
    This measures how well a model performs as a grader by comparing
    its judgments to physician opinions.
    
    Args:
        model_name: Model to use as grader
        num_examples: Number of examples to evaluate (None = all)
    """
    print("=" * 70)
    print("🔬 HEALTHBENCH META-EVALUATION")
    print("=" * 70)
    
    print(f"\n🤖 Setting up grader model: {model_name}")
    grading_sampler = ChatCompletionSampler(
        model=model_name,
        system_message=OPENAI_SYSTEM_MESSAGE_API,
        max_tokens=2048,
    )
    
    print("\n⚙️  Creating meta-evaluation...")
    eval_obj = HealthBenchMetaEval(
        grader_model=grading_sampler,
        num_examples=num_examples,
        n_repeats=1,
        n_threads=120,
    )
    
    # Create a dummy sampler (the model being tested is the grader itself)
    dummy_sampler = grading_sampler
    
    num_str = f"{num_examples} examples" if num_examples else "all examples"
    print(f"\n🚀 Running meta-evaluation on {num_str}...")
    print("⏳ This may take a while...")
    result = eval_obj(dummy_sampler)
    
    # Save results
    now = datetime.now()
    date_str = now.strftime("%Y%m%d_%H%M%S")
    
    output_dir = Path("healthbench_results")
    output_dir.mkdir(exist_ok=True)
    
    report_filename = output_dir / f"healthbench_meta_{model_name}_{date_str}.html"
    report_filename.write_text(common.make_report(result))
    print(f"\n✅ HTML report saved to: {report_filename}")
    
    metrics = result.metrics | {"score": result.score}
    result_filename = output_dir / f"healthbench_meta_{model_name}_{date_str}.json"
    result_filename.write_text(json.dumps(metrics, indent=2))
    print(f"✅ Metrics saved to: {result_filename}")
    
    # Print results
    print("\n" + "=" * 70)
    print(f"📊 META-EVALUATION RESULTS FOR {model_name.upper()}")
    print("=" * 70)
    print(f"\n🎯 Balanced F1 Score: {result.score:.4f}")
    print("\nKey Metrics:")
    # Print most important meta metrics
    important_metrics = [
        "pairwise_model_precision_balanced",
        "pairwise_model_recall_balanced",
        "pairwise_model_f1_balanced",
    ]
    for key in important_metrics:
        if key in metrics:
            print(f"  • {key}: {metrics[key]:.4f}")
    print("\n" + "=" * 70)
    
    return result


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run HealthBench Evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Evaluate GPT-4o
  python run_healthbench.py --model gpt-4o
  
  # Debug mode (5 examples)
  python run_healthbench.py --model gpt-4o --debug
  
  # Hard subset
  python run_healthbench.py --model gpt-4o --subset hard
  
  # Meta-evaluation
  python run_healthbench.py --model gpt-4.1-2025-04-14 --mode meta
        """
    )
    
    parser.add_argument(
        "--model", 
        type=str, 
        default="gpt-4o", 
        help="Model to evaluate (default: gpt-4o)"
    )
    
    parser.add_argument(
        "--mode", 
        type=str, 
        choices=["standard", "meta"], 
        default="standard",
        help="Evaluation mode: 'standard' for normal eval, 'meta' for grader evaluation"
    )
    
    parser.add_argument(
        "--subset",
        type=str,
        choices=["hard", "consensus"],
        default=None,
        help="Dataset subset (only for standard mode)"
    )
    
    parser.add_argument(
        "--examples", 
        type=int, 
        default=None,
        help="Number of examples to evaluate (default: all)"
    )
    
    parser.add_argument(
        "--debug", 
        action="store_true",
        help="Debug mode: evaluate only 5 examples"
    )
    
    args = parser.parse_args()
    
    # Check for API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("\n❌ ERROR: OPENAI_API_KEY environment variable not set!")
        print("\nPlease set it:")
        print("  Windows PowerShell: $env:OPENAI_API_KEY = 'your-key'")
        print("  Linux/Mac: export OPENAI_API_KEY='your-key'")
        sys.exit(1)
    
    num_examples = 5 if args.debug else args.examples
    
    try:
        if args.mode == "standard":
            run_healthbench_standard(args.model, num_examples, args.subset)
        else:
            if args.subset:
                print("\n⚠️  Warning: --subset is ignored in meta mode")
            run_healthbench_meta(args.model, num_examples)
            
        print("\n✨ Evaluation complete!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Evaluation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error during evaluation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

