"""
Live HealthBench Evaluator for Real-Time Chatbot Evaluation

This module provides real-time evaluation of chatbot responses using HealthBench rubrics.
It automatically evaluates every bot response against medical best practices.
"""
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json
import time

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir.parent))

# Try importing as package first, fall back to direct import
try:
    from evals.healthbench_eval import HealthBenchEval
    from evals.samplers.chat_completion_sampler import ChatCompletionSampler, OPENAI_SYSTEM_MESSAGE_API
    from evals.eval_types import SamplerBase
except ImportError:
    try:
        import healthbench_eval
        from samplers.chat_completion_sampler import ChatCompletionSampler, OPENAI_SYSTEM_MESSAGE_API
        from eval_types import SamplerBase
        # Manually fix relative imports in healthbench_eval
        import common
        import eval_types
        healthbench_eval.common = common
        healthbench_eval.eval_types = eval_types
        HealthBenchEval = healthbench_eval.HealthBenchEval
    except Exception as e:
        print(f"Failed to import healthbench_eval: {e}")
        raise


@dataclass
class EvaluationResult:
    """Results from a live evaluation"""
    overall_score: float
    rubric_scores: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    medical_domain: Optional[str] = None
    evaluation_time: float = 0.0
    
    def to_dict(self):
        """Convert to dictionary for serialization"""
        return {
            'overall_score': self.overall_score,
            'rubric_scores': self.rubric_scores,
            'metrics': self.metrics,
            'medical_domain': self.medical_domain,
            'evaluation_time': self.evaluation_time
        }


class LiveEvaluator:
    """
    Real-time evaluator for chatbot responses using HealthBench rubrics
    """
    
    def __init__(self, grader_model: str = "gpt-4o-mini", enabled: bool = True):
        """
        Initialize the live evaluator
        
        Args:
            grader_model: Model to use for grading (gpt-4o-mini, gpt-4, etc.)
            enabled: Whether evaluation is enabled
        """
        self.enabled = enabled
        self.grader_model = grader_model
        self.grader_sampler = None
        self.healthbench_eval = None
        
        if self.enabled:
            try:
                # Initialize grader sampler
                self.grader_sampler = ChatCompletionSampler(
                    model=grader_model,
                    system_message=OPENAI_SYSTEM_MESSAGE_API,
                    max_tokens=2048,
                )
                
                # Load HealthBench evaluation (with a small subset for quick loading)
                print("[EVALUATOR] Loading HealthBench dataset...")
                self.healthbench_eval = HealthBenchEval(
                    grader_model=self.grader_sampler,
                    num_examples=None,  # Load all examples for rubric access
                    n_repeats=1,
                    n_threads=10,  # Lower threads for live evaluation
                    subset_name=None
                )
                print(f"[EVALUATOR] HealthBench loaded with {len(self.healthbench_eval.examples)} examples")
                
            except Exception as e:
                print(f"[EVALUATOR] Failed to initialize: {e}")
                import traceback
                traceback.print_exc()
                self.enabled = False
    
    def evaluate(
        self,
        conversation_history: List[Dict[str, str]],
        bot_question: str,
        medical_context: Optional[str] = None
    ) -> Optional[EvaluationResult]:
        """
        Evaluate a bot response in real-time
        
        Args:
            conversation_history: Previous conversation messages
            bot_question: The bot's response to evaluate
            medical_context: Medical domain/context (e.g., "Cardiac System > Chest Pain")
        
        Returns:
            EvaluationResult with scores and metrics
        """
        if not self.enabled or not self.healthbench_eval:
            return None
        
        start_time = time.time()
        
        try:
            # Find relevant rubrics based on medical context
            relevant_rubrics = self._find_relevant_rubrics(medical_context, bot_question)
            
            if not relevant_rubrics:
                print("[EVALUATOR] No relevant rubrics found, using general medical criteria")
                relevant_rubrics = self._get_general_medical_rubrics()
            
            print(f"[EVALUATOR] Evaluating against {len(relevant_rubrics)} rubrics...")
            
            # Evaluate each rubric
            rubric_scores = []
            for rubric_item in relevant_rubrics[:10]:  # Limit to 10 rubrics for speed
                try:
                    score = self._evaluate_single_rubric(
                        rubric_item=rubric_item,
                        conversation_history=conversation_history,
                        bot_question=bot_question
                    )
                    rubric_scores.append(score)
                except Exception as e:
                    print(f"[EVALUATOR] Failed to evaluate rubric: {e}")
                    continue
            
            # Calculate overall metrics
            overall_score = self._calculate_overall_score(rubric_scores)
            metrics = self._calculate_metrics(rubric_scores)
            
            eval_time = time.time() - start_time
            
            return EvaluationResult(
                overall_score=overall_score,
                rubric_scores=rubric_scores,
                metrics=metrics,
                medical_domain=self._extract_domain(medical_context),
                evaluation_time=eval_time
            )
            
        except Exception as e:
            print(f"[EVALUATOR] Evaluation error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _find_relevant_rubrics(self, medical_context: Optional[str], bot_question: str) -> List[Any]:
        """Find rubrics relevant to the medical context"""
        if not medical_context:
            return []
        
        # Extract keywords from medical context
        context_lower = medical_context.lower()
        relevant_rubrics = []
        
        # Search through HealthBench examples for relevant rubrics
        for example in self.healthbench_eval.examples[:50]:  # Sample first 50
            example_data = example.get('example_data', {})
            rubrics = example_data.get('rubrics', [])
            
            for rubric in rubrics:
                # Check if rubric tags match medical context
                tags = rubric.get('tags', [])
                criterion = rubric.get('criterion', '').lower()
                
                # Match by tags or criterion text
                if any(tag.lower() in context_lower for tag in tags):
                    relevant_rubrics.append(rubric)
                elif any(keyword in criterion for keyword in context_lower.split('>')):
                    relevant_rubrics.append(rubric)
        
        return relevant_rubrics
    
    def _get_general_medical_rubrics(self) -> List[Dict[str, Any]]:
        """Get general medical rubrics applicable to most conversations"""
        general_rubrics = [
            {
                'criterion': 'Uses clear, easy-to-understand language appropriate for patients',
                'points': 1.0,
                'tags': ['communication', 'general'],
                'is_positive': True
            },
            {
                'criterion': 'Shows empathy and acknowledges patient concerns',
                'points': 1.0,
                'tags': ['empathy', 'general'],
                'is_positive': True
            },
            {
                'criterion': 'Asks relevant follow-up questions to gather complete information',
                'points': 1.0,
                'tags': ['thoroughness', 'general'],
                'is_positive': True
            },
            {
                'criterion': 'Avoids making definitive diagnoses or treatment recommendations',
                'points': 1.0,
                'tags': ['safety', 'general'],
                'is_positive': True
            },
            {
                'criterion': 'Provides accurate medical information when explaining concepts',
                'points': 1.0,
                'tags': ['accuracy', 'general'],
                'is_positive': True
            }
        ]
        return general_rubrics
    
    def _evaluate_single_rubric(
        self,
        rubric_item: Dict[str, Any],
        conversation_history: List[Dict[str, str]],
        bot_question: str
    ) -> Dict[str, Any]:
        """Evaluate a single rubric criterion"""
        
        # Build prompt for evaluation
        conversation_text = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in conversation_history
        ])
        
        criterion = rubric_item.get('criterion', '')
        is_positive = rubric_item.get('is_positive', True)
        
        prompt = f"""You are evaluating a medical chatbot's response against a specific criterion.

Conversation history:
{conversation_text}

Bot's response to evaluate:
{bot_question}

Evaluation criterion:
{criterion}

This is a {'POSITIVE' if is_positive else 'NEGATIVE'} criterion.
- If POSITIVE: The bot SHOULD demonstrate this behavior
- If NEGATIVE: The bot should NOT demonstrate this behavior

Evaluate whether the bot's response meets this criterion.

Respond in JSON format:
{{
    "criteria_met": true/false,
    "explanation": "Brief explanation of your decision"
}}
"""
        
        try:
            # Get evaluation from grader model
            messages = [{'role': 'user', 'content': prompt}]
            response = self.grader_sampler([messages])[0]
            
            # Parse response
            result = json.loads(response)
            
            return {
                'criterion': criterion,
                'points': rubric_item.get('points', 1.0),
                'tags': rubric_item.get('tags', []),
                'criteria_met': result.get('criteria_met', False),
                'explanation': result.get('explanation', ''),
                'is_positive': is_positive
            }
            
        except Exception as e:
            print(f"[EVALUATOR] Rubric evaluation failed: {e}")
            # Return neutral result on error
            return {
                'criterion': criterion,
                'points': rubric_item.get('points', 1.0),
                'tags': rubric_item.get('tags', []),
                'criteria_met': False,
                'explanation': f'Evaluation error: {str(e)}',
                'is_positive': is_positive
            }
    
    def _calculate_overall_score(self, rubric_scores: List[Dict[str, Any]]) -> float:
        """Calculate overall score from rubric scores"""
        if not rubric_scores:
            return 0.0
        
        total_points = sum(r['points'] for r in rubric_scores)
        earned_points = sum(
            r['points'] for r in rubric_scores 
            if r['criteria_met'] == r.get('is_positive', True)
        )
        
        return earned_points / total_points if total_points > 0 else 0.0
    
    def _calculate_metrics(self, rubric_scores: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate detailed metrics"""
        total = len(rubric_scores)
        passed = sum(1 for r in rubric_scores if r['criteria_met'] == r.get('is_positive', True))
        
        return {
            'overall_score': self._calculate_overall_score(rubric_scores),
            'num_rubrics_evaluated': total,
            'rubrics_passed': passed,
            'rubrics_failed': total - passed,
            'pass_rate': passed / total if total > 0 else 0.0
        }
    
    def _extract_domain(self, medical_context: Optional[str]) -> Optional[str]:
        """Extract medical domain from context"""
        if not medical_context:
            return None
        
        # Extract first part of tree path as domain
        parts = medical_context.split('>')
        return parts[0].strip() if parts else None


# Singleton instance
_evaluator_instance = None


def get_live_evaluator(grader_model: str = "gpt-4o-mini") -> LiveEvaluator:
    """
    Get or create the live evaluator instance
    
    Args:
        grader_model: Model to use for grading
    
    Returns:
        LiveEvaluator instance
    """
    global _evaluator_instance
    
    # Check if evaluation is enabled via environment variable
    enabled = os.getenv('HEALTHBENCH_EVAL_ENABLED', 'true').lower() == 'true'
    
    if _evaluator_instance is None:
        _evaluator_instance = LiveEvaluator(
            grader_model=grader_model,
            enabled=enabled
        )
    
    return _evaluator_instance


if __name__ == "__main__":
    # Test the evaluator
    print("Testing Live Evaluator...")
    
    evaluator = get_live_evaluator()
    
    if evaluator.enabled:
        # Test evaluation
        test_conversation = [
            {'role': 'user', 'content': 'I have chest pain'},
        ]
        
        test_response = "I understand you're experiencing chest pain. Can you tell me when it started and how long it's been going on?"
        
        result = evaluator.evaluate(
            conversation_history=test_conversation,
            bot_question=test_response,
            medical_context="Cardiac System > Chest Pain > Onset/Duration"
        )
        
        if result:
            print(f"\n✅ Evaluation successful!")
            print(f"Overall Score: {result.overall_score:.2f}")
            print(f"Rubrics Evaluated: {result.metrics['num_rubrics_evaluated']}")
            print(f"Rubrics Passed: {result.metrics['rubrics_passed']}")
        else:
            print("\n❌ Evaluation failed")
    else:
        print("Evaluator is disabled")

