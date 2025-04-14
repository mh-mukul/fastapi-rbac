import uuid
from sqlalchemy.orm import Session
from fastapi import APIRouter, Request, Depends

from configs.database import get_db
from src.helpers import ResponseHelper
from src.auth.dependencies import get_current_user
from src.auth.utils import (
    create_access_token, create_refresh_token, verify_password, blacklist_token, decode_refresh_token, hash_password
)

from src.user.models import User
from src.auth.schemas import LoginSchema, RefreshTokenSchema, ResetPasswordSchema, LoginResponseSchema
from src.auth.services import get_user_permissions

router = APIRouter(prefix="/auth", tags=["Authentication"])
response = ResponseHelper()


@router.post("/login")
async def login(
    request: Request,
    data: LoginSchema,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.phone == data.phone).first()
    if not user or not verify_password(data.password, user.password):
        return response.error_response(401, message="Invalid credentials")
    if not user.is_active:
        return response.error_response(403, message="Inactive user")

    jti = str(uuid.uuid4())
    access_token = create_access_token(
        data={"user_id": user.id, "phone": user.phone}, jti=jti)
    refresh_token = create_refresh_token(
        db=db,
        data={"user_id": user.id, "phone": user.phone}, jti=jti)

    user_permissions = get_user_permissions(db, user)

    user_data = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "is_active": user.is_active,
        "role_id": user.role_id,
        "role_name": user.role.name if user.role else None,
        "department_id": user.department_id,
        "department_name": user.department.name if user.department else None,
    }
    resp_data = LoginResponseSchema(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user_data,
        permissions=user_permissions,
    )

    return response.success_response(200, 'success', resp_data)


@router.post("/refresh-token")
async def refresh_token(
    request: Request,
    data: RefreshTokenSchema,
    db: Session = Depends(get_db),
):
    """
    Refresh a token
    """
    payload = decode_refresh_token(db, data.refresh_token)
    access_token = create_access_token(
        data={"user_id": payload.get(
            "user_id"), "phone": payload.get("phone")},
        jti=payload.get("jti")
    )

    resp_data = {
        "access_token": access_token,
        "refresh_token": data.refresh_token
    }
    return response.success_response(200, 'success', resp_data)


@router.post("/logout")
async def logout(
    request: Request,
    data: RefreshTokenSchema,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Blacklist the token
    """
    blacklist_token(data.refresh_token, db)
    return response.success_response(200, 'success')


@router.post("/password-reset")
async def reset_password(
    request: Request,
    data: ResetPasswordSchema,
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
