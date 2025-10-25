import secrets
from sqlalchemy.types import Unicode
from application.database import Base
from sqlalchemy import Integer, String, Column, Boolean, ForeignKey, DateTime, BigInteger
from sqlalchemy import ForeignKeyConstraint
from datetime import datetime
from pytz import UTC
from sqlalchemy.orm import relationship

def generate_token():
    return secrets.token_urlsafe(32)

class User(Base):
    __tablename__ = 'user_detail'

    user_id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    phone_number = Column(String, unique=True, default=None)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String)
    active = Column(Boolean, default=True)
    register_date = Column(DateTime, default=lambda: datetime.now(UTC))

    admin_associations = relationship("Admin", back_populates="user", cascade="all, delete-orphan")


class Admin(Base):
    __tablename__ = 'admin'
    admin_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user_detail.user_id', ondelete='CASCADE'), unique=True)
    active = Column(Boolean, default=True)
    user = relationship("User", back_populates="admin_associations")
    register_date = Column(DateTime, default=lambda: datetime.now(UTC))

