from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from fastapi import APIRouter, Request, Depends

from config.database import get_db
from utils.helper import ResponseHelper
from utils.auth import (
    create_access_token, create_refresh_token, verify_password,
    get_current_user, blacklist_token, decode_refresh_token, hash_password
)

from models.user import User
from models.permission import Permission, Module, RolePermission

router = APIRouter()
response = ResponseHelper()


class LoginBody(BaseModel):
    phone: str = Field(..., min_length=3, max_length=15)
    password: str = Field(..., min_length=4, max_length=18)


@router.post("/auth/login")
async def login(
    request: Request,
    data: LoginBody,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.phone == data.phone).first()
    if not user or not verify_password(data.password, user.password):
        return response.error_response(401, message="Invalid credentials")
    if not user.is_active:
        return response.error_response(403, message="Inactive user")

    access_token = create_access_token(
        {"user_id": user.id, "phone": user.phone})
    refresh_token = create_refresh_token(
        db,
        {"user_id": user.id, "phone": user.phone})

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

    resp_data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "role_id": user.role_id,
            "role_name": user.role.name if user.role else None,
            "is_active": user.is_active,
            "department_id": user.department_id,
            "department_name": user.department.name if user.department else None,
        },
        "permissions": permissions_response
    }
    return response.success_response(200, 'success', resp_data)


class RefreshTokenBody(BaseModel):
    refresh_token: str = Field(..., min_length=3, max_length=255)


@router.post("/auth/refresh-token")
async def refresh_token(
    request: Request,
    data: RefreshTokenBody,
    db: Session = Depends(get_db),
):
    """
    Refresh a token
    """
    payload = decode_refresh_token(db, data.refresh_token)
    access_token = create_access_token(
        {"user_id": payload.get("user_id"), "phone": payload.get("phone")}
    )

    resp_data = {
        "access_token": access_token,
        "refresh_token": data.refresh_token
    }
    return response.success_response(200, 'success', resp_data)


@router.post("/auth/logout")
async def logout(
    request: Request,
    data: RefreshTokenBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Blacklist the token
    """
    blacklist_token(data.refresh_token, db)
    return response.success_response(200, 'success')


class ResetPasswordBody(BaseModel):
    current_password: str = Field(..., min_length=6, max_length=18)
    new_password: str = Field(..., min_length=6, max_length=18)


@router.post("/auth/password-reset")
async def reset_password(
    request: Request,
    data: ResetPasswordBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Reset Users Password
    """
    if not verify_password(data.current_password, user.password):
        return response.error_response(400, message="Current password did not matched!")
    new_password = hash_password(data.new_password)

    user.password = new_password
    db.commit()

    return response.success_response(200, 'success')
