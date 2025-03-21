from datetime import datetime
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from fastapi import APIRouter, Request, Depends

from config.logger import logger
from config.database import get_db
from utils.helper import ResponseHelper
from utils.auth import get_current_user, has_role_permission

from models.user import User, UserRole
from models.permission import Module, Permission, RolePermission

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
    # Base query for UserRole
    base_query = db.query(UserRole).filter(UserRole.is_deleted == False)

    if not user.is_superuser:
        base_query = base_query.filter(
            UserRole.department_id == user.department_id)

    # Apply filters
    if name:
        base_query = base_query.filter(UserRole.name.ilike(f"%{name}%"))
    if is_active is not None:
        base_query = base_query.filter(UserRole.is_active == is_active)

    # Total records for pagination
    total_records = base_query.count()
    total_pages = (total_records + limit - 1) // limit
    offset = (page - 1) * limit

    # Paginate UserRole records
    paginated_roles = (
        base_query
        .order_by(UserRole.id.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    # Get IDs of paginated UserRole records
    role_ids = [role.id for role in paginated_roles]

    # Fetch RolePermission and related data for the paginated roles
    permissions_query = (
        db.query(
            RolePermission.role_id,
            RolePermission.is_deleted,
            Module.id.label("module_id"),
            Module.name.label("module_name"),
            Permission.id.label("permission_id"),
            Permission.name.label("permission_name"),
        )
        .outerjoin(Permission, RolePermission.permission_id == Permission.id)
        .outerjoin(Module, Permission.module_id == Module.id)
        .filter(RolePermission.role_id.in_(role_ids))
        .filter(RolePermission.is_deleted == False)
        .order_by(Module.id.asc(), Permission.id.asc())
        .all()
    )

    # Organize permissions by role ID
    permissions_by_role = {}
    for perm in permissions_query:
        if perm.role_id not in permissions_by_role:
            permissions_by_role[perm.role_id] = {}
        if perm.module_id not in permissions_by_role[perm.role_id]:
            permissions_by_role[perm.role_id][perm.module_id] = {
                "module_id": perm.module_id,
                "module_name": perm.module_name,
                "permissions": [],
            }
        permissions_by_role[perm.role_id][perm.module_id]["permissions"].append({
            "permission_id": perm.permission_id,
            "permission_name": perm.permission_name,
        })

    # Format the final response
    formatted_data = []
    for role in paginated_roles:
        formatted_data.append({
            "role_id": role.id,
            "role_name": role.name,
            "is_active": role.is_active,
            "created_at": role.created_at,
            "permissions": list(permissions_by_role.get(role.id, {}).values()),
        })

    # Generate pagination URLs
    base_url = str(request.url.path)
    previous_page_url = f"{base_url}?page={page - 1}&limit={limit}" if page > 1 else None
    next_page_url = f"{base_url}?page={page + 1}&limit={limit}" if page < total_pages else None

    # Prepare the final response
    response_data = {
        "data": {
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_records": total_records,
                "previous_page_url": previous_page_url,
                "next_page_url": next_page_url,
                "record_per_page": limit,
            },
            "role_list": formatted_data,
        }
    }

    return response.success_response(200, "success", data=response_data)


@router.get("/roles/{role_id}")
async def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _: None = Depends(has_role_permission(["list_role"])),
):
    # Base query for roles
    query = db.query(UserRole).filter(UserRole.is_deleted == False)

    if not user.is_superuser:
        query = query.filter(UserRole.department_id == user.department_id)

    # Query to fetch the role along with its permissions
    role_with_permissions = (
        query
        .outerjoin(
            RolePermission,
            (RolePermission.role_id == UserRole.id) & (
                RolePermission.is_deleted == False)
        )
        .outerjoin(Permission, RolePermission.permission_id == Permission.id)
        .outerjoin(Module, Permission.module_id == Module.id)
        .filter(UserRole.id == role_id)
        .with_entities(
            UserRole.id.label("role_id"),
            UserRole.name.label("role_name"),
            UserRole.is_active,
            UserRole.created_at,
            Module.id.label("module_id"),
            Module.name.label("module_name"),
            Permission.id.label("permission_id"),
            Permission.name.label("permission_name"),
        )
        .order_by(Module.id.asc(), Permission.id.asc())
        .all()
    )

    if not role_with_permissions:
        return response.error_response(404, "Role not found")

    # Group data by role and organize permissions by module
    role_data = None
    module_dict = {}

    for row in role_with_permissions:
        if role_data is None:
            role_data = {
                "id": row.role_id,
                "name": row.role_name,
                "is_active": row.is_active,
                "created_at": row.created_at,
                "permissions": [],
            }

        if row.module_id:
            if row.module_id not in module_dict:
                module_dict[row.module_id] = {
                    "module_id": row.module_id,
                    "module_name": row.module_name,
                    "permissions": [],
                }
            if row.permission_id:
                module_dict[row.module_id]["permissions"].append({
                    "permission_id": row.permission_id,
                    "permission_name": row.permission_name,
                })

    # Add modules and permissions to the role data
    role_data["permissions"] = list(module_dict.values())

    # Return the response
    return response.success_response(200, "Success", role_data)


class CreateRoleBody(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    permission_ids: list[int] = None


@router.post("/roles")
async def create_role(
    request: Request,
    data: CreateRoleBody,
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

    db_role = UserRole(
        name=data.name,
        department_id=user.department_id,
    )
    db.add(db_role)
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
            new_permissions = [(RolePermission(role_id=db_role.id, permission_id=permission_id))
                               for permission_id in data.permission_ids]
            db.bulk_save_objects(new_permissions)
        except Exception as e:
            logger.error(f"Error creating Role: {e}")
            db.rollback()
            return response.error_response(500, "Error creating Role")
    db.commit()

    resp_data = {
        "id": db_role.id,
        "name": db_role.name,
        "created_at": db_role.created_at,
    }
    return response.success_response(201, "Role created successfully", resp_data)


class UpdateRoleBody(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    permission_ids: list[int] = None


@router.put("/roles/{role_id}")
async def update_role(
    role_id: int,
    data: UpdateRoleBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _: None = Depends(has_role_permission(["update_role"])),
):
    # Check if the role exists
    query = db.query(UserRole).filter(
        UserRole.id == role_id,
        UserRole.is_deleted == False,
        UserRole.department_id == user.department_id,
    )
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
            db.query(RolePermission).filter(
                RolePermission.role_id == role_id,
                RolePermission.is_deleted == False
            ).update({RolePermission.is_deleted: True, RolePermission.updated_at: datetime.now()})

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

    resp_data = {
        "id": db_role.id,
        "name": db_role.name,
        "is_active": db_role.is_active,
        "created_at": db_role.created_at,
    }
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
        db.query(RolePermission).filter(
            RolePermission.role_id == role_id,
            RolePermission.is_deleted == False
        ).update({RolePermission.is_active: False, RolePermission.is_deleted: True, RolePermission.updated_at: datetime.now()})
    except Exception as e:
        logger.error(f"Error deleting Role: {e}")
        db.rollback()
        return response.error_response(500, "Error deleting Role")
    db.commit()

    return response.success_response(200, "Role deleted successfully")
