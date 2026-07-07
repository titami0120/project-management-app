import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.matter import Matter
from app.models.project import Project
from app.schemas.project_schema import (
    ProjectCreateRequest,
    ProjectMatterAssignRequest,
    ProjectResponse,
    ProjectUpdateRequest,
)

logger = logging.getLogger(__name__)
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
        created_at=project.created_at,
    )


def _load(db: Session, project_id: int) -> Project:
    project = db.execute(
        select(Project).options(joinedload(Project.matter)).where(Project.id == project_id)
    ).scalar_one_or_none()
    if project is None or project.is_deleted:
        raise HTTPException(status_code=404, detail="プロジェクトが見つかりません。")
    return project


@router.get("", response_model=list[ProjectResponse])
def list_projects(
    unassigned: bool = Query(False, description="true のとき未紐づきプロジェクトのみ返す"),
    db: Session = Depends(get_db),
) -> list[ProjectResponse]:
    stmt = (
        select(Project)
        .options(joinedload(Project.matter))
        .where(Project.is_deleted == False)  # noqa: E712
        .order_by(Project.display_order.asc().nulls_last(), Project.wbs_tmp)
    )
    if unassigned:
        stmt = stmt.where(Project.matter_id == None)  # noqa: E711
    projects = db.execute(stmt).scalars().unique().all()
    return [_to_response(p) for p in projects]


@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(body: ProjectCreateRequest, db: Session = Depends(get_db)) -> ProjectResponse:
    wbs_tmp = body.wbs_tmp.strip()
    existing = db.execute(
        select(Project).options(joinedload(Project.matter)).where(Project.wbs_tmp == wbs_tmp)
    ).scalar_one_or_none()
    if existing:
        if existing.is_deleted:
            existing.name = body.name.strip()
            existing.code = body.code or None
            existing.display_order = body.display_order
            existing.matter_id = body.matter_id
            existing.is_deleted = False
            db.commit()
            db.refresh(existing)
            return _to_response(
                db.execute(
                    select(Project).options(joinedload(Project.matter)).where(Project.id == existing.id)
                ).scalar_one()
            )
        raise HTTPException(status_code=409, detail=f"WBS仮コード '{wbs_tmp}' は既に存在します")

    if body.matter_id is not None:
        matter = db.get(Matter, body.matter_id)
        if matter is None:
            raise HTTPException(status_code=404, detail="案件が見つかりません。")

    project = Project(
        wbs_tmp=wbs_tmp,
        name=body.name.strip(),
        code=body.code or None,
        display_order=body.display_order,
        matter_id=body.matter_id,
    )
    db.add(project)
    db.commit()
    return _to_response(
        db.execute(
            select(Project).options(joinedload(Project.matter)).where(Project.id == project.id)
        ).scalar_one()
    )


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    body: ProjectUpdateRequest,
    db: Session = Depends(get_db),
) -> ProjectResponse:
    project = _load(db, project_id)

    if body.name is not None:
        project.name = body.name.strip()
    if body.code is not None:
        project.code = body.code.strip() or None
    if body.display_order is not None:
        project.display_order = body.display_order
    if "matter_id" in body.model_fields_set:
        if body.matter_id is not None:
            matter = db.get(Matter, body.matter_id)
            if matter is None:
                raise HTTPException(status_code=404, detail="案件が見つかりません。")
        project.matter_id = body.matter_id

    db.commit()
    db.refresh(project)
    return _to_response(
        db.execute(
            select(Project).options(joinedload(Project.matter)).where(Project.id == project_id)
        ).scalar_one()
    )


@router.put("/{project_id}/matter", response_model=ProjectResponse)
def assign_matter(
    project_id: int,
    body: ProjectMatterAssignRequest,
    db: Session = Depends(get_db),
) -> ProjectResponse:
    project = _load(db, project_id)

    if body.matter_id is not None:
        matter = db.execute(
            select(Matter).where(Matter.id == body.matter_id)
        ).scalar_one_or_none()
        if matter is None:
            raise HTTPException(status_code=404, detail="案件が見つかりません。")

    project.matter_id = body.matter_id
    db.commit()
    db.refresh(project)
    return _to_response(
        db.execute(
            select(Project).options(joinedload(Project.matter)).where(Project.id == project_id)
        ).scalar_one()
    )


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db)) -> None:
    project = db.get(Project, project_id)
    if project is None or project.is_deleted:
        raise HTTPException(status_code=404, detail="プロジェクトが見つかりません。")
    project.is_deleted = True
    db.commit()
