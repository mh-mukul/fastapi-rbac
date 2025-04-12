from typing import List
from datetime import datetime
from pydantic import BaseModel, Field

from schemas.abstract import Pagination


class DepartmentBase(BaseModel):
    name: str = Field(..., max_length=100)


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(DepartmentBase):
    pass


class DepartmentGet(DepartmentBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DepartmentListResponse(BaseModel):
    pagination: Pagination
    departments: List[DepartmentGet]
