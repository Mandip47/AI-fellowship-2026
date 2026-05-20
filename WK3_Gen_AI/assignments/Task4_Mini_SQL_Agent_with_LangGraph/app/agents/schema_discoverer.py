"""
app/agents/schema_discoverer.py
===============================
[THINK] The schema discovery node - discovers database structure at runtime.
"""

from typing import Dict, Any
from app.logger import get_logger
from app.graph import AgentState
from app.tools import list_tables, get_schema

logger = get_logger("SchemaDiscoverer")


def schema_discovery_node(state: AgentState) -> Dict[str, Any]:
    """
    [THINK] Node in the LangGraph workflow.
    Discovers all available tables and their schema using tools.

    This is what makes the system agentic:
    - Schema is discovered at RUNTIME, not hardcoded
    - Works on ANY PostgreSQL database
    - Automatically adapts when schema changes
    """
    trace = state.get("trace", [])

    try:
        logger.info("[Node] Executing schema_discovery_node")

        # Tool 1: Discover tables
        tables = list_tables()
        trace.append(f"[Schema Discovery] Found tables: {tables}")
        logger.info(f"[Schema] Discovered {len(tables)} tables")

        if not tables:
            raise ValueError("No tables found in database")

        # Tool 2: Get full schema
        schema = get_schema(tables)
        if not schema:
            raise ValueError("Failed to retrieve schema from database")

        trace.append(f"[Schema Discovery] Retrieved schema for {len(tables)} tables")
        logger.info(f"[Schema] Retrieved full schema definition")

        return {
            **state,
            "tables": tables,
            "schema": schema,
            "trace": trace,
        }
    except Exception as e:
        logger.error(f"[Node] Schema discovery failed: {e}")
        error_msg = f"[Schema Discovery] ERROR: {str(e)}"
        trace.append(error_msg)
        return {
            **state,
            "trace": trace,
        }


__all__ = ["schema_discovery_node"]
