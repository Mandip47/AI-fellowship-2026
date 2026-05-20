"""
app/agents/sql_validator.py
==========================
[ACT] The SQL validation node - validates and fixes SQL before execution.
Provides critical error feedback for the retry loop.
"""

import os
import re
from typing import Dict, Any, Optional
import requests
from dotenv import load_dotenv
from app.logger import get_logger
from app.graph import AgentState

load_dotenv()
logger = get_logger("SQLValidator")

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


def _add_quotes_to_identifiers(sql: str) -> str:
    """
    Add double quotes around all unquoted column and table identifiers.
    Preserves existing quoted identifiers and string literals.
    """
    # Pattern to match unquoted identifiers (letters, numbers, underscores)
    # but NOT keywords or already quoted strings
    import re

    # Regex pattern to match SQL keywords that should NOT be quoted
    keywords = (
        r"\b(SELECT|FROM|WHERE|JOIN|ON|LEFT|RIGHT|INNER|OUTER|CROSS|"
        r"AS|AND|OR|NOT|IN|EXISTS|BETWEEN|LIKE|IS|NULL|ORDER|BY|GROUP|"
        r"HAVING|LIMIT|OFFSET|UNION|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|"
        r"CASE|WHEN|THEN|ELSE|END|COUNT|SUM|AVG|MAX|MIN|DISTINCT|ALL|CAST|"
        r"INTERVAL|DATE|TIME|TIMESTAMP)\b"
    )

    # Split by whitespace and quotes, process each token
    tokens = re.split(r'(\s+|"[^"]*"|\([^)]*\)|\'[^\']*\')', sql)
    result = []

    for token in tokens:
        # Skip whitespace, already quoted strings, and keywords
        if (
            not token
            or token.isspace()
            or token.startswith('"')
            or token.startswith("'")
        ):
            result.append(token)
        elif re.match(keywords, token, re.IGNORECASE):
            result.append(token)
        elif token in ("(", ")", ",", ";", "=", "<", ">", "<=", ">=", "!=", "<>"):
            result.append(token)
        elif re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", token):
            # It's an unquoted identifier, add quotes
            result.append(f'"{token}"')
        else:
            result.append(token)

    return "".join(result)


def validate_sql(sql: str, schema: str, error: Optional[str] = None) -> str:
    """
    Validate SQL for correctness before execution.
    If there's a previous error, fix it intelligently.
    Returns validated/corrected SQL with all identifiers properly quoted.
    """
    if error:
        # ERROR MODE: Fix the broken SQL based on the error
        system_prompt = """You are a PostgreSQL expert debugging SQL errors.

The user has provided a BROKEN SQL query and the PostgreSQL error message.

Your job: FIX the SQL to resolve the error.

IMPORTANT RULES:
1. ALL column names and table aliases must be wrapped in double quotes: "columnName"
2. SQL keywords (SELECT, FROM, WHERE, JOIN, etc.) should NOT be quoted
3. Read the error message carefully to understand the issue
4. Fix the exact issue mentioned in the error
5. Simplify if possible (e.g., use COUNT(*) instead of COUNT(column) when counting rows)

Return ONLY the corrected SQL - no markdown, no explanation, no other text."""

        user_prompt = f"""Schema:
{schema}

Broken SQL that failed:
{sql}

PostgreSQL Error:
{error}

Fix this SQL so it works. Remember to quote ALL column names and table aliases with double quotes.
Return only the corrected SQL query."""
    else:
        # VALIDATION MODE: Check syntax and schema references
        system_prompt = """You are a PostgreSQL expert focused on query validation.

Your job: Review the SQL and ensure:
1. ALL column names and table aliases are wrapped in double quotes: "columnName"
2. Valid column names (check against schema)
3. Valid JOIN conditions
4. No syntax errors
5. Proper NULL handling
6. No dangerous operations (DROP, DELETE, INSERT, UPDATE)

If the SQL looks good and properly quoted, return it as-is.
If there are issues or missing quotes, fix them.

Return ONLY corrected SQL - no markdown, no explanation."""

        user_prompt = f"""Schema:
{schema}

SQL to validate:
{sql}

Validate and ensure ALL column names and table aliases are wrapped in double quotes.
Return ONLY the corrected PostgreSQL SQL."""

    corrected = _call_llm(system_prompt, user_prompt)
    corrected = _strip_markdown(corrected)

    # Ensure all identifiers are properly quoted
    corrected = _add_quotes_to_identifiers(corrected)

    logger.info(f"[Validator] Output SQL:\n{corrected}")
    return corrected


def sql_validation_node(state: AgentState) -> Dict[str, Any]:
    """
    [ACT] Node in the LangGraph workflow.
    Validates SQL before execution and fixes errors for retry loop.
    """
    trace = state.get("trace", [])

    try:
        logger.info("[Node] Executing sql_validation_node")

        sql = state.get("sql", "")
        schema = state.get("schema", "")

        # If there was a previous execution error, use fix mode
        execution = state.get("execution", {})
        previous_error = execution.get("error") if execution else None

        if not schema:
            raise ValueError("Schema not available for validation")

        validated_sql = validate_sql(sql, schema, error=previous_error)

        if previous_error:
            trace.append(f"[SQL Validation] Fixed SQL based on error:\n{validated_sql}")
        else:
            trace.append(f"[SQL Validation] Validated SQL:\n{validated_sql}")

        return {
            **state,
            "validated_sql": validated_sql,
            "trace": trace,
        }
    except Exception as e:
        logger.error(f"[Node] SQL validation failed: {e}")
        error_msg = f"[SQL Validation] ERROR: {str(e)}"
        trace.append(error_msg)
        return {
            **state,
            "trace": trace,
        }


__all__ = ["sql_validation_node", "validate_sql"]
