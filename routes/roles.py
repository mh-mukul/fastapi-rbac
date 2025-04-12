from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import APIRouter, Request, Depends

from config.logger import logger
from config.database import get_db
from utils.helper import ResponseHelper
from utils.auth import get_current_user, has_role_permission

from models import User, UserRole, RolePermission
from schemas.abstract import Pagination
from schemas.role import RoleGet, RoleListResponse, RoleCreate, RoleUpdate
from services.role_service import get_role_permissions, format_role

router = APIRouter()
response = ResponseHelper()


@router.get("/roles")
async def get_roles(
    request: Request,
    page: int = 1,
    limit: int = 10,
    name: str = None,
    is_active: bool = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _: None = Depends(has_role_permission(["list_role"])),
):
    query = UserRole.get_active(db)
    if not user.is_superuser:
        query = query.filter(UserRole.department_id == user.department_id)
    if name:
        query = query.filter(UserRole.name.ilike(f"%{name}%"))
    if is_active is not None:
        query = query.filter(UserRole.is_active == is_active)

    roles, total = response.paginate_query(query, page, limit)
    role_ids = [r.id for r in roles]
    permissions_map = get_role_permissions(db, role_ids)

    formatted_roles = [
        RoleGet.model_validate(format_role(
            role, permissions_map.get(role.id, [])))
        for role in roles
    ]

    pagination = Pagination(
        current_page=page,
        total_pages=(total + limit - 1) // limit,
        total_records=total,
        record_per_page=limit,
        previous_page_url=f"{request.url.path}?page={page - 1}&limit={limit}" if page > 1 else None,
        next_page_url=f"{request.url.path}?page={page + 1}&limit={limit}" if (
            page * limit) < total else None,
    )

    return response.success_response(200, "success", RoleListResponse(pagination=pagination, roles=formatted_roles))


@router.get("/roles/{role_id}")
async def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _: None = Depends(has_role_permission(["list_role"])),
):
    query = UserRole.get_active(db).filter(UserRole.id == role_id)

    if not user.is_superuser:
        query = query.filter(UserRole.department_id == user.department_id)

    role = query.first()

    if not role:
        return response.error_response(404, "Role not found")

    permissions_map = get_role_permissions(db, [role.id])
    formatted_role = format_role(role, permissions_map.get(role.id, []))

    resp_data = RoleGet.model_validate(formatted_role)

    return response.success_response(200, "Success", resp_data)


@router.post("/roles")
async def create_role(
    request: Request,
    data: RoleCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _: None = Depends(has_role_permission(["create_role"])),
):
    # Check for duplicate role by name
    if (
        db.query(UserRole)
        .filter(
            UserRole.name == data.name,
            UserRole.department_id == user.department_id,
            UserRole.is_deleted == False,
        ).first()
    ):
        return response.error_response(400, "UserRole exists with this name")

    new_role = UserRole(
        name=data.name,
        department_id=user.department_id,
    )
    db.add(new_role)
    db.flush()
    if data.permission_ids:
        user_permissions = db.query(RolePermission.permission_id).filter(
            RolePermission.role_id == user.role_id
        ).all()
        user_permissions = [
            permission.permission_id for permission in user_permissions]
        if not set(data.permission_ids).issubset(set(user_permissions)):
            return response.error_response(403, "Permission denied")
        try:
            # Add permissions to the role
            new_permissions = [(RolePermission(role_id=new_role.id, permission_id=permission_id))
                               for permission_id in data.permission_ids]
            db.bulk_save_objects(new_permissions)
        except Exception as e:
            logger.error(f"Error creating Role: {e}")
            db.rollback()
            return response.error_response(500, "Error creating Role")
    db.commit()
    db.refresh(new_role)

    permissions_map = get_role_permissions(db, [new_role.id])
    formatted_role = format_role(
        new_role, permissions_map.get(new_role.id, []))

    resp_data = RoleGet.model_validate(formatted_role)

    return response.success_response(201, "Role created successfully", resp_data)


@router.put("/roles/{role_id}")
async def update_role(
    role_id: int,
    data: RoleUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _: None = Depends(has_role_permission(["update_role"])),
):
    query = UserRole.get_active(db).filter(UserRole.id == role_id)
    if not user.is_superuser:
        query = query.filter(UserRole.department_id == user.department_id)
    db_role = query.first()
    if not db_role:
        return response.error_response(404, "Role not found")

    # Check for duplicate UserRole by name (excluding the current UserRole)
    if (
        db.query(UserRole)
        .filter(
            UserRole.name == data.name,
            UserRole.id != role_id,
            UserRole.is_deleted == False,
            UserRole.department_id == user.department_id,
        )
        .first()
    ):
        return response.error_response(400, "Role exists with this name")

    # Update UserRole fields
    db_role.name = data.name
    db_role.updated_at = datetime.now()

    if not data.permission_ids:
        # Delete existing permissions
        db.query(RolePermission).filter(
            RolePermission.role_id == role_id,
            RolePermission.is_deleted == False
        ).update({RolePermission.is_active: False, RolePermission.is_deleted: True, RolePermission.updated_at: datetime.now()})

    else:
        user_permissions = db.query(RolePermission.permission_id).filter(
            RolePermission.role_id == user.role_id
        ).all()
        user_permissions = [
            permission.permission_id for permission in user_permissions]
        if not set(data.permission_ids).issubset(set(user_permissions)):
            return response.error_response(403, "Permission denied")

        try:
            # Delete existing permissions
            RolePermission.get_active(db).filter(
                RolePermission.role_id == role_id
            ).update(
                {RolePermission.is_active: False, RolePermission.is_deleted: True,
                    RolePermission.updated_at: datetime.now()}
            )

            # Add new permissions
            new_permissions = [(RolePermission(role_id=role_id, permission_id=permission_id))
                               for permission_id in data.permission_ids]
            db.bulk_save_objects(new_permissions)
        except Exception as e:
            logger.error(f"Error updating Role: {e}")
            db.rollback()
            return response.error_response(500, "Error updating Role")
    db.commit()
    db.refresh(db_role)

    permissions_map = get_role_permissions(db, [db_role.id])
    formatted_role = format_role(db_role, permissions_map.get(db_role.id, []))
    resp_data = RoleGet.model_validate(formatted_role)
    return response.success_response(200, "Role updated successfully", resp_data)


@router.delete("/roles/{role_id}")
async def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _: None = Depends(has_role_permission(["delete_role"])),
):
    query = db.query(UserRole).filter(
        UserRole.id == role_id,
        UserRole.is_deleted == False,
    )
    if not user.is_superuser:
        query = query.filter(UserRole.department_id == user.department_id)
    db_role = query.first()
    if not db_role:
        return response.error_response(404, "Role not found")
    try:
        db_role.soft_delete()
        # Delete existing permissions
        RolePermission.get_active(db).filter(
            RolePermission.role_id == role_id,
        ).update({RolePermission.is_active: False, RolePermission.is_deleted: True, RolePermission.updated_at: datetime.now()})
    except Exception as e:
        logger.error(f"Error deleting Role: {e}")
        db.rollback()
        return response.error_response(500, "Error deleting Role")
    db.commit()

    return response.success_response(200, "Role deleted successfully")
