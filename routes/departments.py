from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import APIRouter, Request, Depends

from config.database import get_db
from utils.helper import ResponseHelper
from utils.auth import get_current_user

from models.user import User
from models.department import Department
from schemas.abstract import Pagination
from schemas.department import DepartmentCreate, DepartmentUpdate, DepartmentGet, DepartmentListResponse

router = APIRouter(prefix="/departments", tags=["Departments"])
response = ResponseHelper()


@router.get("")
async def get_departments(
    request: Request,
    page: int = 1,
    limit: int = 10,
    name: str = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.is_superuser:
        return response.error_response(403, "Permission denied")

    query = Department.get_active(db)

    if name:
        query = query.filter(Department.name.ilike(f"%{name}%"))

    total_records = query.count()
    total_pages = (total_records + limit - 1) // limit
    offset = (page - 1) * limit

    data_list = (
        query.order_by(Department.name.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    departments = [DepartmentGet.model_validate(data) for data in data_list]

    base_url = str(request.url.path)
    previous_page_url = f"{base_url}?page={page - 1}&limit={limit}" if page > 1 else None
    next_page_url = f"{base_url}?page={page + 1}&limit={limit}" if page < total_pages else None

    pagination_data = Pagination(
        current_page=page,
        total_pages=total_pages,
        total_records=total_records,
        record_per_page=limit,
        previous_page_url=previous_page_url,
        next_page_url=next_page_url
    )
    resp_data = DepartmentListResponse(
        departments=departments,
        pagination=pagination_data
    )

    return response.success_response(200, 'Success', resp_data)


@router.get("/{department_id}")
async def get_department(
    department_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.is_superuser:
        return response.error_response(403, "Permission denied")
    department = Department.get_active(db).filter(
        Department.id == department_id
    ).first()

    if not department:
        return response.error_response(404, "Department not found")

    resp_data = DepartmentGet.model_validate(department)

    return response.success_response(200, "success", resp_data)


@router.post("")
async def create_department(
    request: Request,
    data: DepartmentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.is_superuser:
        return response.error_response(403, "Permission denied")

    # Check for duplicate department by name
    if (
        Department.get_active(db)
        .filter(
            Department.name == data.name,
        )
        .first()
    ):
        return response.error_response(400, "Department exists with this name")

    new_department = Department(
        name=data.name
    )
    db.add(new_department)
    db.commit()
    db.refresh(new_department)

    reps_data = DepartmentGet.model_validate(new_department)

    return response.success_response(201, "Department created successfully", reps_data)


@router.put("/{department_id}")
async def update_department(
    department_id: int,
    data: DepartmentUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.is_superuser:
        return response.error_response(403, "Permission denied")

    department = Department.get_active(db).filter(
        Department.id == department_id
    ).first()
    if not department:
        return response.error_response(404, "Department not found")

    # Check for duplicate Department by name (excluding the current department)
    if (
        Department.get_active(db)
        .filter(
            Department.name == data.name,
            Department.id != department_id,
        )
        .first()
    ):
        return response.error_response(400, "Department exists with this name")

    department.name = data.name
    department.updated_at = datetime.now()
    db.commit()
    db.refresh(department)

    resp_data = DepartmentGet.model_validate(department)

    return response.success_response(200, "Department updated successfully", resp_data)


@router.delete("/{department_id}")
async def delete_department(
    department_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.is_superuser:
        return response.error_response(403, "Permission denied")

    department = Department.get_active(db).filter(
        Department.id == department_id,
    ).first()

    if not department:
        return response.error_response(404, "Department not found")

    department.soft_delete()
    db.commit()

    return response.success_response(200, "Department deleted successfully")
