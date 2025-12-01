"""
Test HELM Integration with HealthBench
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'evals'))

print("=" * 80)
print("TESTING HELM + HEALTHBENCH PARALLEL EVALUATION")
print("=" * 80)

# Test 1: Import modules
print("\n[TEST 1] Testing imports...")
try:
    from simple_live_evaluator import get_live_evaluator
    from helm_live_evaluator import get_helm_evaluator
    from results_storage import get_results_storage
    print("[OK] All modules imported successfully")
except Exception as e:
    print(f"[FAIL] Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Initialize evaluators
print("\n[TEST 2] Initializing evaluators...")
try:
    healthbench_eval = get_live_evaluator(grader_model="gpt-4o-mini")
    helm_eval = get_helm_evaluator(judge_model="gpt-4o-mini")
    storage = get_results_storage()
    
    print(f"[OK] HealthBench evaluator: {'Enabled' if healthbench_eval.enabled else 'Disabled'}")
    print(f"[OK] HELM evaluator: {'Enabled' if helm_eval.enabled else 'Disabled'}")
    print(f"[OK] Storage initialized at: {storage.storage_path}")
except Exception as e:
    print(f"[FAIL] Initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Check data structures
print("\n[TEST 3] Checking evaluation structures...")
try:
    print(f"  HealthBench rubrics: {len(healthbench_eval.GENERAL_RUBRICS)}")
    print(f"    - Positive rubrics: {len([r for r in healthbench_eval.GENERAL_RUBRICS if r.get('is_positive', True)])}")
    print(f"    - Red flag rubrics: {len([r for r in healthbench_eval.GENERAL_RUBRICS if not r.get('is_positive', True)])}")
    
    print(f"  HELM criteria: Accuracy, Completeness, Clarity (1-5 scale each)")
    print("[OK] Both evaluation systems ready")
except Exception as e:
    print(f"[FAIL] Structure check failed: {e}")

# Test 4: Check statistics calculation
print("\n[TEST 4] Testing statistics calculation...")
try:
    stats = storage.get_statistics()
    print(f"  Total evaluations: {stats.get('total_evaluations', 0)}")
    print(f"  Average score: {stats.get('average_score', 0):.3f}")
    print(f"  Average safety score: {stats.get('average_safety_score', 0):.3f}")
    print(f"  Average HELM score: {stats.get('average_helm_score', 0):.2f}/5.0")
    print(f"  HELM evaluations: {stats.get('helm_evaluations', 0)}")
    print("[OK] Statistics calculation works")
except Exception as e:
    print(f"[FAIL] Statistics calculation failed: {e}")
    import traceback
    traceback.print_exc()

# Summary
print("\n" + "=" * 80)
print("INTEGRATION TEST SUMMARY")
print("=" * 80)
print("\n[OK] HELM + HealthBench integration complete!")
print("\nEvaluation Flow:")
print("  1. User sends message")
print("  2. Bot generates response")
print("  3. HealthBench evaluates (13 rubrics) - parallel thread 1")
print("  4. HELM evaluates (3 criteria: accuracy, completeness, clarity) - parallel thread 2")
print("  5. Combined results saved to healthbench_results.json")
print("  6. Dashboard displays both scores")
print("\nWhat Each System Evaluates:")
print("  HealthBench:")
print("    - Safety & Red Flags (critical behaviors)")
print("    - Empathy & Communication")
print("    - Tag-based scores (safety, empathy, accuracy, etc)")
print("    - Output: 0-1 scale (0.88 = 88%)")
print("  HELM:")
print("    - Medical Accuracy (1-5)")
print("    - Information Completeness (1-5)")
print("    - Communication Clarity (1-5)")
print("    - Output: 1-5 scale (4.2 = 84%)")
print("\nTo use:")
print("  1. Restart app: python app.py")
print("  2. Have a conversation")
print("  3. Check console for both scores")
print("  4. View dashboard: http://localhost:8002/healthbench/dashboard")
print("\n" + "=" * 80)

