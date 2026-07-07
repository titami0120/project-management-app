import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.department import Department
from app.models.member import Member

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/departments", tags=["departments"])


class DepartmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str


class DepartmentCreateRequest(BaseModel):
    code: str
    name: str


class DepartmentUpdateRequest(BaseModel):
    name: str


@router.get("", response_model=list[DepartmentResponse])
def list_departments(db: Session = Depends(get_db)) -> list[DepartmentResponse]:
    rows = db.execute(
        select(Department)
        .where(Department.is_deleted == False)  # noqa: E712
        .order_by(Department.code)
    ).scalars().all()
    return [DepartmentResponse.model_validate(d) for d in rows]


@router.post("", response_model=DepartmentResponse, status_code=201)
def create_department(body: DepartmentCreateRequest, db: Session = Depends(get_db)) -> DepartmentResponse:
    code = body.code.strip()
    name = body.name.strip()
    existing = db.execute(select(Department).where(Department.code == code)).scalar_one_or_none()
    if existing:
        if existing.is_deleted:
            existing.name = name
            existing.is_deleted = False
            db.commit()
            db.refresh(existing)
            return DepartmentResponse.model_validate(existing)
        raise HTTPException(status_code=409, detail=f"部門コード '{code}' は既に存在します")
    dept = Department(code=code, name=name)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return DepartmentResponse.model_validate(dept)


@router.put("/{dept_id}", response_model=DepartmentResponse)
def update_department(dept_id: int, body: DepartmentUpdateRequest, db: Session = Depends(get_db)) -> DepartmentResponse:
    dept = db.get(Department, dept_id)
    if not dept or dept.is_deleted:
        raise HTTPException(status_code=404, detail="部門が見つかりません")
    dept.name = body.name.strip()
    db.commit()
    db.refresh(dept)
    return DepartmentResponse.model_validate(dept)


@router.delete("/{dept_id}", status_code=204)
def delete_department(dept_id: int, db: Session = Depends(get_db)) -> None:
    dept = db.get(Department, dept_id)
    if not dept or dept.is_deleted:
        raise HTTPException(status_code=404, detail="部門が見つかりません")
    active_count = db.execute(
        select(func.count(Member.id)).where(
            (Member.department_id == dept_id) & (Member.is_deleted == False)  # noqa: E712
        )
    ).scalar() or 0
    if active_count > 0:
        raise HTTPException(
            status_code=409,
            detail=f"この部門には {active_count} 名の有効な要員がいます。先に要員を削除または移動してください。",
        )
    dept.is_deleted = True
    db.commit()
