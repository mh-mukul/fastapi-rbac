from datetime import datetime
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from fastapi import APIRouter, Request, Depends

from config.database import get_db
from utils.helper import ResponseHelper
from utils.auth import get_current_user, hash_password, has_role_permission

from models.user import User, UserRole

router = APIRouter()
response = ResponseHelper()


@router.get("/users")
async def get_users(
    request: Request,
    page: int = 1,
    limit: int = 10,
    name: str = None,
    email: str = None,
    phone: str = None,
    role_id: int = None,
    is_active: bool = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _: None = Depends(has_role_permission(["list_user"])),
):
    # Base query with filtering logic
    query = db.query(User).filter(
        User.is_deleted == False,
        User.department_id == user.department_id)

    # Apply dynamic filters
    if name:
        query = query.filter(User.name.ilike(f"%{name}%"))
    if email:
        query = query.filter(User.email.ilike(f"%{email}%"))
    if phone:
        query = query.filter(User.phone.ilike(f"%{phone}%"))
    if role_id is not None:
        query = query.filter(User.role_id == role_id)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    # Calculate pagination
    total_records = query.count()
    total_pages = (total_records + limit - 1) // limit
    offset = (page - 1) * limit

    # Fetch paginated data
    data_list = (
        query.order_by(User.name.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    # Format user data
    formatted_data = [
        {
            "id": user.id,
            "name": user.name,
            "phone": user.phone,
            "email": user.email,
            "is_active": user.is_active,
            "role_id": user.role_id,
            "role_name": user.role.name if user.role else None,
            "department_id": user.department_id,
            "department_name": user.department.name if user.department else None,
            "created_at": user.created_at,
        }
        for user in data_list
    ]

    # Generate pagination URLs
    base_url = str(request.url.path)
    previous_page_url = f"{base_url}?page={page - 1}&limit={limit}" if page > 1 else None
    next_page_url = f"{base_url}?page={page + 1}&limit={limit}" if page < total_pages else None

    # Prepare the final response
    resp_data = {
        "data": {
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_records": total_records,
                "previous_page_url": previous_page_url,
                "next_page_url": next_page_url,
                "record_per_page": limit,
            },
            "user_list": formatted_data,
        }
    }

    return response.success_response(200, "success", data=resp_data)


@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _: None = Depends(has_role_permission(["list_user"])),
):

    query = db.query(User).filter(
        User.id == user_id,
        User.is_deleted == False,
        User.department_id == user.department_id
    )
    db_user = query.first()
    if not db_user:
        return response.error_response(404, "User not found")
    resp_data = {
        "id": db_user.id,
        "name": db_user.name,
        "phone": db_user.phone,
        "email": db_user.email,
        "role_id": db_user.role_id,
        "role_name": db_user.role.name if db_user.role else None,
        "is_active": db_user.is_active,
        "created_at": db_user.created_at,
        "departmen_id": db_user.department.id if db_user.department else None,
        "departmen_name": db_user.department.name if db_user.department else None,
    }

    return response.success_response(200, "User fetched successfully", resp_data)


class CreateUserBody(BaseModel):
    name: str = Field(..., min_length=5, max_length=50)
    phone: str = Field(..., min_length=10, max_length=20)
    email: str = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=6, max_length=18)
    role_id: int


@router.post("/users")
async def create_user(
    request: Request,
    data: CreateUserBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _: None = Depends(has_role_permission(["create_user"])),
):
    db_user = db.query(User).filter(
        (User.email == data.email) | (User.phone == data.phone)
    ).first()
    if db_user:
        return response.error_response(400, "Account already exists with the email or phone")

    if not db.query(UserRole).filter(
        UserRole.department_id == user.department_id,
        UserRole.id == data.role_id
    ).first():
        return response.error_response(400, "Role not found")

    db_user = User(
        name=data.name,
        phone=data.phone,
        email=data.email,
        password=hash_password(data.password),
        role_id=data.role_id,
        department_id=user.department_id
    )
    db.add(db_user)
    db.commit()

    resp_data = {
        "id": db_user.id,
        "name": db_user.name,
        "phone": db_user.phone,
        "email": db_user.email,
        "is_active": db_user.is_active,
        "role_id": db_user.role_id,
        "role_name": db_user.role.name if db_user.role else None,
        "created_at": db_user.created_at,
        "department_id": db_user.department_id,
        "department_name": db_user.department.name if db_user.department else None,
    }
    return response.success_response(201, "User created successfully", resp_data)


class UpdateUserBody(BaseModel):
    name: str = Field(..., min_length=5, max_length=50)
    phone: str = Field(..., min_length=10, max_length=20)
    email: str = Field(..., min_length=5, max_length=100)
    role_id: int


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    data: UpdateUserBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _: None = Depends(has_role_permission(["update_user"])),
):
    db_user = db.query(User).filter(
        User.id == user_id,
        User.department_id == user.department_id,
        User.is_deleted == False
    ).first()
    if not db_user:
        return response.error_response(404, "User not found")

    if not db.query(UserRole).filter(
        UserRole.department_id == user.department_id,
        UserRole.id == data.role_id
    ).first():
        return response.error_response(400, "Role not found")

    # Check for duplicate users by email or phone (excluding the current user)
    if (
        db.query(User)
        .filter(
            (User.phone == data.phone) | (User.email == data.email),
            User.id != user_id
        )
        .first()
    ):
        return response.error_response(400, "Account exists with this phone or email")

    db_user.name = data.name
    db_user.phone = data.phone
    db_user.email = data.email
    db_user.role_id = data.role_id
    db_user.department_id = user.department_id
    db_user.updated_at = datetime.now()
    db.commit()

    user_data = {
        "id": db_user.id,
        "name": db_user.name,
        "phone": db_user.phone,
        "email": db_user.email,
        "role_id": db_user.role_id,
        "role_name": db_user.role.name if db_user.role else None,
        "is_active": db_user.is_active,
        "created_at": db_user.created_at,
        "department_id": db_user.department_id,
        "department_name": db_user.department.name if db_user.department else None,
    }
    return response.success_response(200, "User updated successfully", user_data)


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _: None = Depends(has_role_permission(["delete_user"])),
):
    db_user = db.query(User).filter(
        User.id == user_id,
        User.is_deleted == False,
        User.department_id == user.department_id
    ).first()
    if not db_user:
        return response.error_response(404, "User not found")
    db_user.soft_delete()
    db.commit()
    return response.success_response(200, "User deleted successfully")
