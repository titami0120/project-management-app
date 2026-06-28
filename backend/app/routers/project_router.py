from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.matter import Matter
from app.models.project import Project
from app.schemas.project_schema import (
    ProjectMatterAssignRequest,
    ProjectResponse,
    ProjectUpdateRequest,
)

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


def _to_response(project: Project) -> ProjectResponse:
    return ProjectResponse(
        id=project.id,
        wbs_tmp=project.wbs_tmp,
        name=project.name,
        code=project.code,
        display_order=project.display_order,
        matter_id=project.matter_id,
        matter_name=project.matter.name if project.matter else None,
    )


@router.get("", response_model=list[ProjectResponse])
def list_projects(
    unassigned: bool = Query(False, description="true のとき未紐づきプロジェクトのみ返す"),
    db: Session = Depends(get_db),
) -> list[ProjectResponse]:
    stmt = (
        select(Project)
        .options(joinedload(Project.matter))
        .where(Project.is_deleted == False)  # noqa: E712
        .order_by(Project.id)
    )
    if unassigned:
        stmt = stmt.where(Project.matter_id == None)  # noqa: E711
    projects = db.execute(stmt).scalars().unique().all()
    return [_to_response(p) for p in projects]


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    body: ProjectUpdateRequest,
    db: Session = Depends(get_db),
) -> ProjectResponse:
    project = db.execute(
        select(Project).options(joinedload(Project.matter)).where(Project.id == project_id)
    ).scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="プロジェクトが見つかりません。")

    if body.name is not None:
        project.name = body.name
    if body.code is not None:
        project.code = body.code
    if body.display_order is not None:
        project.display_order = body.display_order

    db.commit()
    db.refresh(project)
    return _to_response(project)


@router.put("/{project_id}/matter", response_model=ProjectResponse)
def assign_matter(
    project_id: int,
    body: ProjectMatterAssignRequest,
    db: Session = Depends(get_db),
) -> ProjectResponse:
    project = db.execute(
        select(Project).options(joinedload(Project.matter)).where(Project.id == project_id)
    ).scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="プロジェクトが見つかりません。")

    if body.matter_id is not None:
        matter = db.execute(
            select(Matter).where(Matter.id == body.matter_id)
        ).scalar_one_or_none()
        if matter is None:
            raise HTTPException(status_code=404, detail="案件が見つかりません。")

    project.matter_id = body.matter_id
    db.commit()
    db.refresh(project)
    return _to_response(project)
