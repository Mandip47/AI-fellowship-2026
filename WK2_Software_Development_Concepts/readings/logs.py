import sys
from fastapi import FastAPI
from loguru import logger
from contextlib import asynccontextmanager
from config import settings

# --- Factor 11: Logging Setup ---
logger.remove()
logger.add(
    sys.stdout,
    level=settings.log_level,
    format="<green>{time}</green> | <level>{message}</level>",
)


# --- Factor 9: Disposability (Lifespan) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to "Backing Service" (Factor 4)
    logger.info(f"🚀 Starting {settings.app_name} in {settings.current_env} mode")
    logger.info(f"🔌 Connecting to Redis at {settings.db_host}:{settings.db_port}")

    yield  # The app is now running and handling requests (separate startup from request handling and shutdown)

    # Shutdown: Graceful Cleanup
    logger.warning("🛑 Shutting down... closing connections")


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    logger.info("Handling request at /")
    return {"status": "online", "env": settings.current_env}


# --- Factor 7: Port Binding ---
if __name__ == "__main__":
    import uvicorn

    # We fetch the port from Dynaconf, or default to 8000
    uvicorn.run(app, host="0.0.0.0", port=settings.get("PORT", 8000))
