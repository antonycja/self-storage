import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from os import getenv
from app.models.base import db
from app.models.user import UserModel


class AuthService:
    SECRET_KEY = getenv('SECRET')
    ALGORITHM = getenv('ALGORITHM', 'HS256')

    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def verify_password(stored_password: str, provided_password: str) -> bool:
        return bcrypt.checkpw(
            provided_password.encode('utf-8'),
            stored_password.encode('utf-8')
        )

    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        user = db.session.execute(
            db.select(UserModel).filter_by(email=email)
        ).scalar_one_or_none()

        if not user:
            return None

        return {
            "id": str(user.id),
            "name": user.name,
            "surname": user.surname,
            "email": user.email,
            "password": user.password
        }

    @staticmethod
    def generate_token(email: str) -> str:
        """Generate JWT token"""
        token = jwt.encode(
            {
                'email': email,
                'exp': datetime.utcnow() + timedelta(hours=24)
            },
            AuthService.SECRET_KEY,
            algorithm=AuthService.ALGORITHM
        )
        return token
