"""
app/agents/planner.py
====================
[PLAN] The planner node - creates step-by-step SQL strategy.
Separates reasoning from generation for accuracy.
"""

import os
import json
import re
from typing import Dict, Any
import requests
from dotenv import load_dotenv
from app.logger import get_logger
from app.graph import AgentState

load_dotenv()
logger = get_logger("Planner")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openrouter/auto"
TIMEOUT = 60


def _call_llm(system: str, user_content: str) -> str:
    """Helper to call OpenRouter LLM."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENROUTER_API_KEY not configured")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.0,
    }

    response = requests.post(
        OPENROUTER_URL, headers=headers, json=payload, timeout=TIMEOUT
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def create_plan(question: str, tables: list, schema: str) -> str:
    """
    Create a step-by-step SQL strategy without writing SQL.
    This is the [PLAN] step in Think-Plan-Act-Execute.
    """
    system_prompt = """You are a senior data analyst expert in database design and SQL optimization.
Your job is to create a detailed step-by-step SQL strategy - NOT to write SQL yet.

For each step, reason about:
1. Which tables need to be joined and why
2. What filtering conditions should be applied
3. What aggregations or calculations are needed
4. How to order and limit results

Be precise but concise. The SQL generator will use your plan to write the actual query."""

    user_prompt = f"""Available tables: {', '.join(tables)}

Full schema:
{schema}

User question: {question}

Create a step-by-step SQL strategy. For each step:
- Explain which tables are involved
- Describe the joins needed (if any)
- List the filters that should be applied
- Specify aggregations or calculations
- Note any special considerations

Do NOT write SQL. Just explain the strategy."""

    plan = _call_llm(system_prompt, user_prompt)
    logger.info(f"[Plan] Created strategy:\n{plan}")
    return plan


def planning_node(state: AgentState) -> Dict[str, Any]:
    """
    [PLAN] Node in the LangGraph workflow.
    Takes question + tables and creates a strategy for SQL generation.
    """
    trace = state.get("trace", [])

    try:
        logger.info("[Node] Executing planning_node")
        plan = create_plan(state["question"], state["tables"], state.get("schema", ""))
        trace.append(f"[Planning] Strategy created:\n{plan}")

        return {
            **state,
            "plan": plan,
            "trace": trace,
        }
    except Exception as e:
        logger.error(f"[Node] Planning failed: {e}")
        error_msg = f"[Planning] ERROR: {str(e)}"
        trace.append(error_msg)
        return {
            **state,
            "trace": trace,
        }


__all__ = ["planning_node", "create_plan"]
