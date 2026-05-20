"""
app/main.py
===========
FastAPI application interface.
Exposes POST /agent/sql endpoint.
"""

from contextlib import asynccontextmanager
from typing import Any
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.agent import SQLAgent
from app.database import test_connection
from app.logger import get_logger

logger = get_logger("API")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle hook to test PostgreSQL connectivity on startup."""
    logger.info("Initializing FastAPI application...")
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
    title="Mini SQL Agent API",
    description="Agentic System that answers natural-language questions over PostgreSQL with automatic retry self-correction.",
    version="1.0",
    lifespan=lifespan,
)


# ── Schemas ───────────────────────────────────────────────────────────────────
class SQLAgentRequest(BaseModel):
    question: str = Field(
        ...,
        description="The natural-language question you want to ask the database.",
        examples=["How many shipped orders are from USA customers?"],
    )


class SQLAgentResponse(BaseModel):
    sql: str = Field(..., description="The final valid SELECT query executed.")
    result: Any = Field(
        ..., description="The query execution result (can be rows or direct scalar)."
    )
    summary: str = Field(
        ..., description="Natural language summary describing the results."
    )
    status: str = Field(..., description="Status of the agent: success or failed.")


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
    return {
        "service": "Mini SQL Agent API",
        "status": "online",
        "db_connected": test_connection(),
    }


@app.post("/agent/sql")
def execute_sql_agent(payload: SQLAgentRequest):
    """
    Run the self-correcting SQL Agent on the provided question.
    Processes Decompose -> Generate -> Safe Validate -> Execute -> Retry Correction -> Summarize.
    """
    logger.info(f"API Request Received: question='{payload.question}'")

    agent = SQLAgent(max_retries=3)
    response_data = agent.run(payload.question)

    # Check if there is an error in status to help debug
    if response_data.get("status") == "failed":
        logger.error(
            f"Agent failed to execute successfully: {response_data.get('error')}"
        )

    return response_data
