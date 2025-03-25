from sqlalchemy import Column, Integer, String, Text, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped
from database import Base


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
    telegram_chat_id: Mapped[str] = Column(String)
    project_id: Mapped[int] = Column(Integer)
    last_message_id: Mapped[str] = Column(Integer)
    is_active: Mapped[bool] = Column(Boolean, default=True)

    __table_args__ = (UniqueConstraint('telegram_user_id', 'telegram_chat_id', 'project_id', name='_user_uc'),)


class Master(Base):
    __tablename__ = 'master'

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    telegram_user_id: Mapped[str] = Column(String)
    telegram_chat_id: Mapped[str] = Column(String)
    project_id: Mapped[int] = Column(Integer)
    is_active: Mapped[bool] = Column(Boolean, default=True)

    __table_args__ = (UniqueConstraint('telegram_user_id', 'telegram_chat_id', 'project_id', name='_master_uc'),)


class Project(Base):
    __tablename__ = 'project'

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    master_token: Mapped[str] = Column(String, unique=True)
    servant_token: Mapped[str] = Column(String, unique=True)
    master_reg_token: Mapped[str] = Column(String)
    servant_reg_token: Mapped[str] = Column(String)
    is_active: Mapped[bool] = Column(Boolean, default=True)