from typing import Optional, Dict, Any, List
from app.models.base import db
from app.models.user import UserModel
from .auth_service import AuthService


class UserService:
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
            password=AuthService.hash_password(password)
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

        # Handle general updates
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)

        # Handle password update
        if old_password and new_password:
            if not AuthService.verify_password(user.password, old_password):
                return {"error": "Incorrect password"}
            user.password = AuthService.hash_password(new_password)

        db.session.commit()
        return UserService.sanitize_user_data(user)

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        user = db.session.execute(
            db.select(UserModel).filter_by(id=user_id)
        ).scalar_one_or_none()

        if not user:
            return None

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
    def get_all_users() -> List[Dict[str, Any]]:
        users = db.session.execute(
            db.select(UserModel).order_by(UserModel.name)
        ).scalars().all()
        return [UserService.sanitize_user_data(user) for user in users]

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
