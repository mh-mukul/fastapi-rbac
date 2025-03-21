from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey

from config.database import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=True, unique=True)
    phone = Column(String(15), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey('user_roles.id'), nullable=True)
    department_id = Column(Integer, ForeignKey(
        'departments.id'), nullable=True)
    is_active = Column(Boolean(), nullable=False, default=True)
    is_deleted = Column(Boolean(), nullable=False, default=False)
    is_superuser = Column(Boolean(), nullable=False, default=False)
    created_at = Column(DateTime(6), default=datetime.now)
    updated_at = Column(DateTime(6), default=datetime.now)

    department = relationship("Department", backref="user_departments")
    role = relationship("UserRole", backref="user_roles")

    def soft_delete(self):
        self.is_active = False
        self.is_deleted = True
        self.updated_at = datetime.now()

    def __repr__(self):
        return f"{self.name}"


class UserRole(Base):
    __tablename__ = 'user_roles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    editable = Column(Boolean(), nullable=False, default=True)
    is_active = Column(Boolean(), nullable=False, default=True)
    is_deleted = Column(Boolean(), nullable=False, default=False)
    department_id = Column(Integer, ForeignKey(
        'departments.id'), nullable=False)
    created_at = Column(DateTime(6), default=datetime.now)
    updated_at = Column(DateTime(6), default=datetime.now)

    department = relationship("Department", backref="user_role_departments")

    def soft_delete(self):
        self.is_active = False
        self.is_deleted = True
        self.updated_at = datetime.now()

    def __repr__(self):
        return f"{self.name}"
