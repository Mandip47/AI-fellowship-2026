"""
app/langsmith_config.py
=======================
LangSmith observability configuration.
Enables tracing of agent workflows for debugging and validation.
"""

import os
from typing import Optional


def setup_langsmith() -> bool:
    """
    Configure LangSmith tracing for the application.

    LangSmith enables:
    - Real-time trace visualization
    - Complete workflow observation
    - Error debugging with full context
    - Performance analytics

    Returns:
        bool: True if LangSmith is configured, False otherwise
    """
    api_key = os.getenv("LANGCHAIN_API_KEY")

    if not api_key:
        print("⚠ LangSmith tracing disabled. Set LANGCHAIN_API_KEY to enable.")
        return False

    # Environment variables for LangSmith
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = os.getenv(
        "LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com"
    )
    os.environ["LANGCHAIN_API_KEY"] = api_key
    os.environ["LANGCHAIN_PROJECT"] = os.getenv(
        "LANGCHAIN_PROJECT", "sql-agent-langgraph"
    )

    print(f"✓ LangSmith enabled for project: {os.environ['LANGCHAIN_PROJECT']}")
    print(f"  Dashboard: https://smith.langchain.com/o/")
    return True


def get_langsmith_url() -> Optional[str]:
    """
    Get the LangSmith dashboard URL for the project.

    Returns:
        Optional[str]: Full URL to project dashboard or None if not configured
    """
    if not os.getenv("LANGCHAIN_API_KEY"):
        return None

    project = os.getenv("LANGCHAIN_PROJECT", "sql-agent-langgraph")
    return f"https://smith.langchain.com/o/projects/p/{project}"


def get_trace_url_for_run(run_id: str) -> Optional[str]:
    """
    Get the LangSmith dashboard URL for a specific trace.

    Args:
        run_id: UUID of the trace

    Returns:
        Optional[str]: Full URL to trace or None if not configured
    """
    if not os.getenv("LANGCHAIN_API_KEY"):
        return None

    return f"https://smith.langchain.com/r/runs/{run_id}"
