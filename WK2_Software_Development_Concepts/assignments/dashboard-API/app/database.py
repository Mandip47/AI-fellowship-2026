from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = (
    f"postgresql+asyncpg://"
    f"{os.getenv('POSTGRES_USER')}:"
    f"{os.getenv('POSTGRES_PASSWORD')}@"
    f"{os.getenv('POSTGRES_HOST')}:"
    f"{os.getenv('POSTGRES_PORT')}/"
    f"{os.getenv('POSTGRES_DB')}"
)

engine = create_async_engine(DATABASE_URL, echo=False)

SessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()


async def get_db():
    async with SessionLocal() as session:
        yield session
