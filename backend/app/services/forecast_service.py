from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.forecast_snapshot import ForecastSnapshot
from app.models.forecast_version import ForecastVersion
from app.models.monthly_workload import MonthlyWorkload


class ForecastService:
    def create_version_with_snapshot(self, db: Session, trigger_type: str) -> int:
        max_no = db.execute(select(func.max(ForecastVersion.version_no))).scalar() or 0
        version = ForecastVersion(version_no=max_no + 1, trigger_type=trigger_type)
        db.add(version)
        db.flush()

        workloads = db.execute(select(MonthlyWorkload)).scalars().all()
        snapshots = []
        for wl in workloads:
            forecast_mm: Decimal | None = (
                wl.simulated_mm if wl.simulated_mm is not None else wl.planned_mm
            )
            if forecast_mm is not None:
                snapshots.append(ForecastSnapshot(
                    version_id=version.id,
                    member_id=wl.member_id,
                    project_id=wl.project_id,
                    year=wl.year,
                    month=wl.month,
                    forecast_mm=forecast_mm,
                ))
        if snapshots:
            db.add_all(snapshots)

        return version.version_no
