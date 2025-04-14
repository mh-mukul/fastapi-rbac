from sqlalchemy.orm import Session

from src.permission.models import RolePermission, Module, Permission
from src.user.models import UserRole


def get_role_permissions(db: Session, role_ids: list[int]) -> dict[int, list[dict]]:
    query = (
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

    role_permissions = {}
    for perm in query:
        role_permissions.setdefault(perm.role_id, {}).setdefault(perm.module_id, {
            "module_id": perm.module_id,
            "module_name": perm.module_name,
            "permissions": [],
        })["permissions"].append({
            "permission_id": perm.permission_id,
            "permission_name": perm.permission_name,
        })

    return {rid: list(modules.values()) for rid, modules in role_permissions.items()}


def group_permissions_by_module(permissions_query):
    permissions_by_module = {}
    for perm in permissions_query:
        if perm.module_id not in permissions_by_module:
            permissions_by_module[perm.module_id] = {
                "module_id": perm.module_id,
                "module_name": perm.module_name,
                "permissions": [],
            }
        permissions_by_module[perm.module_id]["permissions"].append({
            "permission_id": perm.permission_id,
            "permission_name": perm.permission_name,
        })
    return list(permissions_by_module.values())


def format_role(role: UserRole, permissions: list[dict]):
    return {
        "id": role.id,
        "name": role.name,
        "is_active": role.is_active,
        "created_at": role.created_at,
        "updated_at": role.updated_at,
        "permissions": permissions,
    }
