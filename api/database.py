import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

postgres_user = os.getenv("POSTGRES_USER")
postgres_password = os.getenv("POSTGRES_PASSWORD")
postgres_db = os.getenv("POSTGRES_DB")
url = f'postgresql+asyncpg://{postgres_user}:{postgres_password}@postgres:5432/{postgres_db}'

print(url)

async_engine = create_async_engine(
    url=url,
    echo=True,
)

async_session_factory = async_sessionmaker(async_engine)

class Base(DeclarativeBase):
    pass