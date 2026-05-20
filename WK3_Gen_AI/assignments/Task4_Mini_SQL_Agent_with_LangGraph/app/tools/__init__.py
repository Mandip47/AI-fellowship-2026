"""
app/tools/db_tools.py
====================
Database tools for schema discovery and query execution.
These are the three core tools that make the system agentic.
"""

import os
import psycopg2
import psycopg2.extras
from typing import List, Dict, Any
from dotenv import load_dotenv
from app.logger import get_logger

load_dotenv()
logger = get_logger("DBTools")

# Database connection parameters
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", 5433)),
    "dbname": os.getenv("POSTGRES_DB", "classicmodels"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
    "connect_timeout": 10,
}


def _get_conn():
    """Create and return a new PostgreSQL connection."""
    return psycopg2.connect(**DB_CONFIG)


def test_connection() -> bool:
    """Return True if PostgreSQL is reachable, False otherwise."""
    try:
        conn = _get_conn()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False


# ─── TOOL 1: List Tables ──────────────────────────────────────────────────────
def list_tables() -> List[str]:
    """
    [TOOL 1: THINK]
    Discover all tables in the database that the agent can query.
    This allows schema discovery without hardcoding.
    """
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            # Query information_schema to get all user tables
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            tables = [row[0] for row in cur.fetchall()]
        conn.close()
        logger.info(f"[Tool] list_tables() discovered {len(tables)} tables: {tables}")
        return tables
    except Exception as e:
        logger.error(f"Error listing tables: {e}")
        return []


# ─── TOOL 2: Get Schema ───────────────────────────────────────────────────────
def get_schema(table_names: List[str]) -> str:
    """
    [TOOL 2: THINK]
    Retrieve full DDL (CREATE TABLE statements) for specified tables.
    Includes column names, types, constraints, and foreign key relationships.
    """
    if not table_names:
        return ""

    schema_info = []
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            for table_name in table_names:
                # Get CREATE TABLE statement from information_schema
                cur.execute(
                    f"""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = %s
                    ORDER BY ordinal_position
                """,
                    (table_name,),
                )
                columns = cur.fetchall()

                # Build schema string
                table_schema = f"CREATE TABLE {table_name} (\n"
                col_defs = []
                for col_name, data_type, is_nullable, col_default in columns:
                    nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
                    col_def = f"  {col_name} {data_type} {nullable}"
                    if col_default:
                        col_def += f" DEFAULT {col_default}"
                    col_defs.append(col_def)

                table_schema += ",\n".join(col_defs)

                # Add foreign keys
                cur.execute(
                    f"""
                    SELECT DISTINCT 
                        kcu.constraint_name,
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                        AND ccu.table_schema = tc.table_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = 'public'
                    AND kcu.table_name = %s
                """,
                    (table_name,),
                )
                fks = cur.fetchall()

                if fks:
                    table_schema += ",\n"
                    fk_defs = []
                    for fk_name, fk_col, fk_table, fk_ref_col in fks:
                        fk_def = f"  FOREIGN KEY ({fk_col}) REFERENCES {fk_table}({fk_ref_col})"
                        fk_defs.append(fk_def)
                    table_schema += ",\n".join(fk_defs)

                table_schema += "\n);\n"
                schema_info.append(table_schema)

        conn.close()
        full_schema = "\n".join(schema_info)
        logger.info(
            f"[Tool] get_schema() retrieved schema for {len(table_names)} tables"
        )
        return full_schema
    except Exception as e:
        logger.error(f"Error retrieving schema: {e}")
        return ""


# ─── TOOL 3: Run Query ────────────────────────────────────────────────────────
def run_query(query: str) -> Dict[str, Any]:
    """
    [TOOL 3: EXECUTE]
    Execute a SELECT query against PostgreSQL.
    Returns a structured result with success status, rows, and any error.
    """
    result = {
        "success": False,
        "rows": [],
        "columns": [],
        "row_count": 0,
        "error": None,
    }

    try:
        conn = _get_conn()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query)
            rows = cur.fetchall()
            result["rows"] = [dict(r) for r in rows]
            result["columns"] = list(rows[0].keys()) if rows else []
            result["row_count"] = len(rows)
            result["success"] = True
        conn.close()
        logger.info(f"[Tool] run_query() succeeded with {result['row_count']} rows")
    except psycopg2.Error as e:
        result["error"] = str(e).strip()
        logger.warning(f"[Tool] run_query() failed: {result['error']}")
    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"
        logger.error(f"[Tool] run_query() unexpected error: {result['error']}")

    return result


__all__ = ["list_tables", "get_schema", "run_query", "test_connection"]
