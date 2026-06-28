from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.workload_schema import (
    CsvUploadErrorResponse,
    CsvUploadResponse,
    ForecastWorkloadResponse,
    ParticipatingProject,
    SimulationUpdateRequest,
)
from app.services.csv_import_service import CsvImportService
from app.services.exceptions import CsvValidationException
from app.services.workload_service import WorkloadService

router = APIRouter(prefix="/api/v1/workloads", tags=["workloads"])

_csv_import_service = CsvImportService()
_workload_service = WorkloadService()


def _parse_ym(value: str) -> tuple[int, int]:
    """'YYYY-MM' を (year, month) に変換する。不正な形式は ValueError を送出。"""
    parts = value.split("-")
    if len(parts) != 2:
        raise ValueError(f"Invalid YYYY-MM format: {value}")
    return int(parts[0]), int(parts[1])


@router.post(
    "/plan/upload",
    response_model=CsvUploadResponse,
    responses={422: {"model": CsvUploadErrorResponse}},
)
def upload_plan_csv(
    file: UploadFile,
    db: Session = Depends(get_db),
) -> CsvUploadResponse:
    content = file.file.read()
    try:
        return _csv_import_service.import_plan_csv(content, db)
    except CsvValidationException as exc:
        raise HTTPException(
            status_code=422,
            detail={"errors": [e.model_dump() for e in exc.errors]},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/participating-projects", response_model=list[ParticipatingProject])
def get_participating_projects(
    dept_id: int | None = Query(None, description="部門IDフィルタ"),
    db: Session = Depends(get_db),
) -> list[ParticipatingProject]:
    projects = _workload_service.get_participating_projects(db, dept_id)
    return [ParticipatingProject(id=p.id, wbs_tmp=p.wbs_tmp, name=p.name) for p in projects]


@router.get("/forecast", response_model=ForecastWorkloadResponse)
def get_forecast(
    from_: str = Query(..., alias="from", description="開始年月 (YYYY-MM)"),
    to: str = Query(..., description="終了年月 (YYYY-MM)"),
    dept_id: int | None = Query(None, description="部門IDフィルタ"),
    team_id: int | None = Query(None, description="チームIDフィルタ"),
    project_id: int | None = Query(None, description="プロジェクトIDフィルタ"),
    db: Session = Depends(get_db),
) -> ForecastWorkloadResponse:
    try:
        year_from, month_from = _parse_ym(from_)
        year_to, month_to = _parse_ym(to)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="クエリパラメータ 'from' / 'to' は YYYY-MM 形式で指定してください。",
        ) from exc

    return _workload_service.get_forecast(
        db, dept_id, team_id, year_from, month_from, year_to, month_to, project_id
    )


@router.put("/simulate", response_model=dict)
def save_simulation(
    body: SimulationUpdateRequest,
    db: Session = Depends(get_db),
) -> dict:
    try:
        _workload_service.save_simulation(db, body.updates)
        return {"ok": True}
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.delete("/simulate", response_model=dict)
def reset_simulation(
    member_id: int | None = Query(None, description="リセット対象の要員ID"),
    project_id: int | None = Query(None, description="リセット対象のプロジェクトID"),
    db: Session = Depends(get_db),
) -> dict:
    try:
        _workload_service.reset_simulation(db, member_id, project_id)
        return {"ok": True}
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/forecast/download")
def download_forecast_csv(
    from_: str = Query(..., alias="from", description="開始年月 (YYYY-MM)"),
    to: str = Query(..., description="終了年月 (YYYY-MM)"),
    dept_id: int | None = Query(None, description="部門IDフィルタ"),
    team_id: int | None = Query(None, description="チームIDフィルタ"),
    project_id: int | None = Query(None, description="プロジェクトIDフィルタ"),
    db: Session = Depends(get_db),
) -> Response:
    try:
        year_from, month_from = _parse_ym(from_)
        year_to, month_to = _parse_ym(to)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="クエリパラメータ 'from' / 'to' は YYYY-MM 形式で指定してください。",
        ) from exc

    csv_bytes = _workload_service.download_forecast_csv(
        db, dept_id, team_id, year_from, month_from, year_to, month_to, project_id
    )
    filename = f"workload_{from_}_{to}.csv"
    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=shift_jis",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
