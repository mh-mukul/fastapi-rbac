from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean

from config.database import Base


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(6), default=datetime.now)
    updated_at = Column(DateTime(6), default=datetime.now)

    def __repr__(self):
        return f"{self.id}"


class UserToken(Base):
    __tablename__ = "user_tokens"
    id = Column(Integer, primary_key=True)
    token = Column(String(255), unique=True)
    created_at = Column(DateTime, default=datetime.now)
    expires_at = Column(DateTime)
    user_id = Column(Integer)
    jti = Column(String(255), unique=True)
    is_blacklisted = Column(Boolean, default=False)

    def __repr__(self):
        return f"{self.id}"
