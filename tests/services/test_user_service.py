import pytest
from app.services.user_service import UserService
from app.services.auth_service import AuthService
from app.models.user import UserModel
from app import db


class TestUserService:
    def test_create_user(self, app):
        """Test user creation with valid data."""
        with app.app_context():
            result = UserService.create_user(
                name="John",
                surname="Doe",
                email="john@example.com",
                password="password123"
            )

            assert "error" not in result
            assert result["name"] == "John"
            assert result["surname"] == "Doe"
            assert result["email"] == "john@example.com"
            assert "password" not in result

    def test_create_duplicate_user(self, app, test_user):
        """Test creating user with existing email."""
        with app.app_context():
            result = UserService.create_user(
                name="Another",
                surname="User",
                email=test_user.email,  # Using existing email
                password="password123"
            )

            assert "error" in result
            assert "already exists" in result["error"]

    def test_update_user(self, app, test_user):
        """Test updating user information."""
        with app.app_context():
            result = UserService.update_user(
                user_id=test_user.id,
                name="Updated",
                surname="Name"
            )

            assert "error" not in result
            assert result["name"] == "Updated"
            assert result["surname"] == "Name"
            assert result["email"] == test_user.email
    def test_update_user_password(self, app):
        """Test password update functionality."""
        with app.app_context():
            # First create user with known password
            initial_password = "initial123"
            new_user = UserModel(
                name="Test",
                surname="User",
                email="test.password@example.com",
                password=AuthService.hash_password(initial_password)
            )
            db.session.add(new_user)
            db.session.commit()

            # Try updating password
            result = UserService.update_user(
                user_id=new_user.id,
                old_password=initial_password,
                new_password="newpassword123"
            )

            assert "error" not in result
            # Verify new password works
            assert AuthService.verify_password(
                new_user.password, "newpassword123")

    def test_update_user_wrong_password(self, app, test_user):
        """Test password update with incorrect old password."""
        with app.app_context():
            result = UserService.update_user(
                user_id=test_user.id,
                old_password="wrongpassword",
                new_password="newpassword123"
            )

            assert "error" in result
            assert "Incorrect password" in result["error"]

    def test_get_user_by_id(self, app, test_user):
        """Test retrieving user by ID."""
        with app.app_context():
            result = UserService.get_user_by_id(test_user.id)

            assert result is not None
            assert result["id"] == str(test_user.id)
            assert result["email"] == test_user.email
            assert "password" not in result

    def test_get_nonexistent_user(self, app):
        """Test retrieving non-existent user."""
        with app.app_context():
            result = UserService.get_user_by_id(999)
            assert result is None

    def test_delete_user(self, app, test_user):
        """Test user deletion."""
        with app.app_context():
            result = UserService.delete_user(test_user.id)

            assert "success" in result
            assert UserService.get_user_by_id(test_user.id) is None

    def test_delete_nonexistent_user(self, app):
        """Test deleting non-existent user."""
        with app.app_context():
            result = UserService.delete_user(999)
            assert "error" in result
            assert "not found" in result["error"]

    def test_get_all_users(self, app, test_user):
        """Test retrieving all users."""
        with app.app_context():
            # Create additional user
            UserService.create_user(
                name="Another",
                surname="User",
                email="another@example.com",
                password="password123"
            )

            result = UserService.get_all_users()

            assert isinstance(result, list)
            assert len(result) >= 2
            for user in result:
                assert "id" in user
                assert "name" in user
                assert "email" in user
                assert "password" not in user

    def test_sanitize_user_data(self, app, test_user):
        """Test user data sanitization."""
        with app.app_context():
            result = UserService.sanitize_user_data(test_user)

            assert "id" in result
            assert "name" in result
            assert "email" in result
            assert "password" not in result
            assert isinstance(result["id"], str)
