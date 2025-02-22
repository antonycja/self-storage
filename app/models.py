from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Float, DateTime, JSON, Enum, ForeignKey, CheckConstraint, Numeric
from flask_login import UserMixin
from typing import Optional, List
import enum


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
    name: Mapped[str] = mapped_column(
        String(50), nullable=False)  # 250 is quite long for names
    surname: Mapped[str] = mapped_column(
        String(50), nullable=False)  # 250 is quite long for surnames
    email: Mapped[str] = mapped_column(
        String(250),
        nullable=False,
        unique=True,
        index=True  # Add index for email lookups
    )
    password: Mapped[str] = mapped_column(String, nullable=False)

    # Relationships with UnitModel
    owned_units = relationship(
        "UnitModel",
        foreign_keys="UnitModel.user_id",
        back_populates="owner"
    )

    rented_units = relationship(
        "UnitModel",
        foreign_keys="UnitModel.tenant_id",
        back_populates="tenant"
    )

    # Add some basic validation
    __table_args__ = (
        CheckConstraint(
            "length(email) > 5",  # Basic email length check
            name="email_length_check"
        ),
    )


class AuthUser(UserMixin):
    def __init__(self, user_dict):
        self.id = user_dict['id']
        self.name = user_dict['name']
        self.surname = user_dict['surname']
        self.email = user_dict['email']
        # self.password_hash = user_dict['password_hash']


class UnitStatus(enum.Enum):
    AVAILABLE = "AVAILABLE"
    OCCUPIED = "OCCUPIED"
    RESERVED = "RESERVED"
    MAINTENANCE = "MAINTENANCE"


class UnitModel(BaseModel):
    __tablename__ = "units"

    unit_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status: Mapped[UnitStatus] = mapped_column(
        Enum(UnitStatus), nullable=False)
    size_sqm: Mapped[float] = mapped_column(Float, nullable=False)
    # Keeping as string since that's your current setup
    monthly_rate: Mapped[float] = mapped_column(Numeric(10,2), nullable=False)
    climate_controlled: Mapped[str] = mapped_column(
        String(3), nullable=False)  # 'yes'/'no'
    floor_level: Mapped[str] = mapped_column(String(50), nullable=False)
    security_features: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    rental_duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    tenant_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    shared_user_emails: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )

    # Relationships
    owner = relationship("UserModel", foreign_keys=[
                         user_id], back_populates="owned_units")
    tenant = relationship("UserModel", foreign_keys=[
                          tenant_id], back_populates="rented_units")

    # Constraints
    __table_args__ = (
        CheckConstraint('size_sqm > 0', name='positive_size'),
        CheckConstraint('rental_duration_days > 0', name='positive_duration'),
        CheckConstraint("climate_controlled IN ('yes', 'no')",
                        name='valid_climate_control')
    )
