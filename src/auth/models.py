from sqlalchemy import Column, Integer, String, DateTime, Boolean

from src.models import AbstractBase


class ApiKey(AbstractBase):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(255), nullable=False)

    def __repr__(self):
        return f"{self.id}"


class UserToken(AbstractBase):
    __tablename__ = "user_tokens"
    
    id = Column(Integer, primary_key=True)
    token = Column(String(255), unique=True)
    expires_at = Column(DateTime)
    user_id = Column(Integer)
    jti = Column(String(255), unique=True)
    is_blacklisted = Column(Boolean, default=False)

    def __repr__(self):
        return f"{self.id}"
