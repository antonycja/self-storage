import csv
import os

from datetime import datetime
import bcrypt
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float, DateTime
from flask_login import UserMixin


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class BaseModel(db.Model):
    """Base model class with common functionality"""
    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now)


class UserModel(BaseModel):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    surname: Mapped[str] = mapped_column(String(250), nullable=False)
    email: Mapped[str] = mapped_column(
        String(250), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String, nullable=False)


class AuthUser(UserMixin):
    def __init__(self, user_dict):
        self.id = user_dict['id']
        self.name = user_dict['name']
        self.surname = user_dict['surname']
        self.email = user_dict['email']
        # self.password_hash = user_dict['password_hash']


class Data(BaseModel):
    __tablename__ = "units"

    unit_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status: Mapped[str] = mapped_column(String(250), nullable=False)
    size_sqm: Mapped[float] = mapped_column(Float, nullable=False)
    monthly_rate: Mapped[str] = mapped_column(String, nullable=False)
    climate_controlled: Mapped[str] = mapped_column(String(5), nullable=False)
    floor_level: Mapped[str] = mapped_column(String(50), nullable=False)
    security_features: Mapped[str] = mapped_column(String, nullable=False)
    rental_duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    pass

