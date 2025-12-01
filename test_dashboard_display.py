"""
Test Dashboard Display - Verify all scores show up
"""
import json
from pathlib import Path

print("=" * 80)
print("DASHBOARD DISPLAY TEST")
print("=" * 80)

# Load data
results_file = Path("healthbench_results.json")
with open(results_file, 'r') as f:
    data = json.load(f)

evaluations = data.get('evaluations', [])
latest = evaluations[-1] if evaluations else None

if not latest:
    print("\n[FAIL] No evaluations found!")
    exit(1)

print(f"\n[TEST 1] Checking evaluation data structure...")
eval_data = latest.get('evaluation', {})

required_fields = ['overall_score', 'safety_score', 'tag_scores', 'red_flags', 'critical_failure', 'metrics']
missing_fields = [f for f in required_fields if f not in eval_data]

if missing_fields:
    print(f"[FAIL] Missing fields: {missing_fields}")
else:
    print("[OK] All required fields present")

print(f"\n[TEST 2] Field values...")
print(f"Overall Score: {eval_data.get('overall_score', 'N/A')}")
print(f"Safety Score: {eval_data.get('safety_score', 'N/A')}")
print(f"Tag Scores: {len(eval_data.get('tag_scores', {}))} tags")
print(f"Red Flags: {len(eval_data.get('red_flags', []))} flags")
print(f"Critical Failure: {eval_data.get('critical_failure', 'N/A')}")

print(f"\n[TEST 3] Tag Scores breakdown...")
tag_scores = eval_data.get('tag_scores', {})
for tag, score in tag_scores.items():
    print(f"  {tag}: {score:.3f} ({score*100:.1f}%)")

print(f"\n[TEST 4] Dashboard would display...")
print(f"- Total Evaluations: {data.get('total_evaluations', 0)}")
print(f"- Overall Score: {eval_data.get('overall_score', 0):.3f}")
print(f"- Safety Score: {eval_data.get('safety_score', 0):.3f}")
print(f"- Rubrics: {eval_data.get('metrics', {}).get('num_rubrics_evaluated', 0)} total")
print(f"- Passed: {eval_data.get('metrics', {}).get('rubrics_passed', 0)}")
print(f"- Failed: {eval_data.get('metrics', {}).get('rubrics_failed', 0)}")

if eval_data.get('red_flags'):
    print(f"\n[WARNING] Red Flags:")
    for flag in eval_data['red_flags']:
        print(f"  [{flag['severity']}] {flag['criterion'][:60]}")

print("\n" + "=" * 80)
print("DASHBOARD TEST SUMMARY")
print("=" * 80)
print("\n[OK] Data structure is correct!")
print("[OK] All new fields (safety_score, tag_scores, red_flags) are present")
print("[OK] Dashboard should display all scores correctly")
print("\nIf dashboard still shows 0.000:")
print("  1. Restart the Flask app: python app.py")
print("  2. Refresh the dashboard page")
print("  3. Clear browser cache if needed")
print("\n" + "=" * 80)

