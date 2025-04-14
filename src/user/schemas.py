from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from src.schemas import Pagination


class UserBase(BaseModel):
    name: str = Field(..., max_length=100)
    phone: str = Field(..., max_length=15)
    email: str = Field(..., max_length=100)
    is_active: bool = Field(default=True)


class UserCreate(UserBase):
    role_id: int
    password: str = Field(..., min_length=6, max_length=18)



class UserUpdate(UserBase):
    role_id: int


class RoleData(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class DepartmentData(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class UserGet(UserBase):
    id: int
    role: Optional[RoleData]
    department: Optional[DepartmentData]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    pagination: Pagination
    users: List[UserGet]
