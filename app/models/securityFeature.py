from enum import Enum
from app.models.base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, ForeignKey, Enum as SQLEnum


class SecurityFeatureType(Enum):
    """Standardized security feature types"""
    BASIC = "Basic Lock and Key"
    CCTV = "CCTV Surveillance"
    GUARDS = "24/7 Security Guards"
    BIOMETRIC = "Biometric Access"
    MOTION = "Motion Sensors"
    ALARM = "Individual Alarms"
    FIRE = "Fire Detection System"
    ACCESS = "Access Control System"


class SecurityFeatureModel(BaseModel):
    __tablename__ = "security_features"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    feature_type: Mapped[SecurityFeatureType] = mapped_column(
        SQLEnum(SecurityFeatureType),
        nullable=False
    )
    unit_id: Mapped[str] = mapped_column(
        String,
        ForeignKey('units.unit_id', ondelete='CASCADE'),
        nullable=False
    )

    # Add additional feature-specific fields if needed
    notes: Mapped[str] = mapped_column(String(200), nullable=True)

    # Relationship with Unit
    unit = relationship("UnitModel", back_populates="security_features")

    @property
    def feature_name(self) -> str:
        return self.feature_type.value

    @classmethod
    def get_premium_features(cls) -> list[SecurityFeatureType]:
        """Return list of premium security features"""
        return [
            SecurityFeatureType.BIOMETRIC,
            SecurityFeatureType.GUARDS
        ]

    @classmethod
    def get_standard_features(cls) -> list[SecurityFeatureType]:
        """Return list of standard security features"""
        return [
            SecurityFeatureType.CCTV,
            SecurityFeatureType.ACCESS
        ]
