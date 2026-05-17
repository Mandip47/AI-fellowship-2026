from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import engine
from app.router import router
from app import models

app = FastAPI()

app.include_router(router)


@asynccontextmanager
async def lifespan(app: FastAPI):

    async with engine.begin() as conn:

        await conn.run_sync(models.Base.metadata.create_all)

    yield


@app.get("/")
async def root():

    return {"message": "Dashboard API running"}
