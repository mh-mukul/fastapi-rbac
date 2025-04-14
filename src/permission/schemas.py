from datetime import datetime
from pydantic import BaseModel, Field


class ModuleBase(BaseModel):
    id: int = Field(..., gt=0)
    name: str = Field(..., max_length=100)

    class Config:
        from_attributes = True


class PermissionBase(BaseModel):
    id: int = Field(..., gt=0)


class PermissionGet(PermissionBase):
    name: str
    module: ModuleBase
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PermissionCreate(BaseModel):
    name: str = Field(..., min_length=5, max_length=100)
    module_id: int = Field(..., gt=0)


class PermissionUpdate(BaseModel):
    name: str = Field(..., min_length=5, max_length=100)
    module_id: int = Field(..., gt=0)
