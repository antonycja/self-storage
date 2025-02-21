from flask import Flask
from dotenv import load_dotenv
from os import getenv
from app.models import db

def create_app():
    load_dotenv()
    
    app = Flask(__name__)
    app.secret_key = getenv("SECRET")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///storage.db"
    
    # Initialize the database
    db.init_app(app)
    
    # Create all database tables
    with app.app_context():
        db.create_all()
    
    # Import routes here to avoid circular imports
    from app.routes import register_routes
    register_routes(app)
    
    return app