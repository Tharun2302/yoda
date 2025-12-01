"""
Start HYoda with HealthBench Dashboard
This script properly initializes all paths and starts the server
"""
import sys
from pathlib import Path

# Set up paths BEFORE any imports
current_dir = Path(__file__).parent
simple_evals_path = current_dir.parent / 'simple-evals'
custom_evals_path = simple_evals_path / 'custom_evaluations'

sys.path.insert(0, str(simple_evals_path))
sys.path.insert(0, str(custom_evals_path))

print("=" * 80)
print("Starting HealthYoda with HealthBench Dashboard")
print("=" * 80)

# Verify paths
print(f"\n[CHECK] Simple-evals path: {simple_evals_path}")
print(f"[CHECK] Custom evals path: {custom_evals_path}")
print(f"[CHECK] Simple-evals exists: {simple_evals_path.exists()}")
print(f"[CHECK] Custom evals exists: {custom_evals_path.exists()}")

# Test imports
print("\n[CHECK] Testing imports...")
try:
    from results_storage import ResultsStorage, get_results_storage
    print("[OK] results_storage imported")
except Exception as e:
    print(f"[FAIL] results_storage import failed: {e}")
    print("\nAttempting alternative import...")
    try:
        import results_storage as rs_module
        ResultsStorage = rs_module.ResultsStorage
        get_results_storage = rs_module.get_results_storage
        print("[OK] results_storage imported (alternative method)")
    except Exception as e2:
        print(f"[FAIL] Alternative import also failed: {e2}")
        print("\nDEBUG: Checking if file exists...")
        results_storage_file = custom_evals_path / 'results_storage.py'
        print(f"File exists: {results_storage_file.exists()}")
        if results_storage_file.exists():
            print(f"File path: {results_storage_file}")

# Now start the app
print("\n[START] Launching app.py...")
print("=" * 80)
exec(open('app.py').read())

