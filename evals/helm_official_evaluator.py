"""
Official HELM Framework Evaluator for Real-Time Chatbot Evaluation

This module uses the actual installed crfm-helm package
with Stanford CRFM's MedHELM medical dialogue annotators.
"""
import os
import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Import from official HELM package
from helm.clients.auto_client import AutoClient
from helm.common.request import Request
from helm.common.cache_backend_config import SqliteCacheBackendConfig
from helm.benchmark.annotation.model_as_judge import AnnotatorModelInfo


@dataclass
class HelmEvaluationResult:
    """Results from HELM evaluation"""
    accuracy_score: float  # 1-5 scale
    completeness_score: float  # 1-5 scale
    clarity_score: float  # 1-5 scale
    overall_helm_score: float  # Average of 3 scores
    
    accuracy_explanation: str
    completeness_explanation: str
    clarity_explanation: str
    
    evaluation_time: float = 0.0
    
    def to_dict(self):
        """Convert to dictionary for serialization"""
        return {
            'accuracy_score': self.accuracy_score,
            'completeness_score': self.completeness_score,
            'clarity_score': self.clarity_score,
            'overall_helm_score': self.overall_helm_score,
            'accuracy_explanation': self.accuracy_explanation,
            'completeness_explanation': self.completeness_explanation,
            'clarity_explanation': self.clarity_explanation,
            'evaluation_time': self.evaluation_time
        }


class HelmOfficialEvaluator:
    """
    Real-time HELM evaluator using official HELM framework
    
    Uses Stanford CRFM's medical dialogue evaluation system
    """
    
    # Official HELM MediQA evaluation prompt
    EVALUATION_PROMPT = """You are a medical expert tasked with evaluating the quality of a
medical chatbot's response in a patient conversation.

Your goal is to assess how well the response demonstrates medical competence,
thoroughness, and communication clarity.

The recent conversation:
<question>
{QUESTION}
</question>

The chatbot's response to evaluate:
<response>
{RESPONSE}
</response>

Carefully analyze the <response> in the context of the <question>.
For each of the following criteria, rate the response on a scale of 1 to 5 (1 = very poor, 5 = excellent),
and provide a short justification for your score.

Evaluation Criteria:

**Accuracy (1-5)**
- Is the medical information correct and appropriate?
- For intake: Is the question medically relevant?
- For explanations: Is the information factually correct?

**Completeness (1-5)**
- Does the response adequately address what's needed?
- For intake: Does it ask relevant follow-up questions?
- For explanations: Does it cover important aspects?

**Clarity (1-5)**
- Is the response easy for the patient to understand?
- Is it communicated professionally?

Output Format:
Output the evaluation as a single valid JSON object:
{{
    "accuracy": {{
        "score": 0,
        "explanation": "Explain why this score was given."
    }},
    "completeness": {{
        "score": 0,
        "explanation": "Explain why this score was given."
    }},
    "clarity": {{
        "score": 0,
        "explanation": "Explain why this score was given."
    }}
}}

Ensure valid JSON with double quotes. No markdown, no additional text.
"""
    
    def __init__(self, judge_model: str = "openai/gpt-4o-mini", enabled: bool = True):
        """
        Initialize the official HELM evaluator
        
        Args:
            judge_model: HELM model identifier (e.g., "openai/gpt-4o-mini")
            enabled: Whether evaluation is enabled
        """
        self.enabled = enabled
        self.judge_model = judge_model
        self.auto_client = None
        
        if self.enabled:
            try:
                api_key = os.getenv('OPENAI_API_KEY')
                if not api_key:
                    print("[HELM OFFICIAL] OPENAI_API_KEY not found, disabling HELM evaluation")
                    self.enabled = False
                    return
                
                # Initialize HELM's AutoClient with required parameters
                cache_config = SqliteCacheBackendConfig(
                    path='.helm_cache/cache.sqlite'
                )
                
                self.auto_client = AutoClient(
                    credentials={'openaiApiKey': api_key},
                    file_storage_path='.helm_cache',
                    cache_backend_config=cache_config
                )
                
                print(f"[HELM OFFICIAL] [OK] Initialized with official HELM framework ({judge_model})")
                
            except Exception as e:
                print(f"[HELM OFFICIAL] Failed to initialize: {e}")
                import traceback
                traceback.print_exc()
                self.enabled = False
    
    def evaluate(
        self,
        conversation_history: List[Dict[str, str]],
        bot_response: str,
        medical_context: Optional[str] = None
    ) -> Optional[HelmEvaluationResult]:
        """
        Evaluate a bot response using official HELM framework
        
        Args:
            conversation_history: Previous messages
            bot_response: Bot's response to evaluate
            medical_context: Medical domain context
        
        Returns:
            HelmEvaluationResult with scores (1-5 scale)
        """
        if not self.enabled or not self.auto_client:
            return None
        
        start_time = time.time()
        
        try:
            # Build conversation text for HELM
            conversation_text = "\n".join([
                f"{msg['role'].upper()}: {msg['content']}"
                for msg in conversation_history[-5:]  # Last 5 messages
            ])
            
            # Build HELM evaluation prompt
            prompt = self.EVALUATION_PROMPT.format(
                QUESTION=conversation_text,
                RESPONSE=bot_response
            )
            
            # Create HELM Request object
            # HELM uses specific registered model deployments
            # For gpt-4o-mini, use openai/gpt-4o-mini-2024-07-18
            model_name = self.judge_model
            if 'gpt-4o-mini' in model_name and '/' not in model_name:
                model_name = 'openai/gpt-4o-mini-2024-07-18'
            elif model_name == 'openai/gpt-4o-mini':
                model_name = 'openai/gpt-4o-mini-2024-07-18'
            
            helm_request = Request(
                model=model_name,
                model_deployment=model_name,
                prompt=prompt,
                temperature=0.0,
                max_tokens=400,
                echo_prompt=False,
                num_completions=1
            )
            
            # Make request using HELM's AutoClient
            helm_response = self.auto_client.make_request(helm_request)
            
            if not helm_response.success:
                print(f"[HELM OFFICIAL] Request failed: {helm_response.error}")
                return None
            
            # Extract response text
            if not helm_response.completions or len(helm_response.completions) == 0:
                print("[HELM OFFICIAL] No completions returned")
                return None
            
            result_text = helm_response.completions[0].text.strip()
            
            # Clean up response (remove markdown if present)
            if result_text.startswith('```'):
                lines = result_text.split('\n')
                result_text = '\n'.join(lines[1:-1]) if len(lines) > 2 else result_text
                if result_text.startswith('json'):
                    result_text = result_text[4:]
            result_text = result_text.strip()
            
            # Parse JSON response
            result = json.loads(result_text)
            
            # Extract scores (HELM standard format)
            accuracy_score = result.get('accuracy', {}).get('score', 0)
            completeness_score = result.get('completeness', {}).get('score', 0)
            clarity_score = result.get('clarity', {}).get('score', 0)
            
            # Calculate overall (average of 3 scores)
            overall_score = (accuracy_score + completeness_score + clarity_score) / 3.0
            
            eval_time = time.time() - start_time
            
            return HelmEvaluationResult(
                accuracy_score=accuracy_score,
                completeness_score=completeness_score,
                clarity_score=clarity_score,
                overall_helm_score=overall_score,
                accuracy_explanation=result.get('accuracy', {}).get('explanation', ''),
                completeness_explanation=result.get('completeness', {}).get('explanation', ''),
                clarity_explanation=result.get('clarity', {}).get('explanation', ''),
                evaluation_time=eval_time
            )
            
        except Exception as e:
            print(f"[HELM OFFICIAL] Evaluation error: {e}")
            import traceback
            traceback.print_exc()
            return None


# Singleton
_helm_evaluator_instance = None


def get_helm_evaluator(judge_model: str = "openai/gpt-4o-mini") -> HelmOfficialEvaluator:
    """
    Get or create official HELM evaluator instance
    
    Uses the installed crfm-helm[medhelm] package
    """
    global _helm_evaluator_instance
    
    # Check if HELM evaluation is enabled
    enabled = os.getenv('HELM_EVAL_ENABLED', 'true').lower() == 'true'
    
    if _helm_evaluator_instance is None:
        _helm_evaluator_instance = HelmOfficialEvaluator(
            judge_model=judge_model,
            enabled=enabled
        )
    
    return _helm_evaluator_instance


if __name__ == "__main__":
    print("Testing Official HELM Evaluator...")
    
    evaluator = get_helm_evaluator()
    
    if evaluator.enabled:
        test_conv = [
            {'role': 'user', 'content': 'I have chest pain'},
        ]
        
        test_response = "I understand you're experiencing chest pain. Can you tell me when it started and how severe it is?"
        
        print("Running test evaluation using official HELM framework...")
        result = evaluator.evaluate(
            conversation_history=test_conv,
            bot_response=test_response,
            medical_context="Cardiac System > Chest Pain"
        )
        
        if result:
            print(f"\n[OK] Official HELM Evaluation successful!")
            print(f"Overall Score: {result.overall_helm_score:.2f}/5.0")
            print(f"Accuracy: {result.accuracy_score}/5 - {result.accuracy_explanation[:80]}...")
            print(f"Completeness: {result.completeness_score}/5 - {result.completeness_explanation[:80]}...")
            print(f"Clarity: {result.clarity_score}/5 - {result.clarity_explanation[:80]}...")
            print(f"Evaluation Time: {result.evaluation_time:.1f}s")
        else:
            print("\n❌ Evaluation failed")
    else:
        print("HELM Evaluator disabled")

