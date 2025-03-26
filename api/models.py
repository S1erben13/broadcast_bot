from sqlalchemy import Column, Integer, String, Text, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, declared_attr
from database import Base


class BaseModel(Base):
    """Base model with common columns"""
    __abstract__ = True

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    is_active: Mapped[bool] = Column(Boolean, default=True)

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()


class Message(BaseModel):
    """Message model"""
    telegram_user_id: Mapped[str] = Column(String)
    project_id: Mapped[int] = Column(Integer)
    text: Mapped[str] = Column(Text)


class User(BaseModel):
    """User model"""
    telegram_user_id: Mapped[str] = Column(String)
    telegram_chat_id: Mapped[str] = Column(String)
    project_id: Mapped[int] = Column(Integer)
    last_message_id: Mapped[int] = Column(Integer)

    __table_args__ = (
        UniqueConstraint(
            'telegram_user_id',
            'telegram_chat_id',
            'project_id',
            name='uq_user_identity'
        ),
    )


class Master(BaseModel):
    """Master user model"""
    telegram_user_id: Mapped[str] = Column(String)
    telegram_chat_id: Mapped[str] = Column(String)
    project_id: Mapped[int] = Column(Integer)

    __table_args__ = (
        UniqueConstraint(
            'telegram_user_id',
            'telegram_chat_id',
            'project_id',
            name='uq_master_identity'
        ),
    )


class Project(BaseModel):
    """Project model"""
    master_token: Mapped[str] = Column(String, unique=True)
    servant_token: Mapped[str] = Column(String, unique=True)
    master_reg_token: Mapped[str] = Column(String)
    servant_reg_token: Mapped[str] = Column(String)