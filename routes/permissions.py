from datetime import datetime
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from fastapi import APIRouter, Request, Depends

from config.database import get_db
from utils.helper import ResponseHelper
from utils.auth import get_current_user, has_role_permission

from models.user import User
from models.permission import Module, Permission, RolePermission

router = APIRouter()
response = ResponseHelper()


@router.get("/permissions")
async def get_permissions(
    request: Request,
    name: str = None,
    is_active: bool = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _: None = Depends(has_role_permission(["list_permission"])),
):
    # Base query with filtering logic
    query = (
        db.query(Permission, Module)
        .outerjoin(Module, Permission.module_id == Module.id)
        .filter(Permission.is_deleted == False, Module.is_deleted == False)
    )

    if not user.is_superuser:
        query = query.outerjoin(
            RolePermission,
            RolePermission.permission_id == Permission.id,
        ).filter(
            RolePermission.role_id == user.role_id,
            RolePermission.is_deleted == False,
        )

    # Apply dynamic filters
    if name:
        query = query.filter(Permission.name.ilike(f"%{name}%"))
    if is_active is not None:
        query = query.filter(Permission.is_active == is_active)

    # Fetch data
    results = query.order_by(Module.id.asc(), Permission.id.asc()).all()

    # Group permissions by module
    grouped_data = {}
    for permission, module in results:
        if module.name not in grouped_data:
            grouped_data[module.name] = {
                "module_id": module.id,
                "module_name": module.name,
                "permissions": [],
            }
        grouped_data[module.name]["permissions"].append(
            {
                "permission_id": permission.id,
                "permission_name": permission.name,
                "is_active": permission.is_active,
            }
        )

    # Convert grouped data to a list
    resp_data = list(grouped_data.values())

    return response.success_response(200, "success", resp_data)


@router.get("/permissions/{permission_id}")
async def get_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _: None = Depends(has_role_permission(["list_permission"])),
):
    query = db.query(Permission).filter(
        Permission.id == permission_id,
        Permission.is_deleted == False,
    )
    db_permission = query.first()
    if not db_permission:
        return response.error_response(404, "Permission not found")
    resp_data = {
        "id": db_permission.id,
        "name": db_permission.name,
        "is_active": db_permission.is_active,
        "module_id": db_permission.module_id,
        "module_name": db_permission.module.name if db_permission.module else None,
        "created_at": db_permission.created_at,
    }

    return response.success_response(200, "Success", resp_data)


class CreatePermissionBody(BaseModel):
    name: str = Field(..., min_length=5, max_length=100)


@router.post("/permissions")
async def create_permission(
    request: Request,
    data: CreatePermissionBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _: None = Depends(has_role_permission(["create_permission"])),
):
    if not user.is_superuser:
        return response.error_response(403, "Permission denied")
    # Check for duplicate permission by name
    if (
        db.query(Permission)
        .filter(
            Permission.name == data.name,
            Permission.is_deleted == False,
        ).first()
    ):
        return response.error_response(400, "Permission exists with this name")

    db_permission = Permission(
        name=data.name,
        department_id=user.department_id,
    )
    db.add(db_permission)
    db.commit()

    resp_data = {
        "id": db_permission.id,
        "name": db_permission.name,
        "created_at": db_permission.created_at,
        "module_id": db_permission.module_id,
        "module_name": db_permission.module.name if db_permission.module else None,
    }
    return response.success_response(201, "Permission created successfully", resp_data)


class UpdatePermissionBody(BaseModel):
    name: str = Field(..., min_length=5, max_length=100)


@router.put("/permissions/{permission_id}")
async def update_permission(
    permission_id: int,
    data: UpdatePermissionBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _: None = Depends(has_role_permission(["update_permission"])),
):
    if not user.is_superuser:
        return response.error_response(403, "Permission denied")
    # Check if the role exists
    query = db.query(Permission).filter(
        Permission.id == permission_id,
        Permission.is_deleted == False,
    )
    db_permission = query.first()
    if not db_permission:
        return response.error_response(404, "Permission not found")

    # Check for duplicate Permission by name (excluding the current Permission)
    if (
        db.query(Permission)
        .filter(
            Permission.name == data.name,
            Permission.id != permission_id,
            Permission.is_deleted == False,
        )
        .first()
    ):
        return response.error_response(400, "Permission exists with this name")

    # Update Permission fields
    db_permission.name = data.name
    db_permission.updated_at = datetime.now()

    db.commit()
    db.refresh(db_permission)

    resp_data = {
        "id": db_permission.id,
        "name": db_permission.name,
        "is_active": db_permission.is_active,
        "created_at": db_permission.created_at,
        "module_id": db_permission.module_id,
        "module_name": db_permission.module.name if db_permission.module else None,
    }
    return response.success_response(200, "Role updated successfully", resp_data)


@router.delete("/permissions/{permission_id}")
async def delete_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _: None = Depends(has_role_permission(["delete_permission"])),
):
    if not user.is_superuser:
        return response.error_response(403, "Permission denied")
    query = db.query(Permission).filter(
        Permission.id == permission_id,
        Permission.is_deleted == False,
    )
    db_permission = query.first()
    if not db_permission:
        return response.error_response(404, "Permission not found")
    db_permission.soft_delete()
    db.commit()

    return response.success_response(200, "Permission deleted successfully")
