from app.models.base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Float, ForeignKey, DateTime
from datetime import datetime
from typing import Optional, List
import json


class RentalModel(BaseModel):
    __tablename__ = 'rentals'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    unit_id: Mapped[str] = mapped_column(
        String(20), ForeignKey('units.unit_id'), nullable=False)
    tenant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('users.id'), nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    monthly_rate: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    total_cost: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,  # Add default value
        server_default='0.0'  # Add server default
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=datetime.utcnow)
    shared_user_emails: Mapped[str] = mapped_column(
        String,
        nullable=True,
        default='[]'
    )  # Store as JSON string

    # Relationships
    unit = relationship("UnitModel")
    tenant = relationship("UserModel")

    def calculate_total_cost(self) -> float:
        """Calculate total cost for rental period"""
        if not self.start_date or not self.end_date:
            return 0.0

        days = (self.end_date - self.start_date).days
        months = days / 30.0  # Approximate months
        return round(self.monthly_rate * months, 2)

    def add_shared_user(self, email: str) -> bool:
        """Add a user to shared users list"""
        try:
            shared_users = json.loads(self.shared_user_emails or '[]')
            if not shared_users:
                shared_users = []

            if email not in shared_users:
                shared_users.append(email)
                self.shared_user_emails = json.dumps(shared_users)
                return True
            return False
        except json.JSONDecodeError:
            self.shared_user_emails = json.dumps([email])
            return True

    def remove_shared_user(self, email: str) -> bool:
        """Remove a shared user email"""
        try:
            shared_users = json.loads(self.shared_user_emails or '[]')
            if email in shared_users:
                shared_users.remove(email)
                self.shared_user_emails = json.dumps(shared_users)
                return True
            return False
        except Exception:
            return False
