from app.models.base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Float, ForeignKey, DateTime
from datetime import datetime
from typing import Optional


class Rental(BaseModel):
    __tablename__ = 'rentals'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    unit_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('units.unit_id'), nullable=False)
    tenant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('users.id'), nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    monthly_rate: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=datetime.utcnow)

    # Define relationship without backref
    unit = relationship("UnitModel")
    tenant = relationship("UserModel")
