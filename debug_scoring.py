"""Debug the scoring calculation"""
import json

with open('healthbench_results.json', 'r') as f:
    data = json.load(f)

latest = data['evaluations'][-1]
rubric_scores = latest['evaluation']['rubric_scores']

print("=" * 80)
print("DEBUGGING SCORE CALCULATION")
print("=" * 80)

print(f"\nTotal Rubrics: {len(rubric_scores)}")

positive_rubrics = [r for r in rubric_scores if r.get('is_positive', True)]
negative_rubrics = [r for r in rubric_scores if not r.get('is_positive', True)]

print(f"Positive Rubrics: {len(positive_rubrics)}")
print(f"Negative Rubrics: {len(negative_rubrics)}")

print("\n--- POSITIVE RUBRICS ---")
for r in positive_rubrics:
    status = "PASS" if r['criteria_met'] else "FAIL"
    print(f"[{status}] {r['criterion'][:60]}... (points: {r['points']})")

print("\n--- NEGATIVE RUBRICS (RED FLAGS) ---")
for r in negative_rubrics:
    # For negative rubrics: criteria_met=False is GOOD (bad behavior not present)
    status = "GOOD" if not r['criteria_met'] else "RED FLAG!"
    print(f"[{status}] {r['criterion'][:60]}... (points: {r['points']})")
    print(f"   criteria_met: {r['criteria_met']} (should be False for safe)")

# Calculate score manually
print("\n--- SCORE CALCULATION ---")
total_points = sum(abs(r['points']) for r in rubric_scores)
print(f"Total possible points (absolute): {total_points}")

earned_points = 0
for r in rubric_scores:
    is_positive = r.get('is_positive', True)
    criteria_met = r['criteria_met']
    
    if is_positive:
        if criteria_met:
            earned_points += abs(r['points'])
            print(f"  + {abs(r['points'])} for {r['criterion'][:40]}...")
    else:
        if not criteria_met:
            earned_points += abs(r['points'])
            print(f"  + {abs(r['points'])} for NOT {r['criterion'][:40]}...")

print(f"\nEarned Points: {earned_points}")
print(f"Total Points: {total_points}")
print(f"Overall Score: {earned_points / total_points if total_points > 0 else 0:.3f}")

stored_score = latest['evaluation']['overall_score']
print(f"\nStored Overall Score: {stored_score}")
print(f"Stored Safety Score: {latest['evaluation']['safety_score']:.3f}")

print("\n" + "=" * 80)

