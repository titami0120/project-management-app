import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.department import Department
from app.models.member import Member

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/members", tags=["members"])


class MemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_code: str
    name: str
    department_id: int
    department_name: str


class MemberCreateRequest(BaseModel):
    employee_code: str
    name: str
    department_id: int


class MemberUpdateRequest(BaseModel):
    name: str
    department_id: int


def _load_with_dept(db: Session, member_id: int) -> Member:
    return db.execute(
        select(Member).options(joinedload(Member.department)).where(Member.id == member_id)
    ).scalar_one()


def _to_response(m: Member) -> MemberResponse:
    return MemberResponse(
        id=m.id,
        employee_code=m.employee_code,
        name=m.name,
        department_id=m.department_id,
        department_name=m.department.name,
    )


@router.get("", response_model=list[MemberResponse])
def list_members(
    dept_id: int | None = Query(None, description="部門IDフィルタ"),
    db: Session = Depends(get_db),
) -> list[MemberResponse]:
    stmt = (
        select(Member)
        .options(joinedload(Member.department))
        .where(Member.is_deleted == False)  # noqa: E712
        .order_by(Member.employee_code)
    )
    if dept_id is not None:
        stmt = stmt.where(Member.department_id == dept_id)
    rows = db.execute(stmt).scalars().unique().all()
    return [_to_response(m) for m in rows]


@router.post("", response_model=MemberResponse, status_code=201)
def create_member(body: MemberCreateRequest, db: Session = Depends(get_db)) -> MemberResponse:
    dept = db.get(Department, body.department_id)
    if not dept or dept.is_deleted:
        raise HTTPException(status_code=404, detail="部門が見つかりません")
    code = body.employee_code.strip()
    existing = db.execute(select(Member).where(Member.employee_code == code)).scalar_one_or_none()
    if existing:
        if existing.is_deleted:
            existing.name = body.name.strip()
            existing.department_id = body.department_id
            existing.is_deleted = False
            db.commit()
            return _to_response(_load_with_dept(db, existing.id))
        raise HTTPException(status_code=409, detail=f"社員コード '{code}' は既に存在します")
    member = Member(employee_code=code, name=body.name.strip(), department_id=body.department_id)
    db.add(member)
    db.commit()
    return _to_response(_load_with_dept(db, member.id))


@router.put("/{member_id}", response_model=MemberResponse)
def update_member(member_id: int, body: MemberUpdateRequest, db: Session = Depends(get_db)) -> MemberResponse:
    member = db.get(Member, member_id)
    if not member or member.is_deleted:
        raise HTTPException(status_code=404, detail="要員が見つかりません")
    dept = db.get(Department, body.department_id)
    if not dept or dept.is_deleted:
        raise HTTPException(status_code=404, detail="部門が見つかりません")
    member.name = body.name.strip()
    member.department_id = body.department_id
    db.commit()
    return _to_response(_load_with_dept(db, member_id))


@router.delete("/{member_id}", status_code=204)
def delete_member(member_id: int, db: Session = Depends(get_db)) -> None:
    member = db.get(Member, member_id)
    if not member or member.is_deleted:
        raise HTTPException(status_code=404, detail="要員が見つかりません")
    member.is_deleted = True
    db.commit()
