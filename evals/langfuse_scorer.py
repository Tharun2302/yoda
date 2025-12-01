"""
Langfuse Scorer for HealthBench Evaluations

This module logs HealthBench evaluation scores to Langfuse for tracking and analysis.
"""
from typing import Dict, Any, Optional
import time


class LangfuseScorer:
    """
    Logs HealthBench evaluation scores to Langfuse
    """
    
    def __init__(self, langfuse_client=None):
        """
        Initialize the Langfuse scorer
        
        Args:
            langfuse_client: Langfuse client instance (optional)
        """
        self.langfuse = langfuse_client
        self.enabled = langfuse_client is not None
        
        if not self.enabled:
            print("[LANGFUSE SCORER] Langfuse client not provided, scoring disabled")
    
    def log_scores(
        self,
        trace_id: str,
        generation_id: Optional[str],
        eval_results: Any,
        medical_context: Optional[str] = None
    ):
        """
        Log evaluation scores to Langfuse
        
        Args:
            trace_id: Langfuse trace ID
            generation_id: Langfuse generation ID (optional)
            eval_results: EvaluationResult object from live_evaluator
            medical_context: Medical domain context
        """
        if not self.enabled or not self.langfuse:
            return
        
        try:
            # Note: We don't need to fetch the trace object first.
            # Langfuse allows logging scores directly with just the trace_id
            
            # Log overall score (using client.score for compatibility)
            self.langfuse.score(
                trace_id=trace_id,
                name="healthbench_overall_score",
                value=eval_results.overall_score,
                comment=f"HealthBench evaluation score: {eval_results.overall_score:.2f}"
            )
            
            # Log safety score
            safety_score = eval_results.safety_score
            self.langfuse.score(
                trace_id=trace_id,
                name="healthbench_safety_score",
                value=safety_score,
                comment=f"Safety-specific score: {safety_score:.2f}"
            )
            
            # Log pass rate
            pass_rate = eval_results.metrics.get('pass_rate', 0.0)
            self.langfuse.score(
                trace_id=trace_id,
                name="healthbench_pass_rate",
                value=pass_rate,
                comment=f"Percentage of rubrics passed: {pass_rate:.1%}"
            )
            
            # Log tag scores (safety, empathy, accuracy, etc)
            if eval_results.tag_scores:
                for tag, score in eval_results.tag_scores.items():
                    self.langfuse.score(
                        trace_id=trace_id,
                        name=f"healthbench_{tag}_score",
                        value=score,
                        comment=f"{tag.capitalize()} score: {score:.2f}"
                    )
            
            # Log red flags
            if eval_results.red_flags:
                red_flags_summary = f"{len(eval_results.red_flags)} red flag(s) detected"
                for flag in eval_results.red_flags:
                    red_flags_summary += f"\n[{flag['severity']}] {flag['criterion']}"
                
                self.langfuse.score(
                    trace_id=trace_id,
                    name="healthbench_red_flags",
                    value=float(len(eval_results.red_flags)),
                    comment=red_flags_summary[:500]  # Limit comment length
                )
            
            # Log critical failure flag
            if eval_results.critical_failure:
                self.langfuse.score(
                    trace_id=trace_id,
                    name="healthbench_critical_failure",
                    value=1.0,
                    comment="CRITICAL SAFETY VIOLATION DETECTED"
                )
            
            # Log individual rubric scores
            for idx, rubric in enumerate(eval_results.rubric_scores[:5]):  # First 5 only to avoid too many scores
                criterion_short = rubric['criterion'][:50]  # Truncate for readability
                score_value = 1.0 if rubric['criteria_met'] else 0.0
                
                self.langfuse.score(
                    trace_id=trace_id,
                    name=f"healthbench_rubric_{idx}",
                    value=score_value,
                    comment=f"{criterion_short}: {rubric['explanation'][:100]}"
                )
            
            print(f"[LANGFUSE SCORER] ✅ Logged {len(eval_results.rubric_scores) + 2} scores to Langfuse for trace {trace_id}")
            
        except Exception as e:
            print(f"[LANGFUSE SCORER] Failed to log scores: {e}")
            import traceback
            traceback.print_exc()


def create_langfuse_scorer(langfuse_client=None) -> LangfuseScorer:
    """
    Create a Langfuse scorer instance
    
    Args:
        langfuse_client: Langfuse client instance
    
    Returns:
        LangfuseScorer instance
    """
    return LangfuseScorer(langfuse_client=langfuse_client)


if __name__ == "__main__":
    print("Langfuse Scorer Module - Ready for integration")
    print("Usage: scorer = create_langfuse_scorer(langfuse_client)")

