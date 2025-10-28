from application.database import Base
from sqlalchemy import Integer, String, Column, Boolean, ForeignKey, DateTime, LargeBinary, Float, Text
from datetime import datetime
from pytz import UTC
from sqlalchemy.orm import relationship


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
    visit_associations = relationship("VisitData", back_populates="user", cascade="all, delete-orphan")

class Admin(Base):
    __tablename__ = 'admin'
    admin_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user_detail.user_id', ondelete='CASCADE'), unique=True)
    active = Column(Boolean, default=True)
    user = relationship("User", back_populates="admin_associations")
    register_date = Column(DateTime, default=lambda: datetime.now(UTC))

class VisitData(Base):
    __tablename__ = "visit_data"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user_detail.user_id"))
    hs_unique_code = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    file_data = Column(LargeBinary, nullable=False)
    content_type = Column(String, nullable=False)
    place_name = Column(String, nullable=False)
    person_name = Column(String, nullable=False)
    person_position = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    visit_timestamp = Column(DateTime, default=lambda: datetime.now(UTC))
    description = Column(Text, nullable=True)
    user = relationship("User", back_populates="visit_associations")