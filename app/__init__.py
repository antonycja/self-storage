from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
from os import getenv
from app.models.base import db
from app.api.auth import auth_bp
from app.api.users import users_bp
from app.api.units import units_bp
from app.api.rentals import rentals_bp


def create_app(config_name=None):
    """Application factory function"""
    app = Flask(__name__)

    # Default configuration
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'your-secret-key'

    # Configure based on environment
    if config_name == 'testing':
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///storage.db'

    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)

    with app.app_context():
        # Create database tables
        db.create_all()

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(units_bp, url_prefix='/api/units')
    app.register_blueprint(rentals_bp, url_prefix='/api/rentals')

    return app
