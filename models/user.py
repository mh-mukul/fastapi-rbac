from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey

from models.abstract import AbstractBase


class User(AbstractBase):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=True, unique=True)
    phone = Column(String(15), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey('user_roles.id'), nullable=True)
    department_id = Column(Integer, ForeignKey(
        'departments.id'), nullable=True)
    is_superuser = Column(Boolean(), nullable=False, default=False)

    department = relationship("Department", backref="user_departments")
    role = relationship("UserRole", backref="user_roles")

    def __repr__(self):
        return f"{self.name}"


class UserRole(AbstractBase):
    __tablename__ = 'user_roles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    editable = Column(Boolean(), nullable=False, default=True)
    department_id = Column(Integer, ForeignKey(
        'departments.id'), nullable=False)

    department = relationship("Department", backref="user_role_departments")

    def __repr__(self):
        return f"{self.name}"
