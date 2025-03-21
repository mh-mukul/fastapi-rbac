from datetime import datetime
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from fastapi import APIRouter, Request, Depends

from config.database import get_db
from utils.helper import ResponseHelper
from utils.auth import get_current_user

from models.user import User
from models.department import Department

router = APIRouter()
response = ResponseHelper()


@router.get("/departments")
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
    # Base query with filtering logic
    query = db.query(Department).filter(Department.is_deleted == False)

    # Apply dynamic filters
    if name:
        query = query.filter(Department.name.ilike(f"%{name}%"))

    # Calculate pagination
    total_records = query.count()
    total_pages = (total_records + limit - 1) // limit
    offset = (page - 1) * limit

    # Fetch paginated data
    data_list = (
        query.order_by(Department.name.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    formatted_data = [
        {
            "id": department.id,
            "name": department.name,
            "is_active": department.is_active,
            "created_at": department.created_at,
        }
        for department in data_list
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
            "department_list": formatted_data,
        }
    }

    return response.success_response(200, 'Success', resp_data)


@router.get("/departments/{department_id}")
async def get_department(
    department_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.is_superuser:
        return response.error_response(403, "Permission denied")
    db_department = db.query(Department).filter(
        Department.id == department_id,
        Department.is_deleted == False
    ).first()
    if not db_department:
        return response.error_response(404, "Department not found")
    resp_data = {
        "id": db_department.id,
        "name": db_department.name,
        "is_active": db_department.is_active,
        "created_at": db_department.created_at,
    }
    return response.success_response(200, "success", resp_data)


class CreateDepartmentBody(BaseModel):
    name: str = Field(..., min_length=5, max_length=50)


@router.post("/departments")
async def create_department(
    request: Request,
    data: CreateDepartmentBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.is_superuser:
        return response.error_response(403, "Permission denied")

    # Check for duplicate department by name
    if (
        db.query(Department)
        .filter(
            Department.name == data.name,
            Department.is_deleted == False,
        )
        .first()
    ):
        return response.error_response(400, "Department exists with this name")

    db_department = Department(
        name=data.name
    )
    db.add(db_department)
    db.commit()
    db.refresh(db_department)
    reps_data = {
        "id": db_department.id,
        "name": db_department.name,
        "is_active": db_department.is_active,
        "created_at": db_department.created_at,
    }
    return response.success_response(201, "Department created successfully", reps_data)


class UpdateDepartmentBody(BaseModel):
    name: str = Field(..., min_length=5, max_length=50)


@router.put("/departments/{department_id}")
async def update_department(
    department_id: int,
    data: UpdateDepartmentBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.is_superuser:
        return response.error_response(403, "Permission denied")

    db_department = db.query(Department).filter(
        Department.id == department_id,
        Department.is_deleted == False
    ).first()
    if not db_department:
        return response.error_response(404, "Department not found")

    # Check for duplicate Department by name (excluding the current department)
    if (
        db.query(Department)
        .filter(
            Department.name == data.name,
            Department.id != department_id,
            Department.is_deleted == False,
        )
        .first()
    ):
        return response.error_response(400, "Department exists with this name")
    db_department.name = data.name
    db_department.updated_at = datetime.now()
    db.commit()
    db.refresh(db_department)
    resp_data = {
        "id": db_department.id,
        "name": db_department.name,
        "is_active": db_department.is_active,
        "updated_at": db_department.updated_at,
    }
    return response.success_response(200, "Department updated successfully", resp_data)


@router.delete("/departments/{department_id}")
async def delete_department(
    department_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.is_superuser:
        return response.error_response(403, "Permission denied")

    db_department = db.query(Department).filter(
        Department.id == department_id,
        Department.is_deleted == False
    ).first()
    if not db_department:
        return response.error_response(404, "Department not found")
    db_department.soft_delete()
    db.commit()
    return response.success_response(200, "Department deleted successfully")
