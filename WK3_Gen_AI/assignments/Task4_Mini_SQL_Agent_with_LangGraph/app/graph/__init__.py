"""
app/graph/state.py
=================
AgentState definition - the shared brain of the LangGraph workflow.
"""

from typing import TypedDict, List, Optional, Dict, Any


class AgentState(TypedDict, total=False):
    """
    Shared state that all nodes in the graph can read and mutate.

    Think of this as a whiteboard where each agent writes the results
    of its thinking for the next agent to build upon.
    """

    # Input
    question: str  # Original user question

    # [THINK] Schema Discovery
    tables: List[str]  # Discovered table names
    schema: str  # Full DDL/schema information

    # [PLAN] Planning
    plan: str  # Step-by-step SQL strategy

    # [ACT] SQL Generation
    sql: str  # Generated SQL (may have errors)

    # [ACT] SQL Validation
    validated_sql: str  # Validated/corrected SQL

    # [EXECUTE] Query Execution
    execution: Dict[str, Any]  # {success, result, error, rows, columns}

    # [RECOVER] Retry logic
    retries: int  # Current retry attempt count
    max_retries: int  # Maximum retry attempts (default 3)

    # Observability
    trace: List[str]  # Full human-readable execution log
