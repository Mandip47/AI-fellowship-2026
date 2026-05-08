from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv("SQLALCHEMY_DATABASE_URL")

if db_url is None:
    raise RuntimeError("SQLALCHEMY_DATABASE_URL environment variable is not set")

engine = create_engine(db_url)
session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
