"""
Deep verification of evaluation accuracy
Checks if LLM grader is making accurate judgments
"""
import json
from pathlib import Path

# Load recent evaluations
with open('healthbench_results.json', 'r') as f:
    data = json.load(f)

print("=" * 80)
print("DEEP ACCURACY VERIFICATION")
print("=" * 80)

# Analyze last 5 evaluations
recent = data['evaluations'][-5:]

print(f"\nAnalyzing {len(recent)} recent evaluations...\n")

for i, eval_record in enumerate(recent, 1):
    user_msg = eval_record['user_message']
    bot_response = eval_record['bot_response']
    rubric_scores = eval_record['evaluation']['rubric_scores']
    
    print(f"--- EVALUATION {i} ---")
    print(f"User: {user_msg[:50]}...")
    print(f"Bot: {bot_response[:80]}...")
    
    # Check empathy rubric specifically
    empathy_rubric = next((r for r in rubric_scores if 'empathy' in r.get('tags', [])), None)
    if empathy_rubric:
        print(f"\nEmpathy Rubric:")
        print(f"  Passed: {empathy_rubric['criteria_met']}")
        print(f"  Reason: {empathy_rubric['explanation'][:100]}...")
        
        # Manually check if this seems accurate
        bot_lower = bot_response.lower()
        empathy_words = ['sorry', 'understand', 'hear that', 'concerned']
        has_empathy = any(word in bot_lower for word in empathy_words)
        
        if has_empathy and not empathy_rubric['criteria_met']:
            print(f"  [CONCERN] Bot shows empathy words but rubric says NO empathy")
        elif not has_empathy and empathy_rubric['criteria_met']:
            print(f"  [CONCERN] Bot has no empathy words but rubric says HAS empathy")
        else:
            print(f"  [OK] Evaluation seems accurate")
    
    # Check safety rubrics
    safety_rubrics = [r for r in rubric_scores if 'safety' in r.get('tags', [])]
    safety_passed = sum(1 for r in safety_rubrics if r['criteria_met'] == r.get('is_positive', True))
    print(f"\nSafety Rubrics: {safety_passed}/{len(safety_rubrics)} passed")
    
    # Check for concerning patterns
    bot_lower = bot_response.lower()
    concerns = []
    
    if 'take' in bot_lower and ('medication' in bot_lower or 'mg' in bot_lower):
        concerns.append("Bot might be recommending specific medication")
    if 'definitely' in bot_lower or 'you have' in bot_lower:
        concerns.append("Bot might be making diagnosis")
    if "don't need" in bot_lower or "don't worry" in bot_lower:
        concerns.append("Bot might be dismissing symptoms")
    
    if concerns:
        print(f"\n  [CONCERNS DETECTED]:")
        for concern in concerns:
            print(f"    - {concern}")
    
    print()

print("=" * 80)
print("ACCURACY ANALYSIS SUMMARY")
print("=" * 80)

# Calculate average scores across evaluations
all_scores = [e['evaluation']['overall_score'] for e in recent]
all_safety_scores = [e['evaluation'].get('safety_score', 0) for e in recent]

print(f"\nAverage Overall Score: {sum(all_scores)/len(all_scores):.3f}")
print(f"Average Safety Score: {sum(all_safety_scores)/len(all_safety_scores):.3f}")

# Count specific rubric pass rates
all_rubrics = {}
for eval_record in recent:
    for rubric in eval_record['evaluation']['rubric_scores']:
        criterion = rubric['criterion'][:50]
        if criterion not in all_rubrics:
            all_rubrics[criterion] = {'passed': 0, 'total': 0}
        all_rubrics[criterion]['total'] += 1
        if rubric['criteria_met'] == rubric.get('is_positive', True):
            all_rubrics[criterion]['passed'] += 1

print(f"\nRubric Pass Rates (across {len(recent)} evaluations):")
for criterion, stats in sorted(all_rubrics.items(), key=lambda x: x[1]['passed']/x[1]['total']):
    rate = stats['passed'] / stats['total'] * 100
    print(f"  {rate:5.1f}% - {criterion}...")

print("\n" + "=" * 80)
print("RECOMMENDATIONS")
print("=" * 80)

# Check if scores seem reasonable
avg_overall = sum(all_scores)/len(all_scores)
if avg_overall < 0.5:
    print("\n[CONCERN] Average overall score is low (<50%)")
    print("  Possible causes:")
    print("  - Rubrics are too strict")
    print("  - LLM grader is being too harsh")
    print("  - Bot responses need improvement")
else:
    print(f"\n[OK] Average score of {avg_overall:.1%} seems reasonable")

# Check if safety score is good
avg_safety = sum(all_safety_scores)/len(all_safety_scores)
if avg_safety >= 0.9:
    print(f"[OK] Safety score of {avg_safety:.1%} is excellent")
elif avg_safety >= 0.75:
    print(f"[OK] Safety score of {avg_safety:.1%} is good")
else:
    print(f"[CONCERN] Safety score of {avg_safety:.1%} is concerning")

print("\n" + "=" * 80)

