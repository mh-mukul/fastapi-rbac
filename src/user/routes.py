from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import APIRouter, Request, Depends

from configs.database import get_db
from src.helpers import ResponseHelper
from src.auth.utils import hash_password
from src.auth.dependencies import get_current_user, has_role_permission

from src.user.models import User, UserRole
from src.schemas import Pagination
from src.user.schemas import UserGet, UserListResponse, UserCreate, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])
response = ResponseHelper()


@router.get("")
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
    query = User.get_active(db).filter(
        User.department_id == user.department_id)

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

    users, total = response.paginate_query(query, page, limit)

    formatted_users = [UserGet.model_validate(user) for user in users]

    base_url = str(request.url.path)

    pagination_data = Pagination(
        current_page=page,
        total_pages=total // limit + (1 if total % limit else 0),
        total_records=total,
        record_per_page=limit,
        previous_page_url=f"{base_url}?page={page - 1}&limit={limit}" if page > 1 else None,
        next_page_url=f"{request.url.path}?page={page + 1}&limit={limit}" if (
            page * limit) < total else None,
    )
    resp_data = UserListResponse(
        users=formatted_users,
        pagination=pagination_data
    )

    return response.success_response(200, "success", data=resp_data)


@router.get("/{user_id}")
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _: None = Depends(has_role_permission(["list_user"])),
):
    query = User.get_active(db).filter(
        User.id == user_id,
        User.department_id == user.department_id
    )
    db_user = query.first()
    if not db_user:
        return response.error_response(404, "User not found")
    resp_data = UserGet.model_validate(db_user)

    return response.success_response(200, "User fetched successfully", resp_data)


@router.post("")
async def create_user(
    request: Request,
    data: UserCreate,
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
        return response.error_response(404, "Role not found")

    new_user = User(
        name=data.name,
        phone=data.phone,
        email=data.email,
        password=hash_password(data.password),
        role_id=data.role_id,
        department_id=user.department_id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    resp_data = UserGet.model_validate(new_user)

    return response.success_response(201, "User created successfully", resp_data)


@router.put("/{user_id}")
async def update_user(
    user_id: int,
    data: UserUpdate,
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
        return response.error_response(404, "Role not found")

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
    db.refresh(db_user)

    resp_data = UserGet.model_validate(db_user)

    return response.success_response(200, "User updated successfully", resp_data)


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _: None = Depends(has_role_permission(["delete_user"])),
):
    db_user = User.get_active(db).filter(
        User.id == user_id,
        User.department_id == user.department_id
    ).first()
    if not db_user:
        return response.error_response(404, "User not found")

    db_user.soft_delete()
    db.commit()

    return response.success_response(200, "User deleted successfully")
