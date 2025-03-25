from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import Mapped, relationship
from database import Base
from enum import Enum as PyEnum


class Message(Base):
    __tablename__ = 'message'

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    telegram_user_id: Mapped[str] = Column(String)
    project_id: Mapped[int] = Column(Integer)
    text: Mapped[str] = Column(Text)


class User(Base):
    __tablename__ = 'user'

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    telegram_user_id: Mapped[str] = Column(String)
    telegram_chat_id: Mapped[str] = Column(String, unique=True)
    project_id: Mapped[int] = Column(Integer)
    last_message_id: Mapped[str] = Column(Integer)
    is_active: Mapped[bool] = Column(Boolean, default=True)


class Master(Base):
    __tablename__ = 'master'

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    telegram_user_id: Mapped[str] = Column(String, unique=True)
    telegram_chat_id: Mapped[str] = Column(String, unique=True)
    project_id: Mapped[int] = Column(Integer)
    is_active: Mapped[bool] = Column(Boolean, default=True)


class Project(Base):
    __tablename__ = 'project'

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    master_token: Mapped[str] = Column(String, unique=True)
    servant_token: Mapped[str] = Column(String, unique=True)
    master_reg_token: Mapped[str] = Column(String, unique=True)
    servant_reg_token: Mapped[str] = Column(String, unique=True)
    is_active: Mapped[bool] = Column(Boolean, default=True)