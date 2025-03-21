from flask import Flask
from dotenv import load_dotenv
from os import getenv
from app.models.base import db
from app.api.auth import auth_bp
from app.api.users import users_bp
from app.api.units import units_bp


def create_app():
    load_dotenv()

    app = Flask(__name__)
    app.config.from_object('config.Config')

    # Initialize extensions
    db.init_app(app)

    with app.app_context():
        # Create database tables
        db.create_all()

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(units_bp, url_prefix='/api/units')

    return app
