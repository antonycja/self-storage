from datetime import datetime
from app.models.base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, Integer, String, Float, JSON, Enum, ForeignKey, CheckConstraint, Numeric
from typing import Optional
from app.models.enums import UnitStatus  # Add this import


class UnitModel(BaseModel):
    """Model for a Unit"""
    __tablename__ = "units"

    unit_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status: Mapped[UnitStatus] = mapped_column(
        Enum(UnitStatus), nullable=False)  # Update this line
    size_sqm: Mapped[float] = mapped_column(Float, nullable=False)
    # Keeping as string since that's your current setup
    monthly_rate: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    climate_controlled: Mapped[str] = mapped_column(
        String(3), nullable=False)  # 'yes'/'no'
    floor_level: Mapped[str] = mapped_column(String(50), nullable=False)
    security_features: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list)
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
    rentals = relationship("Rental", back_populates="unit")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('size_sqm > 0', name='positive_size'),
        CheckConstraint('rental_duration_days > 0', name='positive_duration'),
        CheckConstraint("climate_controlled IN ('yes', 'no')",
                        name='valid_climate_control')
    )

    @staticmethod
    def get_unit_status_enum():
        from app.models import UnitStatus
        return UnitStatus
