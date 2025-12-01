"""
Fix old scores in healthbench_results.json
Recalculates overall_score with the corrected formula
"""
import json
from pathlib import Path

def calculate_correct_score(rubric_scores):
    """Calculate score correctly"""
    if not rubric_scores:
        return 0.0
    
    total_points = sum(abs(r['points']) for r in rubric_scores)
    earned_points = 0
    
    for r in rubric_scores:
        is_positive = r.get('is_positive', True)
        criteria_met = r['criteria_met']
        
        if is_positive:
            if criteria_met:
                earned_points += abs(r['points'])
        else:
            if not criteria_met:
                earned_points += abs(r['points'])
    
    return earned_points / total_points if total_points > 0 else 0.0

# Load data
results_file = Path("healthbench_results.json")
with open(results_file, 'r') as f:
    data = json.load(f)

print("=" * 80)
print("FIXING OLD SCORES")
print("=" * 80)

evaluations = data.get('evaluations', [])
print(f"\nTotal evaluations to fix: {len(evaluations)}")

fixed_count = 0

for eval_record in evaluations:
    eval_data = eval_record.get('evaluation', {})
    rubric_scores = eval_data.get('rubric_scores', [])
    
    if not rubric_scores:
        continue
    
    # Calculate correct score
    old_score = eval_data.get('overall_score', 0)
    new_score = calculate_correct_score(rubric_scores)
    
    # Update if different
    if abs(old_score - new_score) > 0.001:
        eval_data['overall_score'] = new_score
        eval_data['metrics']['overall_score'] = new_score
        fixed_count += 1
        print(f"Fixed: {eval_record['id'][:30]}... {old_score:.3f} -> {new_score:.3f}")

# Save updated data
if fixed_count > 0:
    with open(results_file, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"\n[OK] Fixed {fixed_count} evaluations and saved to {results_file}")
else:
    print(f"\n[INFO] No evaluations needed fixing")

print("\n" + "=" * 80)
print("DONE! All scores recalculated.")
print("Restart your app and refresh the dashboard to see correct scores!")
print("=" * 80)

