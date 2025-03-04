from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from config import url

async_engine = create_async_engine(
    url=url,
    echo=False,
)

async_session_factory = async_sessionmaker(async_engine)

class Base(DeclarativeBase):
    pass