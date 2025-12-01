"""Quick test to verify app startup"""
import sys
print("Testing app imports...")

try:
    # This is exactly how app.py imports the modules
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / 'simple-evals'))
    
    from custom_evaluations.live_evaluator import get_live_evaluator
    from custom_evaluations.langfuse_scorer import create_langfuse_scorer
    
    print("[OK] Evaluation modules imported successfully!")
    print("[OK] Your setup is working!")
    
except Exception as e:
    print(f"[FAIL] Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

