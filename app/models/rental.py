from app.models.base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Float, ForeignKey, DateTime
from datetime import datetime
from typing import Optional


class Rental(BaseModel):
    __tablename__ = 'rentals'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    unit_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('units.unit_id'), nullable=False)  # Changed from 'units.id' to 'units.unit_id'
    tenant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('users.id'), nullable=False)
    start_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    monthly_rate: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default='active')
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=datetime.utcnow)

    # Relationships
    unit = relationship('UnitModel', backref='rentals')
    tenant = relationship('UserModel', backref='rentals')

    def __repr__(self):
        return f'<Rental {self.id} - Unit {self.unit_id} - Tenant {self.tenant_id}>'
