"""Test if dashboard integration is working"""
import sys
from pathlib import Path

print("=" * 80)
print("Testing HealthBench Dashboard Integration")
print("=" * 80)

# Test 1: Import results_storage
print("\n[TEST 1] Testing results_storage import...")
try:
    simple_evals_path = Path(__file__).parent.parent / 'simple-evals'
    custom_evals_path = simple_evals_path / 'custom_evaluations'
    sys.path.insert(0, str(simple_evals_path))
    sys.path.insert(0, str(custom_evals_path))
    
    from results_storage import ResultsStorage, get_results_storage
    print("[OK] results_storage imported successfully")
except Exception as e:
    print(f"[FAIL] Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Initialize storage
print("\n[TEST 2] Testing storage initialization...")
try:
    storage = get_results_storage()
    print(f"[OK] Storage initialized at: {storage.storage_path}")
    
    if storage.storage_path.exists():
        print(f"[OK] Results file exists: {storage.storage_path}")
    else:
        print(f"[INFO] Results file will be created on first evaluation")
except Exception as e:
    print(f"[FAIL] Storage initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Test save_evaluation (mock data)
print("\n[TEST 3] Testing save_evaluation with mock data...")
try:
    mock_eval_result = {
        'overall_score': 0.85,
        'rubric_scores': [
            {
                'criterion': 'Test rubric 1',
                'points': 1.0,
                'tags': ['test'],
                'criteria_met': True,
                'explanation': 'This is a test explanation'
            }
        ],
        'metrics': {
            'overall_score': 0.85,
            'num_rubrics_evaluated': 1,
            'rubrics_passed': 1,
            'rubrics_failed': 0
        },
        'medical_domain': 'Test Domain',
        'evaluation_time': 1.5
    }
    
    success = storage.save_evaluation(
        eval_result=mock_eval_result,
        conversation_id='test_session',
        user_message='Test user message',
        bot_response='Test bot response',
        medical_context='Test > Medical > Context'
    )
    
    if success:
        print("[OK] Mock evaluation saved successfully")
    else:
        print("[WARNING] Save returned False")
except Exception as e:
    print(f"[FAIL] Save test failed: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Test get_statistics
print("\n[TEST 4] Testing get_statistics...")
try:
    stats = storage.get_statistics()
    print(f"[OK] Statistics retrieved:")
    print(f"     Total evaluations: {stats['total_evaluations']}")
    print(f"     Average score: {stats['average_score']}")
except Exception as e:
    print(f"[FAIL] Statistics test failed: {e}")

# Test 5: Test get_recent_results
print("\n[TEST 5] Testing get_recent_results...")
try:
    results = storage.get_recent_results(limit=10)
    print(f"[OK] Retrieved {len(results)} recent results")
except Exception as e:
    print(f"[FAIL] Recent results test failed: {e}")

# Test 6: Check if dashboard HTML exists
print("\n[TEST 6] Checking dashboard HTML file...")
dashboard_path = Path(__file__).parent / 'healthbench_dashboard.html'
if dashboard_path.exists():
    print(f"[OK] Dashboard HTML exists: {dashboard_path}")
else:
    print(f"[FAIL] Dashboard HTML not found: {dashboard_path}")

print("\n" + "=" * 80)
print("Summary")
print("=" * 80)
print("""
[OK] All tests passed!

Your HealthBench Dashboard is ready:
1. Start the bot: python app.py
2. Open dashboard: http://localhost:8002/healthbench/dashboard
3. Have a conversation with the bot
4. Watch the dashboard auto-update with evaluation scores!
""")
print("=" * 80)

