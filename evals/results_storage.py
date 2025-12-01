"""
Results Storage for HealthBench Evaluations

This module stores evaluation results to a JSON file for the custom dashboard.
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import time


class ResultsStorage:
    """
    Stores HealthBench evaluation results for dashboard display
    """
    
    def __init__(self, storage_path: str = "healthbench_results.json"):
        """
        Initialize the results storage
        
        Args:
            storage_path: Path to JSON file for storing results
        """
        self.storage_path = Path(storage_path)
        self._initialize_storage()
    
    def _initialize_storage(self):
        """Initialize storage file if it doesn't exist"""
        if not self.storage_path.exists():
            initial_data = {
                "created_at": datetime.now().isoformat(),
                "total_evaluations": 0,
                "evaluations": [],
                "metadata": {
                    "last_updated": datetime.now().isoformat()
                }
            }
            self._save_data(initial_data)
            print(f"[RESULTS STORAGE] Created new storage file: {self.storage_path}")
    
    def _load_data(self) -> Dict[str, Any]:
        """Load data from storage file"""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[RESULTS STORAGE] Error loading data: {e}")
            return {
                "created_at": datetime.now().isoformat(),
                "total_evaluations": 0,
                "evaluations": [],
                "metadata": {}
            }
    
    def _save_data(self, data: Dict[str, Any]):
        """Save data to storage file"""
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[RESULTS STORAGE] Error saving data: {e}")
    
    def save_evaluation(
        self,
        eval_result: Dict[str, Any],
        conversation_id: str,
        user_message: str,
        bot_response: str,
        medical_context: Optional[str] = None
    ):
        """
        Save an evaluation result
        
        Args:
            eval_result: Dictionary from EvaluationResult.to_dict()
            conversation_id: Session/conversation ID
            user_message: User's message
            bot_response: Bot's response
            medical_context: Medical domain context
        """
        try:
            # Load current data
            data = self._load_data()
            
            # Create evaluation record
            evaluation_record = {
                "id": f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{int(time.time() * 1000000) % 1000000}",
                "timestamp": datetime.now().isoformat(),
                "conversation_id": conversation_id,
                "user_message": user_message,
                "bot_response": bot_response,
                "medical_context": medical_context,
                "evaluation": eval_result
            }
            
            # Add to evaluations list (keep last 100)
            data["evaluations"].append(evaluation_record)
            if len(data["evaluations"]) > 100:
                data["evaluations"] = data["evaluations"][-100:]
            
            # Update metadata
            data["total_evaluations"] = data.get("total_evaluations", 0) + 1
            data["metadata"]["last_updated"] = datetime.now().isoformat()
            
            # Save
            self._save_data(data)
            
            print(f"[RESULTS STORAGE] ✅ Saved evaluation {evaluation_record['id']}")
            
        except Exception as e:
            print(f"[RESULTS STORAGE] Failed to save evaluation: {e}")
            import traceback
            traceback.print_exc()
    
    def get_recent_evaluations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent evaluations
        
        Args:
            limit: Maximum number of evaluations to return
        
        Returns:
            List of evaluation records
        """
        data = self._load_data()
        evaluations = data.get("evaluations", [])
        return evaluations[-limit:] if evaluations else []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get overall statistics including HELM scores
        
        Returns:
            Dictionary with statistics
        """
        data = self._load_data()
        evaluations = data.get("evaluations", [])
        
        if not evaluations:
            return {
                "total_evaluations": 0,
                "average_score": 0.0,
                "average_safety_score": 0.0,
                "average_helm_score": 0.0
            }
        
        # Calculate statistics
        scores = []
        safety_scores = []
        helm_scores = []
        pass_rates = []
        
        for eval_record in evaluations:
            eval_data = eval_record.get("evaluation", {})
            
            # HealthBench scores
            scores.append(eval_data.get("overall_score", 0.0))
            safety_scores.append(eval_data.get("safety_score", 0.0))
            
            # HELM scores
            helm_data = eval_data.get("helm", {})
            if helm_data:
                helm_scores.append(helm_data.get("overall_helm_score", 0.0))
            
            # Pass rates
            metrics = eval_data.get("metrics", {})
            pass_rates.append(metrics.get("pass_rate", 0.0))
        
        return {
            "total_evaluations": len(evaluations),
            "average_score": sum(scores) / len(scores) if scores else 0.0,
            "average_safety_score": sum(safety_scores) / len(safety_scores) if safety_scores else 0.0,
            "average_helm_score": sum(helm_scores) / len(helm_scores) if helm_scores else 0.0,
            "average_pass_rate": sum(pass_rates) / len(pass_rates) if pass_rates else 0.0,
            "min_score": min(scores) if scores else 0.0,
            "max_score": max(scores) if scores else 0.0,
            "highest_score": max(scores) if scores else 0.0,
            "lowest_score": min(scores) if scores else 0.0,
            "helm_evaluations": len(helm_scores)
        }


# Singleton instance
_storage_instance = None


def get_results_storage(storage_path: str = "healthbench_results.json") -> ResultsStorage:
    """
    Get or create the results storage instance
    
    Args:
        storage_path: Path to JSON file
    
    Returns:
        ResultsStorage instance
    """
    global _storage_instance
    
    if _storage_instance is None:
        _storage_instance = ResultsStorage(storage_path=storage_path)
    
    return _storage_instance


if __name__ == "__main__":
    # Test the storage
    print("Testing Results Storage...")
    
    storage = get_results_storage("test_healthbench_results.json")
    
    # Test save
    test_eval = {
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
    
    storage.save_evaluation(
        eval_result=test_eval,
        conversation_id="test_session",
        user_message="Test user message",
        bot_response="Test bot response",
        medical_context="Test > Medical > Context"
    )
    
    # Test retrieval
    recent = storage.get_recent_evaluations(5)
    print(f"✅ Saved and retrieved {len(recent)} evaluations")
    
    # Test statistics
    stats = storage.get_statistics()
    print(f"✅ Statistics: {stats}")
    
    print("\n✅ Results Storage working correctly!")

