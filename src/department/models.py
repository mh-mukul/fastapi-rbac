from sqlalchemy import Column, Integer, String

from src.models import AbstractBase


class Department(AbstractBase):
    __tablename__ = 'departments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)

    def __repr__(self):
        return f"{self.name}"
