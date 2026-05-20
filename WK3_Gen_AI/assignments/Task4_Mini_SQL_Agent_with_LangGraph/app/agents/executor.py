"""
app/agents/executor.py
=====================
[EXECUTE] The execution node - runs validated SQL and captures results.
"""

from typing import Dict, Any
from app.logger import get_logger
from app.graph import AgentState
from app.tools import run_query

logger = get_logger("Executor")


def execution_node(state: AgentState) -> Dict[str, Any]:
    """
    [EXECUTE] Node in the LangGraph workflow.
    Executes the validated SQL against PostgreSQL.
    Captures result or error for the retry loop.
    """
    trace = state.get("trace", [])

    try:
        logger.info("[Node] Executing execution_node")

        validated_sql = state.get("validated_sql", "")
        if not validated_sql:
            raise ValueError("No validated SQL to execute")

        # Tool 3: Run the query
        result = run_query(validated_sql)
        trace.append(f"[Execution] Query executed. Success: {result['success']}")

        if result["success"]:
            trace.append(f"[Execution] Returned {result['row_count']} rows")
            logger.info(f"[Execution] Query succeeded with {result['row_count']} rows")
        else:
            trace.append(f"[Execution] Error: {result.get('error', 'Unknown error')}")
            logger.warning(
                f"[Execution] Query failed: {result.get('error', 'Unknown error')}"
            )

        return {
            **state,
            "execution": result,
            "trace": trace,
        }
    except Exception as e:
        logger.error(f"[Node] Execution failed: {e}")
        error_msg = f"[Execution] ERROR: {str(e)}"
        trace.append(error_msg)

        return {
            **state,
            "execution": {
                "success": False,
                "rows": [],
                "columns": [],
                "row_count": 0,
                "error": str(e),
            },
            "trace": trace,
        }


__all__ = ["execution_node"]
