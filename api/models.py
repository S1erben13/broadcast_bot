from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import Mapped

from database import Base


class Message(Base):
    __tablename__ = 'messages'

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    author_id: Mapped[str] = Column(String)
    text: Mapped[str] = Column(Text)

class MessageCreate(BaseModel):
    author_id: str
    text: str

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = Column(String)
    chat_id: Mapped[str] = Column(String, unique=True)

class UserCreate(BaseModel):
    user_id: str
    chat_id: str