"""
validator.py
============
Rule-based security layer.
Blocks any SQL that is not a pure SELECT statement.
"""

import re

# DML / DDL keywords that must never be executed
_BLOCKED_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE|REPLACE"
    r"|GRANT|REVOKE|EXEC|EXECUTE|CALL|MERGE|UPSERT)\b",
    re.IGNORECASE,
)

# Must start with SELECT (after stripping comments/whitespace)
_SELECT_PATTERN = re.compile(r"^\s*SELECT\b", re.IGNORECASE)

# Detect SQL comment injections
_COMMENT_PATTERN = re.compile(r"(--|/\*|\*/)", re.IGNORECASE)


def validate_sql(sql: str) -> tuple[bool, str]:
    """
    Validate that the SQL is a safe SELECT query.

    Returns
    -------
    (is_valid: bool, reason: str)
        is_valid = True  → safe to execute
        is_valid = False → reason explains why it was blocked
    """
    if not sql or not sql.strip():
        return False, "Empty query."

    # Strip leading/trailing whitespace
    cleaned = sql.strip()

    # Must start with SELECT
    if not _SELECT_PATTERN.match(cleaned):
        return False, (
            "Only SELECT statements are allowed. "
            f"Query starts with: '{cleaned[:30]}...'"
        )

    # Check for dangerous keywords
    match = _BLOCKED_KEYWORDS.search(cleaned)
    if match:
        return False, (
            f"Blocked keyword detected: '{match.group().upper()}'. "
            "Only read-only SELECT queries are permitted."
        )

    # Block comment-based injection attempts
    if _COMMENT_PATTERN.search(cleaned):
        return False, "SQL comment syntax (-- or /* */) is not allowed."

    return True, "OK"
