from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import Mapped, relationship
from database import Base
from enum import Enum as PyEnum


class Message(Base):
    __tablename__ = 'message'

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    author_id: Mapped[str] = Column(String)
    text: Mapped[str] = Column(Text)


class Role(PyEnum):
    MASTER = "master"
    SERVANT = "servant"


class Company(Base):
    __tablename__ = 'company'

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = Column(String, nullable=False)

    user_roles = relationship('UserCompanyRole', back_populates='company')


class UserCompanyRole(Base):
    __tablename__ = 'user_company_role'

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = Column(Integer, ForeignKey('user.id'), nullable=False)
    company_id: Mapped[int] = Column(Integer, ForeignKey('company.id'), nullable=False)
    role: Mapped[Role] = Column(Enum(Role), nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'company_id', 'role', name='uq_user_company_role'),
    )

    user = relationship('User', back_populates='company_roles')

    company = relationship('Company', back_populates='user_roles')


class User(Base):
    __tablename__ = 'user'

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = Column(String)
    chat_id: Mapped[str] = Column(String, unique=True)
    last_message_id: Mapped[str] = Column(Integer)
    followed: Mapped[bool] = Column(Boolean, default=True)

    company_roles = relationship('UserCompanyRole', back_populates='user')


class Master(Base):
    __tablename__ = 'master'

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = Column(String, unique=True)
    chat_id: Mapped[str] = Column(String, unique=True)
    active: Mapped[str] = Column(Boolean, default=True)

    company_roles = relationship('UserCompanyRole', back_populates='user')
