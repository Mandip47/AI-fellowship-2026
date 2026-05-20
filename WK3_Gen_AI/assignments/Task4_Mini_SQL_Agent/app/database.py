"""
app/database.py
===============
PostgreSQL database connection and execution helper.
"""

import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# Load env variables from root level .env
load_dotenv()


def _get_conn():
    """Create and return a new PostgreSQL connection."""
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", 5433)),
        dbname=os.getenv("POSTGRES_DB", "classicmodels"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        connect_timeout=10,
    )


def test_connection() -> bool:
    """Return True if PostgreSQL is reachable, False otherwise."""
    try:
        conn = _get_conn()
        conn.close()
        return True
    except Exception:
        return False


def execute_query(sql: str) -> dict:
    """
    Execute a SELECT query and return a structured dictionary:
    {
        "columns": [...],
        "rows": [...],     # list of dicts
        "row_count": int,
        "error": None | str
    }
    """
    result = {"columns": [], "rows": [], "row_count": 0, "error": None}

    try:
        conn = _get_conn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql)
                rows = cur.fetchall()
                result["rows"] = [dict(r) for r in rows]
                result["row_count"] = len(rows)
                result["columns"] = list(rows[0].keys()) if rows else []
        finally:
            conn.close()
    except psycopg2.Error as exc:
        result["error"] = str(exc).strip()
    except Exception as exc:
        result["error"] = f"Unexpected error: {exc}"

    return result
