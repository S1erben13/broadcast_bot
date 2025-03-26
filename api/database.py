from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from config import DATABASE_URL

async_engine = create_async_engine(
    url=DATABASE_URL,
    echo=False,
)

async_session_factory = async_sessionmaker(async_engine)

class Base(DeclarativeBase):
    pass