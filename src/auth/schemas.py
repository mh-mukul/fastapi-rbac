from typing import List, Optional
from pydantic import BaseModel, Field


class LoginSchema(BaseModel):
    phone: str = Field(..., min_length=3, max_length=15)
    password: str = Field(..., min_length=4, max_length=18)


class RefreshTokenSchema(BaseModel):
    refresh_token: str = Field(..., min_length=3, max_length=255)


class ResetPasswordSchema(BaseModel):
    current_password: str = Field(..., min_length=6, max_length=18)
    new_password: str = Field(..., min_length=6, max_length=18)


class LoggedInUserSchema(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    is_active: bool
    role_id: Optional[int] = None
    role_name: Optional[str] = None
    department_id: Optional[int] = None
    department_name: Optional[str] = None


class LoginResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    user: LoggedInUserSchema
    permissions: Optional[List[str]] = None
