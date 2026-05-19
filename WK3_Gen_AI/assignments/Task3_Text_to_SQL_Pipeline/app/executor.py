"""
executor.py
===========
Orchestrates the full 3-stage prompt-chain workflow:

  1. Decompose  (LLM call 1)
  2. Generate   (LLM call 2)
  3. Validate   (rule-based — no LLM)
  4. Execute    (PostgreSQL)
  5. Fix + Retry on failure (LLM call 3, max 1 retry)
  6. Log result to logs/query_logs.json

Returns a structured result dict on every call — never crashes.
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from database import execute_query
from sql_generator import decompose_question, generate_sql, fix_sql
from validator import validate_sql

# Path to the JSON log file
LOG_PATH = Path(__file__).parent.parent / "logs" / "query_logs.json"


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
def _load_logs() -> list:
    if LOG_PATH.exists():
        try:
            return json.loads(LOG_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
    return []


def _save_logs(logs: list) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text(
        json.dumps(logs, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
    )


def _append_log(entry: dict) -> None:
    logs = _load_logs()
    logs.append(entry)
    _save_logs(logs)


# ---------------------------------------------------------------------------
# Main pipeline entry point
# ---------------------------------------------------------------------------
def run_pipeline(question: str) -> dict:
    """
    Execute the full Text-to-SQL pipeline for a natural-language question.

    Returns
    -------
    {
        "question":       str,
        "decomposition":  dict | None,
        "sql":            str | None,
        "fixed_sql":      str | None,
        "result":         { columns, rows, row_count, error } | None,
        "status":         "success" | "blocked" | "failed" | "error",
        "retry_attempted": bool,
        "retry_success":  bool,
        "latency_ms":     float,
        "timestamp":      str  (ISO-8601 UTC),
        "error":          str | None,
    }
    """
    start = time.perf_counter()
    timestamp = datetime.now(timezone.utc).isoformat()

    entry: dict = {
        "question": question,
        "decomposition": None,
        "sql": None,
        "fixed_sql": None,
        "result": None,
        "status": "error",
        "retry_attempted": False,
        "retry_success": False,
        "latency_ms": 0.0,
        "timestamp": timestamp,
        "error": None,
    }

    try:
        # ── Stage 1: Decompose ────────────────────────────────────────────
        decomposition = decompose_question(question)
        entry["decomposition"] = decomposition

        # ── Stage 2: Generate SQL ─────────────────────────────────────────
        sql = generate_sql(decomposition)
        entry["sql"] = sql

        # ── Stage 3: Validate ─────────────────────────────────────────────
        is_valid, reason = validate_sql(sql)
        if not is_valid:
            entry["status"] = "blocked"
            entry["error"] = reason
            _finalize(entry, start)
            _append_log(entry)
            return entry

        # ── Stage 4: Execute ──────────────────────────────────────────────
        db_result = execute_query(sql)
        entry["result"] = db_result

        if db_result["error"] is None:
            entry["status"] = "success"
        else:
            # ── Stage 5: Fix + Retry (max 1) ──────────────────────────────
            entry["retry_attempted"] = True
            error_msg = db_result["error"]

            try:
                fixed = fix_sql(sql, error_msg, decomposition)
                entry["fixed_sql"] = fixed

                # Validate the fixed SQL too
                is_valid_fix, fix_reason = validate_sql(fixed)
                if not is_valid_fix:
                    entry["status"] = "blocked"
                    entry["error"] = f"Fixed SQL blocked: {fix_reason}"
                else:
                    retry_result = execute_query(fixed)
                    entry["result"] = retry_result
                    if retry_result["error"] is None:
                        entry["status"] = "success"
                        entry["retry_success"] = True
                    else:
                        entry["status"] = "failed"
                        entry["error"] = retry_result["error"]
            except Exception as fix_exc:
                entry["status"] = "failed"
                entry["error"] = f"Fix stage failed: {fix_exc}"

    except Exception as exc:
        entry["status"] = "error"
        entry["error"] = str(exc)

    _finalize(entry, start)
    _append_log(entry)
    return entry


def _finalize(entry: dict, start: float) -> None:
    """Set latency_ms in-place."""
    entry["latency_ms"] = round((time.perf_counter() - start) * 1000, 2)
