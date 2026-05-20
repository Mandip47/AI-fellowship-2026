"""
app/agents/sql_generator.py
==========================
[ACT] The SQL generation node - creates SQL based on schema and plan.
"""

import os
import re
from typing import Dict, Any, Optional
import requests
from dotenv import load_dotenv
from app.logger import get_logger
from app.graph import AgentState

load_dotenv()
logger = get_logger("SQLGenerator")

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


def _strip_markdown(sql: str) -> str:
    """Remove markdown fences from SQL if present."""
    sql = sql.strip()
    if sql.startswith("```"):
        lines = sql.splitlines()
        inner_lines = [line for line in lines if not line.startswith("```")]
        sql = "\n".join(inner_lines).strip()
    return sql


def generate_sql(question: str, schema: str, plan: str) -> str:
    """
    Generate PostgreSQL SQL based on schema and plan.
    Returns ONLY valid SQL, no markdown, no explanation.
    """
    system_prompt = """You are a PostgreSQL SQL expert. Your job is to write ONLY valid, executable PostgreSQL SELECT statements.

CRITICAL RULES:
1. Return ONLY the SQL - no markdown fences, no explanation
2. Use double quotes for mixed-case identifiers
3. Ensure all column names and table names are correct per the schema
4. Use proper JOIN syntax
5. Test for NULL values appropriately
6. Never include DROP, DELETE, INSERT, UPDATE, or dangerous operations

Your SQL will be executed immediately against a live database."""

    user_prompt = f"""Schema definition:
{schema}

SQL Strategy (from the planner):
{plan}

User question: {question}

Write the PostgreSQL SELECT query. Return ONLY the SQL, no markdown, no explanation."""

    sql = _call_llm(system_prompt, user_prompt)
    sql = _strip_markdown(sql)
    logger.info(f"[Generator] Generated SQL:\n{sql}")
    return sql


def sql_generation_node(state: AgentState) -> Dict[str, Any]:
    """
    [ACT] Node in the LangGraph workflow.
    Takes question + schema + plan and generates SQL.
    """
    trace = state.get("trace", [])

    try:
        logger.info("[Node] Executing sql_generation_node")

        question = state.get("question", "")
        schema = state.get("schema", "")
        plan = state.get("plan", "")

        # Detailed validation with helpful errors
        if not question:
            raise ValueError("Missing required field: question")
        if not schema:
            raise ValueError(
                "Missing required field: schema (schema discovery may have failed)"
            )
        if not plan:
            raise ValueError(
                "Missing required field: plan (planning node may have failed)"
            )

        sql = generate_sql(question, schema, plan)
        trace.append(f"[SQL Generation] Generated SQL:\n{sql}")

        return {
            **state,
            "sql": sql,
            "trace": trace,
        }
    except Exception as e:
        logger.error(f"[Node] SQL generation failed: {e}")
        error_msg = f"[SQL Generation] ERROR: {str(e)}"
        trace.append(error_msg)
        return {
            **state,
            "trace": trace,
        }


__all__ = ["sql_generation_node", "generate_sql"]
