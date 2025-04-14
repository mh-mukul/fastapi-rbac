from sqlalchemy.orm import Session

from src.permission.models import Permission, Module, RolePermission
from src.user.models import User


def get_user_permissions(db: Session, user: User):
    # Fetch permissions based on the user's role
    permissions_query = (
        db.query(Permission, Module)
        .join(Module, Permission.module_id == Module.id)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .filter(
            Permission.is_deleted == False,
            Module.is_deleted == False,
            RolePermission.role_id == user.role_id
        )
        .order_by(Module.id.asc(), Permission.id.asc())
    )

    # Group permissions by module
    permissions_by_module = {}
    for permission, module in permissions_query.all():
        if module.id not in permissions_by_module:
            permissions_by_module[module.id] = {
                "module_name": module.name,
                "permissions": [],
            }
        permissions_by_module[module.id]["permissions"].append(permission.name)

    # Prepare permissions response
    permissions_response = list(permissions_by_module.values())

    return permissions_response
