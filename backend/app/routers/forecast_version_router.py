from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.forecast_version import ForecastVersion

router = APIRouter(prefix="/api/v1/forecast-versions", tags=["forecast-versions"])


class ForecastVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    version_no: int
    trigger_type: str
    note: str | None
    created_at: datetime


@router.get("", response_model=list[ForecastVersionResponse])
def list_forecast_versions(db: Session = Depends(get_db)) -> list[ForecastVersionResponse]:
    rows = db.execute(
        select(ForecastVersion).order_by(
            ForecastVersion.created_at.desc(), ForecastVersion.id.desc()
        )
    ).scalars().all()
    return [ForecastVersionResponse.model_validate(v) for v in rows]
