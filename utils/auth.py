import os
import jwt
import uuid
from fastapi import Request
from fastapi import Depends
from dotenv import load_dotenv
from typing import Optional, List
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta, timezone

from config.database import get_db
from handlers.custom_exceptions import JWTException, UnauthorizedException

from models.user import User
from models.auth import UserToken
from models.permission import Permission, RolePermission

load_dotenv()

SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.environ.get("JWT_ACCESS_TOKEN_EXPIRE_MINUTES",30))
REFRESH_TOKEN_EXPIRE_MINUTES = int(
    os.environ.get("JWT_REFRESH_TOKEN_EXPIRE_MINUTES", 60*24*7))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + \
            timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(db: Session, data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create a JWT refresh token.
    """
    to_encode = data.copy()
    jti = str(uuid.uuid4())
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + \
            timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "jti": jti, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    # Save the refresh token to the database
    user_token = UserToken(token=encoded_jwt, expires_at=expire,
                           user_id=to_encode.get("user_id"), jti=jti)
    db.add(user_token)
    db.commit()

    return encoded_jwt


def decode_access_token(db: Session, token: str) -> dict:
    """
    Decode a JWT and validate it.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise JWTException(401, "Invalid token type")
        return payload
    except jwt.ExpiredSignatureError:
        raise JWTException(401, "Token has expired")
    except jwt.InvalidTokenError:
        raise JWTException(401, "Invalid token")


def decode_refresh_token(db: Session, token: str) -> dict:
    """
    Decode a JWT and validate it.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        check_blacklist_token(token, db)
        if payload.get("type") != "refresh":
            raise JWTException(401, "Invalid token type")
        return payload
    except jwt.ExpiredSignatureError:
        raise JWTException(401, "Token has expired")
    except jwt.InvalidTokenError:
        raise JWTException(401, "Invalid token")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.headers.get("Authorization")
    if not token:
        raise JWTException(401, "Authorization token missing")

    token = token.split(" ")[1]  # Extract token part after "Bearer"
    try:
        payload = decode_access_token(db, token)
        user_id = payload.get('user_id')
        if not user_id:
            raise JWTException(401, "Invalid token")
    except jwt.PyJWTError:
        raise JWTException(401, "Could not validate credentials")

    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.is_deleted or not user.is_active:
        raise JWTException(401, "Invalid user")
    return user


def blacklist_token(token: str, db: Session):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise JWTException(401, "Invalid token")
    jti = payload.get("jti")
    check_blacklist_token(token, db)
    db_token = db.query(UserToken).filter(
        UserToken.jti == jti, UserToken.is_blacklisted == False).first()
    if db_token:
        db_token.is_blacklisted = True
        db.commit()
    else:
        raise JWTException(401, "Invalid token")


def check_blacklist_token(token: str, db: Session):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise JWTException(401, "Invalid token")
    jti = payload.get("jti")

    db_token = db.query(UserToken).filter(
        UserToken.jti == jti, UserToken.is_blacklisted == True).first()
    if db_token:
        raise JWTException(401, "Token has been blacklisted")
    else:
        return True


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
