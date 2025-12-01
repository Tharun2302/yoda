"""Check what data is in healthbench_results.json"""
import json
from pathlib import Path

results_file = Path("healthbench_results.json")

if not results_file.exists():
    print("healthbench_results.json not found!")
    exit(1)

with open(results_file, 'r') as f:
    data = json.load(f)

print("=" * 80)
print("HEALTHBENCH RESULTS DATA CHECK")
print("=" * 80)

print(f"\nTotal Evaluations: {data.get('total_evaluations', 0)}")
print(f"Number of evaluation records: {len(data.get('evaluations', []))}")

if data.get('evaluations'):
    latest = data['evaluations'][-1]
    print("\n--- LATEST EVALUATION ---")
    print(f"Timestamp: {latest.get('timestamp', 'N/A')}")
    print(f"User: {latest.get('user_message', 'N/A')[:50]}...")
    print(f"Bot: {latest.get('bot_response', 'N/A')[:50]}...")
    
    eval_data = latest.get('evaluation', {})
    print(f"\n--- SCORES ---")
    print(f"Overall Score: {eval_data.get('overall_score', 'NOT FOUND')}")
    print(f"Safety Score: {eval_data.get('safety_score', 'NOT FOUND')}")
    
    print(f"\n--- TAG SCORES ---")
    tag_scores = eval_data.get('tag_scores', {})
    if tag_scores:
        for tag, score in tag_scores.items():
            print(f"  {tag}: {score:.3f}")
    else:
        print("  NOT FOUND")
    
    print(f"\n--- RED FLAGS ---")
    red_flags = eval_data.get('red_flags', [])
    print(f"Count: {len(red_flags)}")
    if red_flags:
        for flag in red_flags:
            print(f"  [{flag.get('severity', 'N/A')}] {flag.get('criterion', 'N/A')[:60]}...")
    
    print(f"\n--- METRICS ---")
    metrics = eval_data.get('metrics', {})
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    
    print(f"\n--- EVALUATION FIELDS ---")
    print(f"Fields in evaluation: {list(eval_data.keys())}")

print("\n" + "=" * 80)

