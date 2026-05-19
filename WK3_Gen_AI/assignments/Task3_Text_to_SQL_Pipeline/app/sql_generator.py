"""
sql_generator.py
================
Handles all three LLM calls via OpenRouter:
  Call 1 – decompose_question()  → structured JSON
  Call 2 – generate_sql()        → raw SQL string
  Call 3 – fix_sql()             → corrected SQL string
"""

import json
import os

import requests
from dotenv import load_dotenv

from prompts import DECOMPOSE_PROMPT, GENERATE_PROMPT, FIX_PROMPT, SYSTEM_PROMPT

load_dotenv()

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openrouter/auto"  # routes to the best available free model
TIMEOUT = 60


def _call_llm(system: str, user_content: str, json_mode: bool = False) -> str:
    """
    Internal helper: send one request to OpenRouter and return the text response.
    Raises requests.HTTPError on non-2xx responses.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENROUTER_API_KEY is not set in environment.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: dict = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    response = requests.post(
        OPENROUTER_URL, headers=headers, json=payload, timeout=TIMEOUT
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


# ---------------------------------------------------------------------------
# Call 1 – Decompose
# ---------------------------------------------------------------------------
def decompose_question(question: str) -> dict:
    """
    Stage 1: Break a natural-language question into structured components.

    Returns
    -------
    dict with keys: question, intent, tables, columns, filters, joins,
                    aggregations, order_by, limit, notes
    """
    raw = _call_llm(
        system=DECOMPOSE_PROMPT,
        user_content=question,
        json_mode=True,
    )
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Decompose LLM returned invalid JSON:\n{raw}") from exc


# ---------------------------------------------------------------------------
# Call 2 – Generate SQL
# ---------------------------------------------------------------------------
def generate_sql(decomposition: dict) -> str:
    """
    Stage 2: Convert a structured decomposition dict into a SQL query string.

    Returns
    -------
    str — a raw SQL query (no markdown fences)
    """
    user_content = (
        "Generate a PostgreSQL SELECT query for this decomposition:\n\n"
        + json.dumps(decomposition, indent=2)
    )
    sql = _call_llm(
        system=GENERATE_PROMPT,
        user_content=user_content,
        json_mode=False,
    )
    # Strip any accidental markdown fences the model might add
    sql = sql.strip()
    if sql.startswith("```"):
        lines = sql.splitlines()
        # Remove first and last fence lines
        inner = [l for l in lines if not l.startswith("```")]
        sql = "\n".join(inner).strip()
    return sql


# ---------------------------------------------------------------------------
# Call 3 – Fix SQL
# ---------------------------------------------------------------------------
def fix_sql(original_sql: str, error_message: str, decomposition: dict) -> str:
    """
    Stage 3: Given a broken SQL and its error, produce a corrected SQL string.

    Returns
    -------
    str — corrected SQL query
    """
    user_content = json.dumps(
        {
            "original_sql": original_sql,
            "error_message": error_message,
            "decomposition": decomposition,
        },
        indent=2,
    )
    fixed = _call_llm(
        system=FIX_PROMPT,
        user_content=user_content,
        json_mode=False,
    )
    fixed = fixed.strip()
    if fixed.startswith("```"):
        lines = fixed.splitlines()
        inner = [l for l in lines if not l.startswith("```")]
        fixed = "\n".join(inner).strip()
    return fixed
