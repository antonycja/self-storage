import pytest
from datetime import datetime, timezone
from functools import wraps
from flask import g
from app import create_app
from app.models.base import db
from app.models.user import UserModel
from app.models.unit import UnitModel
from app.models.rental import RentalModel
from app.services.auth_service import AuthService


def mock_token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        g.current_user = {
            'id': 1,
            'email': 'test@example.com',
            'name': 'Test User'
        }
        return f(*args, **kwargs)
    return decorated


@pytest.fixture
def app():
    app = create_app('testing')
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    # Mock the token_required decorator
    from app.api import rentals
    rentals.token_required = mock_token_required

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers():
    # This is just for consistency, our mock decorator ignores the token
    return {'Authorization': 'Bearer test-token'}


@pytest.fixture
def test_user(app):
    """Create a test user."""
    with app.app_context():
        user = UserModel(
            name="Test",
            surname="User",
            email="test@example.com",
            password=AuthService.hash_password("password123")
        )
        db.session.add(user)
        db.session.commit()
        yield user
        db.session.delete(user)
        db.session.commit()


@pytest.fixture
def test_unit(app, test_user):
    unit = UnitModel(
        unit_id='UNIT-001',
        unit_name='Test Unit',
        user_id=test_user.id,
        monthly_rate=1500.00,
        size_sqm=25.0,
        city='Test City',
        country='Test Country',
        address_link='https://maps.google.com/?q=Camps+Bay,Cape+Town',
        floor_level="ground",  # Add required field
        status='VACANT',
        currency='ZAR',
        climate_controlled=False,
        rental_duration_days=30
    )
    db.session.add(unit)
    db.session.commit()
    return unit


@pytest.fixture
def test_rental(app, test_user, test_unit):
    rental = RentalModel(
        unit_id=test_unit.unit_id,
        tenant_id=test_user.id,
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc).replace(month=12),
        monthly_rate=1500.00,
        status='active'
    )
    db.session.add(rental)
    db.session.commit()
    return rental
