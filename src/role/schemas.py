from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from src.schemas import Pagination


class PermissionSchema(BaseModel):
    permission_id: int
    permission_name: str


class ModulePermissionSchema(BaseModel):
    module_id: int
    module_name: str
    permissions: list[PermissionSchema]


class RoleBase(BaseModel):
    name: str = Field(..., max_length=100)


class RoleCreate(RoleBase):
    permission_ids: Optional[List[int]] = None


class RoleUpdate(RoleBase):
    permission_ids: Optional[List[int]] = None


class RoleGet(BaseModel):
    id: int
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    permissions: Optional[List[ModulePermissionSchema]] = None

    class Config:
        from_attributes = True


class RoleListResponse(BaseModel):
    pagination: Pagination
    roles: List[RoleGet]
