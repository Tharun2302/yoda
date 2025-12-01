# -*- coding: utf-8 -*-

"""
Langfuse Integration for Health Chatbot Observability

This module handles logging all chat interactions to Langfuse for observability.
Adapted for HealthYoda chatbot project.

Setup:
1. Install langfuse: pip install langfuse
2. Set environment variables:
   - LANGFUSE_PUBLIC_KEY
   - LANGFUSE_SECRET_KEY
   - LANGFUSE_HOST (optional, defaults to https://cloud.langfuse.com)
3. Import and use: from langfuse_tracker import langfuse_tracker
"""

from datetime import datetime
from typing import Optional, Dict, Any
from langfuse import Langfuse
import os
import time
from dotenv import load_dotenv

# Load environment variables from .env file FIRST
load_dotenv()

# ============================================================================
# CONFIGURATION - Load from environment variables
# ============================================================================

# Check if Langfuse is explicitly disabled
LANGFUSE_ENABLED = os.getenv("LANGFUSE_ENABLED", "true").lower() == "true"

LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

# Initialize Langfuse client
try:
    if not LANGFUSE_ENABLED:
        print("[!] Langfuse explicitly disabled (LANGFUSE_ENABLED=false)")
        langfuse_client = None
    elif not LANGFUSE_SECRET_KEY or not LANGFUSE_PUBLIC_KEY:
        print("[!] Langfuse credentials not found - observability disabled")
        langfuse_client = None
    else:
        langfuse_client = Langfuse(
            public_key=LANGFUSE_PUBLIC_KEY,
            secret_key=LANGFUSE_SECRET_KEY,
            host=LANGFUSE_HOST
        )
        print(f"[OK] Langfuse initialized: {LANGFUSE_HOST}")
except Exception as e:
    print(f"[!] Langfuse initialization failed: {e}")
    langfuse_client = None


# ============================================================================
# LANGFUSE TRACKER - Main class for logging interactions
# ============================================================================

class LangfuseTracker:
    """Handles Langfuse trace logging for chatbot interactions"""
   
    def __init__(self):
        self.client = langfuse_client
   
    def create_trace(
        self,
        user_id: str,
        question: str,
        answer: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        model: str = "gpt-4o-mini"
    ) -> Optional[str]:
        """
        Create a simple chat trace (for non-RAG queries or simple interactions).
       
        Args:
            user_id: Unique identifier for the user
            question: User's question/query
            answer: Bot's response
            session_id: Optional session identifier (defaults to user_id)
            metadata: Optional additional metadata
            model: LLM model used (default: gpt-4o-mini)
       
        Returns:
            Trace ID if successful, None otherwise
        """
        if not self.client:
            return None
       
        try:
            # Build metadata
            trace_metadata = {
                **(metadata or {}),
                "timestamp": datetime.now().isoformat(),
                "chatbot_type": "health"
            }
           
            # Create main trace
            trace = self.client.trace(
                name="chat_interaction",
                user_id=user_id,
                session_id=session_id or user_id,
                input=question,
                output=answer,
                metadata=trace_metadata,
                tags=["chat", "health_chatbot"]
            )
           
            # Add generation span for LLM call
            trace.generation(
                name="chat_response",
                model=model,
                input=question,
                output=answer,
                metadata={"timestamp": datetime.now().isoformat()}
            )
           
            return trace.id
           
        except Exception as e:
            print(f"[ERROR] Langfuse trace failed: {e}")
            return None
   
    def add_feedback(self, trace_id: str, rating: str, comment: Optional[str] = None, generation_id: Optional[str] = None) -> bool:
        """
        Add user feedback (thumbs up/down) to a trace.
       
        Args:
            trace_id: The trace ID to add feedback to
            rating: "thumbs_up" or "thumbs_down"
            comment: Optional comment from the user
            generation_id: Optional generation ID to link score to specific generation
       
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            print("[WARNING] Langfuse client not available, cannot log feedback")
            return False
       
        if not trace_id:
            print("[ERROR] trace_id is required for feedback")
            return False
       
        try:
            # Create score for user rating
            score_value = 1.0 if rating == "thumbs_up" else 0.0
            
            print(f"[FEEDBACK] Creating score: trace_id={trace_id}, name=user_rating, value={score_value}, rating={rating}")
            
            # Get trace object and create score on it
            try:
                trace = self.client.trace(id=trace_id)
                print(f"[FEEDBACK] ✓ Trace found: {trace_id}")
                
                # Create score directly on the trace object - this is the correct method
                # Try without source parameter first
                try:
                    trace.score(
                        name="user_rating",
                        value=score_value,
                        comment=comment or ""
                    )
                    print(f"[FEEDBACK] ✓ Score created on trace (without source)")
                except Exception as no_source_error:
                    # If that fails, try with source parameter
                    print(f"[WARNING] Score without source failed: {no_source_error}, trying with source")
                    trace.score(
                        name="user_rating",
                        value=score_value,
                        comment=comment or "",
                        source="USER"
                    )
                    print(f"[FEEDBACK] ✓ Score created on trace (with source)")
            except Exception as trace_error:
                print(f"[ERROR] Failed to create score on trace: {trace_error}")
                import traceback
                traceback.print_exc()
                
                # Try alternative method: client.score() as fallback
                try:
                    print(f"[FEEDBACK] Attempting fallback: client.score()")
                    self.client.score(
                        trace_id=trace_id,
                        name="user_rating",
                        value=score_value,
                        comment=comment or "",
                        source="USER"
                    )
                    print(f"[FEEDBACK] ✓ Score created via client.score() fallback")
                except Exception as fallback_error:
                    print(f"[ERROR] Fallback also failed: {fallback_error}")
                    return False
            
            # Flush immediately to ensure it's sent to Langfuse
            try:
                flush_result = self.client.flush()
                print(f"[FEEDBACK] ✓ Flushed to Langfuse, result: {flush_result}")
                
                # Small delay to ensure score is processed
                time.sleep(0.5)
            except Exception as flush_error:
                print(f"[WARNING] Flush failed: {flush_error}")
                # Don't return False here as score might still be queued
            
            print(f"[INFO] ✓ Feedback logged successfully: trace_id={trace_id}, rating={rating}, value={score_value}")
            return True
           
        except Exception as e:
            print(f"[ERROR] Langfuse feedback failed: {e}")
            import traceback
            traceback.print_exc()
            return False


# ============================================================================
# GLOBAL TRACKER INSTANCE
# ============================================================================

# Create a global instance for easy import
langfuse_tracker = LangfuseTracker()

