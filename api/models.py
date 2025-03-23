from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import Mapped, relationship
from database import Base
from enum import Enum as PyEnum


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


class Master(Base):
    __tablename__ = 'master'

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = Column(String, unique=True)
    chat_id: Mapped[str] = Column(String, unique=True)
    active: Mapped[str] = Column(Boolean, default=True)