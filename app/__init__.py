from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
import os
from app.models.base import db
from app.api.auth import auth_bp
from app.api.users import users_bp
from app.api.units import units_bp
from app.api.rentals import rentals_bp


def create_app(config_name=None):
    """Application factory function"""
    app = Flask(__name__)

    # Load environment variables
    load_dotenv()

    # Default configuration
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key')

    # Configure database
    if config_name == 'testing':
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    else:
        # Get DATABASE_URL from environment (provided by Render)
        database_url = os.getenv('DATABASE_URL')
        if (database_url and database_url.startswith("postgres://")):
            database_url = database_url.replace(
                "postgres://", "postgresql://", 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///storage.db'

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

    @app.route('/api/health')
    def health_check():
        return {"status": "healthy"}, 200

    return app
