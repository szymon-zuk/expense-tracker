import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum, Integer, String

from database import Base


class UserRole(PyEnum):
    USER = "user"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.UTC))
    username = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    role = Column(
        Enum(UserRole, name="user_role"), default=UserRole.USER, nullable=False
    )
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
