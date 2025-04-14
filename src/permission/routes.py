from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import APIRouter, Request, Depends

from configs.database import get_db
from src.helpers import ResponseHelper
from src.auth.dependencies import get_current_user, has_role_permission

from src.user.models import User
from src.permission.models import Module, Permission, RolePermission
from src.permission.schemas import PermissionGet, PermissionCreate, PermissionUpdate

router = APIRouter(prefix="/permissions", tags=["Permissions"])
response = ResponseHelper()


@router.get("")
async def get_permissions(
    request: Request,
    name: str = None,
    is_active: bool = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _: None = Depends(has_role_permission(["list_permission"])),
):
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

    if name:
        query = query.filter(Permission.name.ilike(f"%{name}%"))
    if is_active is not None:
        query = query.filter(Permission.is_active == is_active)

    results = query.order_by(Module.id.asc(), Permission.id.asc()).all()

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

    resp_data = list(grouped_data.values())

    return response.success_response(200, "success", resp_data)


@router.get("/{permission_id}")
async def get_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _: None = Depends(has_role_permission(["list_permission"])),
):
    permission = Permission.get_active(db).filter(
        Permission.id == permission_id
    ).first()

    if not permission:
        return response.error_response(404, "Permission not found")

    resp_data = PermissionGet.model_validate(permission)

    return response.success_response(200, "Success", resp_data)


@router.post("")
async def create_permission(
    request: Request,
    data: PermissionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _: None = Depends(has_role_permission(["create_permission"])),
):
    if not user.is_superuser:
        return response.error_response(403, "Permission denied")

    if (
        Permission.get_active(db)
        .filter(
            Permission.name == data.name
        ).first()
    ):
        return response.error_response(400, "Permission exists with this name")

    new_permission = Permission(
        name=data.name,
        module_id=data.module_id,
    )
    db.add(new_permission)
    db.commit()

    resp_data = PermissionGet.model_validate(new_permission)

    return response.success_response(201, "Permission created successfully", resp_data)


@router.put("/{permission_id}")
async def update_permission(
    permission_id: int,
    data: PermissionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _: None = Depends(has_role_permission(["update_permission"])),
):
    if not user.is_superuser:
        return response.error_response(403, "Permission denied")

    query = db.query(Permission).filter(
        Permission.id == permission_id,
        Permission.is_deleted == False,
    )
    permission = query.first()
    if not permission:
        return response.error_response(404, "Permission not found")

    if (
        Permission.get_active(db)
        .filter(
            Permission.name == data.name,
            Permission.id != permission_id
        )
        .first()
    ):
        return response.error_response(400, "Permission exists with this name")

    permission.name = data.name
    permission.module_id = data.module_id
    permission.updated_at = datetime.now()

    db.commit()
    db.refresh(permission)

    resp_data = PermissionGet.model_validate(permission)

    return response.success_response(200, "Permission updated successfully", resp_data)


@router.delete("/{permission_id}")
async def delete_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _: None = Depends(has_role_permission(["delete_permission"])),
):
    if not user.is_superuser:
        return response.error_response(403, "Permission denied")
    permission = Permission.get_active(db).filter(
        Permission.id == permission_id
    ).first()
    if not permission:
        return response.error_response(404, "Permission not found")
    permission.soft_delete()
    db.commit()

    return response.success_response(200, "Permission deleted successfully")
