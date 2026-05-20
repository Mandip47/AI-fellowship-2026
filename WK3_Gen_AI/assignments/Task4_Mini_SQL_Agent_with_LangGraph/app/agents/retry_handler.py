"""
app/agents/retry_handler.py
==========================
[RECOVER] Retry logic node - increments retry counter for self-correction loop.
"""

from typing import Dict, Any
from app.logger import get_logger
from app.graph import AgentState

logger = get_logger("RetryHandler")


def increment_retry_node(state: AgentState) -> Dict[str, Any]:
    """
    [RECOVER] Node in the LangGraph workflow.
    Increments retry counter and feeds corrected SQL back for validation.
    This creates the self-correction loop.
    """
    trace = state.get("trace", [])

    try:
        logger.info("[Node] Executing increment_retry_node")

        retries = state.get("retries", 0) + 1
        validated_sql = state.get("validated_sql", "")

        trace.append(
            f"[Retry Loop] Attempt {retries} - feeding validated SQL back to validator"
        )
        logger.info(
            f"[Retry] Attempt {retries} - looping back to validator with corrected SQL"
        )

        return {
            **state,
            "retries": retries,
            "sql": validated_sql,  # Feed corrected SQL back for next attempt
            "trace": trace,
        }
    except Exception as e:
        logger.error(f"[Node] Retry handler failed: {e}")
        error_msg = f"[Retry Loop] ERROR: {str(e)}"
        trace.append(error_msg)
        return {
            **state,
            "trace": trace,
        }


__all__ = ["increment_retry_node"]
