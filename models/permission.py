from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, ForeignKey

from models.abstract import AbstractBase


class Module(AbstractBase):
    __tablename__ = 'modules'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)

    def __repr__(self):
        return f"{self.name}"


class Permission(AbstractBase):
    __tablename__ = 'permissions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    module_id = Column(Integer, ForeignKey('modules.id'), nullable=False)

    module = relationship("Module", backref="module_permissions")

    def __repr__(self):
        return f"{self.name}"


class RolePermission(AbstractBase):
    __tablename__ = 'user_role_permissions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey('user_roles.id'), nullable=False)
    permission_id = Column(Integer, ForeignKey(
        'permissions.id'), nullable=False)

    permission = relationship("Permission", backref="role_permissions")
    user_role = relationship("UserRole", backref="user_role_permissions")

    def __repr__(self):
        return f"{self.id}"
