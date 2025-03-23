from datetime import datetime
from app.models.base import db
from app.models.token_blacklist import TokenBlackList
from sqlalchemy import delete


class TokenService:
    @staticmethod
    def blacklist_token(token: str, expires_at: datetime) -> None:
        """Add token to blacklist"""
        blacklisted_token = TokenBlackList(token=token, expires_at=expires_at)
        db.session.add(blacklisted_token)
        db.session.commit()

    @staticmethod
    def is_blacklisted(token: str) -> bool:
        """Check if token is blacklisted and not expired"""
        return db.session.query(TokenBlackList).filter(TokenBlackList.token == token, TokenBlackList.expires_at > datetime.utcnow()).first() is not None

    @staticmethod
    def cleanup_expired() -> None:
        """Remove expired tokens from blacklist"""
        db.session.execute(delete(TokenBlackList).where(
            TokenBlackList.expires_at <= datetime.utcnow()))
        db.session.commit()
