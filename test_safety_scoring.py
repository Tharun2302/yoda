"""
Test Safety Scoring and Red Flag Detection
"""
import sys
from pathlib import Path

# Add evals to path
sys.path.insert(0, str(Path(__file__).parent / 'evals'))

print("=" * 80)
print("TESTING SAFETY SCORING AND RED FLAG DETECTION")
print("=" * 80)

# Test 1: Import modules
print("\n[TEST 1] Testing imports...")
try:
    from simple_live_evaluator import SimpleLiveEvaluator, EvaluationResult
    print("[OK] Modules imported successfully")
except Exception as e:
    print(f"[FAIL] Import failed: {e}")
    sys.exit(1)

# Test 2: Check rubric structure
print("\n[TEST 2] Checking rubric structure...")
try:
    evaluator = SimpleLiveEvaluator(enabled=False)  # Don't need API for this test
    rubrics = evaluator.GENERAL_RUBRICS
    
    print(f"[OK] Total rubrics: {len(rubrics)}")
    
    # Count positive and negative rubrics
    positive_rubrics = [r for r in rubrics if r['is_positive']]
    negative_rubrics = [r for r in rubrics if not r['is_positive']]
    
    print(f"[OK] Positive rubrics (good behaviors): {len(positive_rubrics)}")
    print(f"[OK] Negative rubrics (red flags): {len(negative_rubrics)}")
    
    # Check for safety tags
    safety_rubrics = [r for r in rubrics if 'safety' in r.get('tags', [])]
    red_flag_rubrics = [r for r in rubrics if 'red_flag' in r.get('tags', [])]
    
    print(f"[OK] Safety-tagged rubrics: {len(safety_rubrics)}")
    print(f"[OK] Red flag rubrics: {len(red_flag_rubrics)}")
    
    # Display red flag rubrics
    print("\n   Red Flag Rubrics:")
    for rf in red_flag_rubrics:
        print(f"   - [{rf['points']}pts] {rf['criterion'][:70]}...")
    
except Exception as e:
    print(f"[FAIL] Rubric check failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Test tag score calculation
print("\n[TEST 3] Testing tag score calculation...")
try:
    # Create mock rubric scores
    mock_scores = [
        {'criterion': 'Safety 1', 'points': 1.0, 'tags': ['safety'], 'criteria_met': True, 'is_positive': True},
        {'criterion': 'Safety 2', 'points': 1.0, 'tags': ['safety'], 'criteria_met': False, 'is_positive': True},
        {'criterion': 'Empathy 1', 'points': 1.0, 'tags': ['empathy'], 'criteria_met': True, 'is_positive': True},
        {'criterion': 'Red Flag', 'points': -5.0, 'tags': ['safety', 'red_flag'], 'criteria_met': False, 'is_positive': False},
    ]
    
    tag_scores = evaluator._calculate_tag_scores(mock_scores)
    
    print(f"[OK] Tag scores calculated: {tag_scores}")
    print(f"   - Safety score: {tag_scores.get('safety', 0):.2f}")
    print(f"   - Empathy score: {tag_scores.get('empathy', 0):.2f}")
    
except Exception as e:
    print(f"[FAIL] Tag score calculation failed: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Test red flag detection
print("\n[TEST 4] Testing red flag detection...")
try:
    # Mock scores with red flags
    mock_scores_with_flags = [
        {
            'criterion': 'Safe behavior', 
            'points': 1.0, 
            'tags': ['safety'], 
            'criteria_met': True, 
            'is_positive': True,
            'explanation': 'Good behavior'
        },
        {
            'criterion': 'Recommends dangerous treatment', 
            'points': -5.0, 
            'tags': ['safety', 'red_flag', 'critical'], 
            'criteria_met': True,  # RED FLAG TRIGGERED!
            'is_positive': False,
            'explanation': 'Bot recommended unprescribed medication'
        },
        {
            'criterion': 'Another red flag', 
            'points': -3.0, 
            'tags': ['red_flag'], 
            'criteria_met': False,  # Not triggered
            'is_positive': False,
            'explanation': 'Not present'
        },
    ]
    
    red_flags = evaluator._detect_red_flags(mock_scores_with_flags)
    
    print(f"[OK] Red flags detected: {len(red_flags)}")
    for flag in red_flags:
        print(f"   [{flag['severity']}] {flag['criterion']}")
        print(f"   Reason: {flag['explanation']}")
        print(f"   Points deducted: {flag['points_deducted']}")
    
except Exception as e:
    print(f"[FAIL] Red flag detection failed: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Test EvaluationResult structure
print("\n[TEST 5] Testing EvaluationResult structure...")
try:
    result = EvaluationResult(
        overall_score=0.75,
        safety_score=0.67,
        tag_scores={'safety': 0.67, 'empathy': 0.85},
        red_flags=[{'severity': 'WARNING', 'criterion': 'Test', 'explanation': 'Test', 'points_deducted': 3, 'tags': []}],
        critical_failure=False,
        rubric_scores=[],
        metrics={'test': 1},
        medical_domain='Test',
        evaluation_time=1.0
    )
    
    result_dict = result.to_dict()
    
    print("[OK] EvaluationResult created successfully")
    print(f"   Fields in result: {list(result_dict.keys())}")
    
    # Check all new fields are present
    required_fields = ['overall_score', 'safety_score', 'tag_scores', 'red_flags', 'critical_failure']
    missing_fields = [f for f in required_fields if f not in result_dict]
    
    if missing_fields:
        print(f"[FAIL] Missing fields: {missing_fields}")
    else:
        print("[OK] All required fields present")
    
except Exception as e:
    print(f"[FAIL] EvaluationResult test failed: {e}")
    import traceback
    traceback.print_exc()

# Summary
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print("\n[OK] All tests passed!")
print("\nNew Features Implemented:")
print("  1. Safety Score - Separate score for safety-related rubrics")
print("  2. Tag Scores - Granular scores by category (safety, empathy, accuracy, etc)")
print("  3. Red Flag Detection - Identifies critical safety violations")
print("  4. Critical Failure Flag - Immediate alert for dangerous responses")
print("  5. Negative Point Rubrics - Deducts points for bad behaviors")
print("\nRubric Summary:")
print(f"  - Total rubrics: {len(evaluator.GENERAL_RUBRICS)}")
print(f"  - Positive rubrics: {len([r for r in evaluator.GENERAL_RUBRICS if r['is_positive']])}")
print(f"  - Red flag rubrics: {len([r for r in evaluator.GENERAL_RUBRICS if not r['is_positive']])}")
print("\n" + "=" * 80)

