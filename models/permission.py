from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey

from config.database import Base


class Module(Base):
    __tablename__ = 'modules'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    is_active = Column(Boolean(), nullable=False, default=True)
    is_deleted = Column(Boolean(), nullable=False, default=False)
    created_at = Column(DateTime(6), default=datetime.now())
    updated_at = Column(DateTime(6), default=datetime.now())

    def soft_delete(self):
        self.is_active = False
        self.is_deleted = True
        self.updated_at = datetime.now()

    def __repr__(self):
        return f"{self.name}"


class Permission(Base):
    __tablename__ = 'permissions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    module_id = Column(Integer, ForeignKey('modules.id'), nullable=False)
    is_active = Column(Boolean(), nullable=False, default=True)
    is_deleted = Column(Boolean(), nullable=False, default=False)
    created_at = Column(DateTime(6), default=datetime.now())
    updated_at = Column(DateTime(6), default=datetime.now())

    module = relationship("Module", backref="module_permissions")

    def soft_delete(self):
        self.is_active = False
        self.is_deleted = True
        self.updated_at = datetime.now()

    def __repr__(self):
        return f"{self.name}"


class RolePermission(Base):
    __tablename__ = 'user_role_permissions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey('user_roles.id'), nullable=False)
    permission_id = Column(Integer, ForeignKey(
        'permissions.id'), nullable=False)
    is_active = Column(Boolean(), nullable=False, default=True)
    is_deleted = Column(Boolean(), nullable=False, default=False)
    created_at = Column(DateTime(6), default=datetime.now)
    updated_at = Column(DateTime(6), default=datetime.now)

    permission = relationship("Permission", backref="role_permissions")
    user_role = relationship("UserRole", backref="user_role_permissions")

    def soft_delete(self):
        self.is_active = False
        self.is_deleted = True
        self.updated_at = datetime.now()

    def __repr__(self):
        return f"{self.id}"
