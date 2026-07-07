import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.department import Department
from app.models.member import Member
from app.models.team import Team
from app.models.team_member import TeamMember

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/teams", tags=["teams"])


class TeamResponse(BaseModel):
    id: int
    name: str
    department_id: int
    department_name: str
    member_count: int


class TeamMemberResponse(BaseModel):
    member_id: int
    employee_code: str
    name: str
    department_name: str


class TeamCreateRequest(BaseModel):
    name: str
    department_id: int


class TeamUpdateRequest(BaseModel):
    name: str
    department_id: int


def _member_count(db: Session, team_id: int) -> int:
    return db.execute(
        select(func.count(TeamMember.member_id)).where(TeamMember.team_id == team_id)
    ).scalar() or 0


# ---------------------------------------------------------------------------
# チーム CRUD
# ---------------------------------------------------------------------------

@router.get("", response_model=list[TeamResponse])
def list_teams(db: Session = Depends(get_db)) -> list[TeamResponse]:
    rows = db.execute(
        select(
            Team.id,
            Team.name,
            Team.department_id,
            Department.name.label("department_name"),
            func.count(TeamMember.member_id).label("member_count"),
        )
        .join(Department, Team.department_id == Department.id)
        .outerjoin(TeamMember, Team.id == TeamMember.team_id)
        .where(Team.is_deleted == False)  # noqa: E712
        .group_by(Team.id, Team.name, Team.department_id, Department.name)
        .order_by(Department.code, Team.name)
    ).all()
    return [
        TeamResponse(
            id=r.id,
            name=r.name,
            department_id=r.department_id,
            department_name=r.department_name,
            member_count=r.member_count,
        )
        for r in rows
    ]


@router.post("", response_model=TeamResponse, status_code=201)
def create_team(body: TeamCreateRequest, db: Session = Depends(get_db)) -> TeamResponse:
    dept = db.get(Department, body.department_id)
    if not dept or dept.is_deleted:
        raise HTTPException(status_code=404, detail="部門が見つかりません")
    team = Team(name=body.name.strip(), department_id=body.department_id)
    db.add(team)
    db.commit()
    db.refresh(team)
    return TeamResponse(
        id=team.id,
        name=team.name,
        department_id=team.department_id,
        department_name=dept.name,
        member_count=0,
    )


@router.put("/{team_id}", response_model=TeamResponse)
def update_team(team_id: int, body: TeamUpdateRequest, db: Session = Depends(get_db)) -> TeamResponse:
    team = db.get(Team, team_id)
    if not team or team.is_deleted:
        raise HTTPException(status_code=404, detail="チームが見つかりません")
    dept = db.get(Department, body.department_id)
    if not dept or dept.is_deleted:
        raise HTTPException(status_code=404, detail="部門が見つかりません")
    team.name = body.name.strip()
    team.department_id = body.department_id
    db.commit()
    db.refresh(team)
    return TeamResponse(
        id=team.id,
        name=team.name,
        department_id=team.department_id,
        department_name=dept.name,
        member_count=_member_count(db, team_id),
    )


@router.delete("/{team_id}", status_code=204)
def delete_team(team_id: int, db: Session = Depends(get_db)) -> None:
    team = db.get(Team, team_id)
    if not team or team.is_deleted:
        raise HTTPException(status_code=404, detail="チームが見つかりません")
    team.is_deleted = True
    db.commit()


# ---------------------------------------------------------------------------
# チームメンバー管理
# ---------------------------------------------------------------------------

@router.get("/{team_id}/members", response_model=list[TeamMemberResponse])
def list_team_members(team_id: int, db: Session = Depends(get_db)) -> list[TeamMemberResponse]:
    team = db.get(Team, team_id)
    if not team or team.is_deleted:
        raise HTTPException(status_code=404, detail="チームが見つかりません")
    rows = db.execute(
        select(
            Member.id.label("member_id"),
            Member.employee_code,
            Member.name,
            Department.name.label("department_name"),
        )
        .join(TeamMember, TeamMember.member_id == Member.id)
        .join(Department, Member.department_id == Department.id)
        .where(TeamMember.team_id == team_id)
        .where(Member.is_deleted == False)  # noqa: E712
        .order_by(Member.employee_code)
    ).all()
    return [
        TeamMemberResponse(
            member_id=r.member_id,
            employee_code=r.employee_code,
            name=r.name,
            department_name=r.department_name,
        )
        for r in rows
    ]


@router.post("/{team_id}/members/{member_id}", status_code=201)
def add_team_member(team_id: int, member_id: int, db: Session = Depends(get_db)) -> dict[str, bool]:
    team = db.get(Team, team_id)
    if not team or team.is_deleted:
        raise HTTPException(status_code=404, detail="チームが見つかりません")
    member = db.get(Member, member_id)
    if not member or member.is_deleted:
        raise HTTPException(status_code=404, detail="要員が見つかりません")
    already = db.execute(
        select(TeamMember).where(
            (TeamMember.team_id == team_id) & (TeamMember.member_id == member_id)
        )
    ).scalar_one_or_none()
    if already:
        raise HTTPException(status_code=409, detail="この要員は既にチームに所属しています")
    db.add(TeamMember(team_id=team_id, member_id=member_id))
    db.commit()
    return {"ok": True}


@router.delete("/{team_id}/members/{member_id}", status_code=204)
def remove_team_member(team_id: int, member_id: int, db: Session = Depends(get_db)) -> None:
    tm = db.execute(
        select(TeamMember).where(
            (TeamMember.team_id == team_id) & (TeamMember.member_id == member_id)
        )
    ).scalar_one_or_none()
    if not tm:
        raise HTTPException(status_code=404, detail="チームメンバーが見つかりません")
    db.delete(tm)
    db.commit()
