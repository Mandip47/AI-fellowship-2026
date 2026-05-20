"""
app/main.py
==========
FastAPI application interface for the LangGraph agent.
Exposes POST /agent/sql endpoint.
"""

import os
from contextlib import asynccontextmanager
from typing import Any
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.graph.workflow import compile_graph, AgentState
from app.tools import test_connection
from app.logger import get_logger
from app.langsmith_config import setup_langsmith, get_langsmith_url

# Initialize LangSmith tracing if credentials are provided
setup_langsmith()

logger = get_logger("API")

# Compile the graph once at startup
compiled_graph = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle hook to initialize graph and test DB connectivity."""
    global compiled_graph
    logger.info("Initializing FastAPI application...")

    # Compile the LangGraph workflow
    try:
        compiled_graph = compile_graph()
        logger.info("LangGraph workflow compiled successfully")
    except Exception as e:
        logger.error(f"Failed to compile LangGraph workflow: {e}")
        raise

    # Test database connectivity
    if test_connection():
        logger.info("Successfully connected to the PostgreSQL database.")
    else:
        logger.warning(
            "Could not connect to PostgreSQL on startup. "
            "Please check that your database container is running and environment variables are set correctly."
        )

    yield

    logger.info("Shutting down FastAPI application.")


app = FastAPI(
    title="LangGraph SQL Agent API",
    description="Agentic system using LangGraph - Think-Plan-Act-Execute architecture for Text-to-SQL generation with self-correction.",
    version="2.0",
    lifespan=lifespan,
)


# ── Schemas ───────────────────────────────────────────────────────────────────
class SQLAgentRequest(BaseModel):
    question: str = Field(
        ...,
        description="The natural-language question you want to ask the database.",
        examples=["What are the top 10 customers by revenue?"],
    )


class ExecutionResult(BaseModel):
    success: bool = Field(..., description="Whether the query executed successfully")
    rows: list = Field(..., description="Query result rows")
    columns: list = Field(..., description="Column names")
    row_count: int = Field(..., description="Number of rows returned")
    error: Any = Field(..., description="Error message if failed")


class SQLAgentResponse(BaseModel):
    question: str = Field(..., description="The original question")
    sql: str = Field(..., description="The final SQL query executed")
    result: Any = Field(..., description="Query execution result (rows or scalar)")
    execution: ExecutionResult = Field(
        ..., description="Detailed execution information"
    )
    status: str = Field(..., description="Status: success or failed")
    retries: int = Field(..., description="Number of retry attempts made")
    trace: list = Field(
        ..., description="Full execution trace showing all reasoning steps"
    )
    langsmith_url: Any = Field(
        default=None,
        description="LangSmith dashboard link for observability (if configured)",
    )


# ── Exception Handlers ────────────────────────────────────────────────────────
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    logger.warning(
        f"API request validation error on {request.url.path}: {exc.errors()}"
    )
    return JSONResponse(
        status_code=422,
        content={"detail": "Request body validation failed", "errors": exc.errors()},
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    """Root metadata check endpoint."""
    langsmith_url = get_langsmith_url()
    return {
        "message": "LangGraph SQL Agent API",
        "version": "2.0",
        "status": "healthy",
        "endpoint": "/agent/sql (POST)",
        "documentation": "/docs",
        "observability": {
            "enabled": langsmith_url is not None,
            "dashboard": langsmith_url,
        },
    }


@app.post("/agent/sql", response_model=SQLAgentResponse)
def run_agent(request: SQLAgentRequest):
    """
    Execute the LangGraph workflow for a natural language SQL question.

    The workflow implements Think-Plan-Act-Execute:
    1. THINK: Discover database schema at runtime
    2. PLAN: Create step-by-step SQL strategy
    3. ACT: Generate and validate SQL
    4. EXECUTE: Run query with self-correction retry loop
    """
    if not compiled_graph:
        logger.error("LangGraph not initialized")
        raise HTTPException(
            status_code=500, detail="LangGraph workflow not initialized"
        )

    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    logger.info(f"--- START LangGraph AGENT WORKFLOW ---")
    logger.info(f"Question: {question}")

    try:
        # Initialize state
        initial_state: AgentState = {
            "question": question,
            "tables": [],
            "schema": "",
            "plan": "",
            "sql": "",
            "validated_sql": "",
            "execution": {
                "success": False,
                "rows": [],
                "columns": [],
                "row_count": 0,
                "error": None,
            },
            "retries": 0,
            "max_retries": 3,
            "trace": [],
        }

        # Invoke the compiled graph
        logger.info("Invoking LangGraph workflow...")
        final_state = compiled_graph.invoke(initial_state)

        logger.info(
            f"--- END LangGraph AGENT WORKFLOW (Status: {final_state['execution'].get('success', False)}) ---"
        )

        # Prepare response
        execution_result = final_state.get("execution", {})

        # Unpack result - if single scalar value, return that; otherwise return rows
        result = execution_result.get("rows", [])
        if result and len(result) == 1 and len(result[0]) == 1:
            result = list(result[0].values())[0]

        status = "success" if execution_result.get("success") else "failed"

        # Get LangSmith URL if available
        langsmith_url = get_langsmith_url()

        return SQLAgentResponse(
            question=question,
            sql=final_state.get("sql", ""),
            result=result,
            execution=ExecutionResult(**execution_result),
            status=status,
            retries=final_state.get("retries", 0),
            trace=final_state.get("trace", []),
            langsmith_url=langsmith_url,
        )

    except Exception as e:
        logger.error(f"Agent workflow error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent workflow failed: {str(e)}")


@app.get("/health")
def health_check():
    """Health check endpoint."""
    db_ok = test_connection()
    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
