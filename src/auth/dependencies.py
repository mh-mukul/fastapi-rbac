import jwt
from typing import List
from sqlalchemy.orm import Session
from fastapi import Depends, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.security import OAuth2PasswordBearer

from configs.database import get_db
from src.auth.utils import decode_access_token
from src.auth.exceptions import APIKeyException, JWTException, UnauthorizedException

from src.user.models import User
from src.auth.models import ApiKey
from src.permission.models import Permission, RolePermission


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


async def get_api_key(
    api_key: str = Security(api_key_header),
    db: Session = Depends(get_db)
):
    if api_key is None:
        raise APIKeyException(
            status=401, message="Authorization header missing")

    token = api_key.replace("Bearer ", "")
    api_key_obj = db.query(ApiKey).filter(
        ApiKey.key == token,
        ApiKey.is_active == True,
        ApiKey.is_deleted == False
    ).first()

    if not api_key_obj:
        raise APIKeyException(status=403, message="Invalid API Key")

    return api_key_obj


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = decode_access_token(db, token)
        user_id = payload.get('user_id')
        if not user_id:
            raise JWTException(401, message="Invalid token")
    except jwt.PyJWTError:
        raise JWTException(
            401, message="Could not validate credentials")

    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.is_deleted or not user.is_active:
        raise JWTException(401, message="Invalid user")
    return user


def has_role_permission(required_permissions: List[str]):
    async def dependency(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        # Check if the user is a superuser
        if current_user.is_superuser:
            return  # Bypass permission checks for superusers

        # Fetch user's role permissions
        user_permissions = (
            db.query(Permission.name)
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .filter(RolePermission.role_id == current_user.role_id, RolePermission.is_deleted == False)
            .all()
        )
        user_permissions = [perm.name for perm in user_permissions]

        # Check if the user has the required permissions
        if not any(perm in user_permissions for perm in required_permissions):
            raise UnauthorizedException(403, "Permission denied")
    return dependency
