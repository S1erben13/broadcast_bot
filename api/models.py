from sqlalchemy import Column, Integer, String, Text, Boolean
from sqlalchemy.orm import Mapped
from database import Base

class Message(Base):
    __tablename__ = 'message'

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    author_id: Mapped[str] = Column(String)
    text: Mapped[str] = Column(Text)

class User(Base):
    __tablename__ = 'user'

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = Column(String)
    chat_id: Mapped[str] = Column(String, unique=True)
    last_message_id: Mapped[str] = Column(Integer)
    followed: Mapped[bool] = Column(Boolean, default=True)
