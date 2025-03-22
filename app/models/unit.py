from datetime import datetime
from app.models.base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, Integer, String, Float, JSON, Enum, ForeignKey, CheckConstraint, Numeric, Boolean
from typing import Optional, List
from app.models.enums import UnitStatus
# Add this import
from app.models.securityFeature import SecurityFeatureModel, SecurityFeatureType


class UnitModel(BaseModel):
    """Model for a Unit"""
    __tablename__ = "units"

    unit_id: Mapped[str] = mapped_column(String, primary_key=True)
    unit_name: Mapped[str] = mapped_column(String, nullable=False)
    country: Mapped[str] = mapped_column(String, nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False)
    address_link: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[UnitStatus] = mapped_column(
        Enum(UnitStatus), default=UnitStatus.VACANT)  # Update this line
    size_sqm: Mapped[float] = mapped_column(Float, nullable=False)
    # Keeping as string since that's your current setup
    monthly_rate: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(
        String, nullable=False, default="ZAR")
    climate_controlled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    floor_level: Mapped[str] = mapped_column(String(50), nullable=False)
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
    security_features: Mapped[List["SecurityFeatureModel"]] = relationship(
        "SecurityFeatureModel",
        back_populates="unit",
        cascade="all, delete-orphan"
    )
    owner = relationship("UserModel", foreign_keys=[
                         user_id], back_populates="owned_units")
    tenant = relationship("UserModel", foreign_keys=[
                          tenant_id], back_populates="rented_units")
    rentals = relationship("RentalModel", back_populates="unit")

    # Constraints
    __table_args__ = (
        CheckConstraint('size_sqm > 0', name='positive_size'),
        CheckConstraint('rental_duration_days > 0', name='positive_duration'),
        CheckConstraint('climate_controlled IN (0, 1)',
                        name='valid_climate_control')
    )

    @staticmethod
    def get_unit_status_enum():
        from app.models import UnitStatus
        return UnitStatus

    def calculate_security_premium(self) -> float:
        """Calculate price premium based on security features"""
        premium = 0.0
        for feature in self.security_features:
            if feature.feature_type in SecurityFeatureModel.get_premium_features():
                premium += 0.15
            elif feature.feature_type in SecurityFeatureModel.get_standard_features():
                premium += 0.10
        return premium
