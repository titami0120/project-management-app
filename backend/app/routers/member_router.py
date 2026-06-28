from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.member import Member

router = APIRouter(prefix="/api/v1/members", tags=["members"])


class MemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_code: str
    name: str
    department_id: int


@router.get("", response_model=list[MemberResponse])
def list_members(
    dept_id: int | None = Query(None, description="部門IDフィルタ"),
    db: Session = Depends(get_db),
) -> list[MemberResponse]:
    stmt = (
        select(Member)
        .where(Member.is_deleted == False)  # noqa: E712
        .order_by(Member.employee_code)
    )
    if dept_id is not None:
        stmt = stmt.where(Member.department_id == dept_id)
    rows = db.execute(stmt).scalars().all()
    return [MemberResponse.model_validate(m) for m in rows]
