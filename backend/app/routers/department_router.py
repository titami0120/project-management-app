from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.department import Department

router = APIRouter(prefix="/api/v1/departments", tags=["departments"])


class DepartmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str


@router.get("", response_model=list[DepartmentResponse])
def list_departments(db: Session = Depends(get_db)) -> list[DepartmentResponse]:
    rows = db.execute(
        select(Department)
        .where(Department.is_deleted == False)  # noqa: E712
        .order_by(Department.code)
    ).scalars().all()
    return [DepartmentResponse.model_validate(d) for d in rows]
