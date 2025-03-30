from os import getenv
from datetime import timedelta


class Config:
    # Flask settings
    SECRET_KEY = getenv('SECRET', 'your-secret-key')

    # SQLAlchemy settings
    uri = getenv("DATABASE_URL")
    if uri and uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = uri or "sqlite:///storage.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT settings
    JWT_SECRET_KEY = getenv('JWT_SECRET_KEY', 'your-jwt-secret')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

    # Bcrypt settings
    BCRYPT_LOG_ROUNDS = 12
