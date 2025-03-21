from app.models.base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, CheckConstraint
from flask_login import UserMixin

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
    rentals = relationship("Rental", back_populates="tenant")

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
