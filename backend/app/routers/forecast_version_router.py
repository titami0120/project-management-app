from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.forecast_snapshot import ForecastSnapshot
from app.models.forecast_version import ForecastVersion
from app.services.forecast_service import ForecastService

router = APIRouter(prefix="/api/v1/forecast-versions", tags=["forecast-versions"])

_service = ForecastService()


class ForecastVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    version_no: int
    name: str
    description: str | None
    snapshot_count: int
    created_at: datetime


class CreateVersionRequest(BaseModel):
    name: str
    description: str | None = None


class RestoreVersionResponse(BaseModel):
    restored_count: int


@router.get("", response_model=list[ForecastVersionResponse])
def list_forecast_versions(db: Session = Depends(get_db)) -> list[ForecastVersionResponse]:
    rows = db.execute(
        select(ForecastVersion).order_by(
            ForecastVersion.created_at.desc(), ForecastVersion.id.desc()
        )
    ).scalars().all()

    counts: dict[int, int] = {}
    if rows:
        version_ids = [v.id for v in rows]
        count_rows = db.execute(
            select(ForecastSnapshot.version_id, func.count().label("cnt"))
            .where(ForecastSnapshot.version_id.in_(version_ids))
            .group_by(ForecastSnapshot.version_id)
        ).all()
        counts = {r.version_id: r.cnt for r in count_rows}

    return [
        ForecastVersionResponse(
            id=v.id,
            version_no=v.version_no,
            name=v.name,
            description=v.description,
            snapshot_count=counts.get(v.id, 0),
            created_at=v.created_at,
        )
        for v in rows
    ]


@router.post("", response_model=ForecastVersionResponse)
def create_forecast_version(
    body: CreateVersionRequest, db: Session = Depends(get_db)
) -> ForecastVersionResponse:
    version_no = _service.create_version_with_snapshot(
        db, name=body.name, description=body.description
    )
    version = db.execute(
        select(ForecastVersion).where(ForecastVersion.version_no == version_no)
    ).scalar_one()
    snapshot_count = db.execute(
        select(func.count()).where(ForecastSnapshot.version_id == version.id)
    ).scalar() or 0
    return ForecastVersionResponse(
        id=version.id,
        version_no=version.version_no,
        name=version.name,
        description=version.description,
        snapshot_count=snapshot_count,
        created_at=version.created_at,
    )


@router.post("/{version_id}/restore", response_model=RestoreVersionResponse)
def restore_forecast_version(
    version_id: int, db: Session = Depends(get_db)
) -> RestoreVersionResponse:
    version = db.execute(
        select(ForecastVersion).where(ForecastVersion.id == version_id)
    ).scalar_one_or_none()
    if version is None:
        raise HTTPException(status_code=404, detail="バージョンが見つかりません")
    restored_count = _service.restore_from_version(db, version_id)
    return RestoreVersionResponse(restored_count=restored_count)


@router.delete("/{version_id}", status_code=204)
def delete_forecast_version(
    version_id: int, db: Session = Depends(get_db)
) -> None:
    version = db.execute(
        select(ForecastVersion).where(ForecastVersion.id == version_id)
    ).scalar_one_or_none()
    if version is None:
        raise HTTPException(status_code=404, detail="バージョンが見つかりません")
    db.delete(version)
    db.commit()
