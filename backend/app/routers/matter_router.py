from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.matter import Matter
from app.models.project import Project
from app.schemas.matter_schema import MatterCreateRequest, MatterResponse

router = APIRouter(prefix="/api/v1/matters", tags=["matters"])


def _to_response(matter: Matter, project_count: int) -> MatterResponse:
    return MatterResponse(
        id=matter.id,
        name=matter.name,
        code=matter.code,
        client_name=matter.client_name,
        status=matter.status,
        pm_member_id=matter.pm_member_id,
        project_count=project_count,
        created_at=matter.created_at,
    )


@router.get("", response_model=list[MatterResponse])
def list_matters(db: Session = Depends(get_db)) -> list[MatterResponse]:
    rows = db.execute(
        select(Matter, func.count(Project.id).label("project_count"))
        .outerjoin(Project, Project.matter_id == Matter.id)
        .where(Matter.is_deleted == False)  # noqa: E712
        .group_by(Matter.id)
        .order_by(Matter.id)
    ).all()
    return [_to_response(matter, count) for matter, count in rows]


@router.post("", response_model=MatterResponse, status_code=201)
def create_matter(
    body: MatterCreateRequest,
    db: Session = Depends(get_db),
) -> MatterResponse:
    existing = db.execute(
        select(Matter).where(Matter.code == body.code)
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail=f"案件コード '{body.code}' は既に使用されています。",
        )

    matter = Matter(
        name=body.name,
        code=body.code,
        client_name=body.client_name,
        status=body.status,
        pm_member_id=body.pm_member_id,
    )
    db.add(matter)
    db.commit()
    db.refresh(matter)
    return _to_response(matter, 0)
