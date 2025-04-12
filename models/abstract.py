from datetime import datetime
from sqlalchemy import Column, DateTime, Boolean

from config.database import Base


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
