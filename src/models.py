from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import Column, DateTime, Boolean

from configs.database import Base


class AbstractBase(Base):
    __abstract__ = True

    is_active = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(6), default=datetime.now)
    updated_at = Column(DateTime(6), default=datetime.now)

    def soft_delete(self):
        self.is_active = False
        self.is_deleted = True
        self.updated_at = datetime.now()
        return self

    @classmethod
    def get_active(cls, db: Session):
        return db.query(cls).filter(cls.is_deleted == False)
