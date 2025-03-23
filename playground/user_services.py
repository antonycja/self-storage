import bcrypt
from typing import Optional, Dict, Any
from app.models.base import db
from app.models.user import UserModel


class UserService():
    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def verify_password(hashed_password: str, password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

    @staticmethod
    def create_user(name: str, surname: str, email: str, password: str) -> Dict[str, Any]:
        user_exists = db.session.execute(
            db.select(UserModel).filter_by(email=email)
        ).scalar_one_or_none()

        if user_exists:
            return {"error": "User with this email already exists."}

        new_user = UserModel(
            name=name,
            surname=surname,
            email=email,
            password=UserService.hash_password(password)
        )

        db.session.add(new_user)
        db.session.commit()

        return UserService.sanitize_user_data(new_user)

    @staticmethod
    def update_user(user_id: int, old_password=None, new_password=None, **kwargs):
        user = db.session.execute(
            db.select(UserModel).filter_by(id=user_id)
        ).scalar_one_or_none()

        if not user:
            return {"error": "User not found."}

        # Handle general updates dynamically
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)

        # Secure password update
        if old_password and new_password:
            if not bcrypt.checkpw(old_password.encode('utf-8'), user.password.encode('utf-8')):
                return {"error": "Incorrect password"}
            user.password = bcrypt.hashpw(new_password.encode(
                'utf-8'), bcrypt.gensalt()).decode('utf-8')

        db.session.commit()
        return UserService.sanitize_user_data(user)

    @staticmethod
    def delete_user(user_id: int) -> Dict[str, str]:
        user = db.session.execute(
            db.select(UserModel).filter_by(id=user_id)
        ).scalar_one_or_none()

        if not user:
            return {"error": "User not found."}

        db.session.delete(user)
        db.session.commit()
        return {"success": "Account successfully deleted."}

    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        user = db.session.execute(
            db.select(UserModel).filter_by(email=email)
        ).scalar_one_or_none()

        if not user:
            return {"error": "User not found."}

        return {
            "id": str(user.id),
            "name": user.name,
            "surname": user.surname,
            "email": user.email,
            "password_hash": user.password
        }

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        user = db.session.execute(
            db.select(UserModel).filter_by(id=user_id)
        ).scalar_one_or_none()

        if not user:
            return {"error": "User not found."}

        return UserService.sanitize_user_data(user)

    @staticmethod
    def get_all_users():
        users = db.session.execute(db.select(UserModel).order_by(UserModel.name)).scalars()
        return users

    @staticmethod
    def sanitize_user_data(user: Any) -> Dict[str, Any]:
        if not user:
            return {"error": "Error trying to sanitize user information."}
        if isinstance(user, dict):
            return user
        return {
            "id": str(user.id),
            "name": user.name,
            "surname": user.surname,
            "email": user.email
        }
