"""
app/graph/workflow.py
====================
"""

from typing import Literal
from langgraph.graph import StateGraph, END
from app.logger import get_logger
from app.graph import AgentState
from app.agents.schema_discoverer import schema_discovery_node
from app.agents.planner import planning_node
from app.agents.sql_generator import sql_generation_node
from app.agents.sql_validator import sql_validation_node
from app.agents.executor import execution_node
from app.agents.retry_handler import increment_retry_node

logger = get_logger("LangGraph")

MAX_RETRIES = 3


def should_retry(state: AgentState) -> Literal["retry", "done"]:
    """
    Router function - inspects execution result and decides: retry or finish?
    This is the conditional edge that creates the self-correction loop.

    Return "retry" → go to increment_retry node → back to sql_validation
    Return "done" → go to END (success or gave up)
    """
    execution = state.get("execution", {})
    retries = state.get("retries", 0)
    max_retries = state.get("max_retries", MAX_RETRIES)

    # If query succeeded, we're done
    if execution.get("success"):
        logger.info("[Router] Execution successful - ending workflow")
        return "done"

    # If we still have retries left, retry
    if retries < max_retries:
        logger.info(
            f"[Router] Execution failed, retrying ({retries + 1}/{max_retries})"
        )
        return "retry"

    # Otherwise, give up
    logger.warning(f"[Router] Max retries ({max_retries}) exhausted - ending workflow")
    return "done"


def build_graph() -> StateGraph:
    """
    Build the complete LangGraph workflow.

    This is the integration point - all nodes and edges are connected here.
    """
    logger.info("[Graph] Building LangGraph workflow...")

    # Create the StateGraph container
    graph = StateGraph(AgentState)

    # Add nodes (units of work)
    logger.info("[Graph] Adding nodes...")
    graph.add_node("schema_discovery", schema_discovery_node)
    graph.add_node("planning", planning_node)
    graph.add_node("sql_generation", sql_generation_node)
    graph.add_node("sql_validation", sql_validation_node)
    graph.add_node("execution", execution_node)
    graph.add_node("increment_retry", increment_retry_node)

    # Set entry point
    logger.info("[Graph] Setting entry point...")
    graph.set_entry_point("schema_discovery")

    # Add linear edges (deterministic flow)
    logger.info("[Graph] Adding linear edges...")
    graph.add_edge("schema_discovery", "planning")
    graph.add_edge("planning", "sql_generation")
    graph.add_edge("sql_generation", "sql_validation")
    graph.add_edge("sql_validation", "execution")

    # Add conditional edge (the retry loop - the agentic part!)
    logger.info("[Graph] Adding conditional retry edge...")
    graph.add_conditional_edges(
        "execution",
        should_retry,
        {
            "retry": "increment_retry",
            "done": END,
        },
    )

    # Add loop edge (back to validator)
    logger.info("[Graph] Adding loop edge...")
    graph.add_edge("increment_retry", "sql_validation")

    logger.info("[Graph] Graph topology complete")
    return graph


def compile_graph():
    """
    Build and compile the graph into a runnable.

    compile() validates the graph topology and returns a callable.
    """
    logger.info("[Graph] Compiling graph...")
    graph_builder = build_graph()
    compiled_graph = graph_builder.compile()
    logger.info("[Graph] Graph compiled successfully")
    return compiled_graph


__all__ = ["compile_graph", "AgentState", "MAX_RETRIES"]
