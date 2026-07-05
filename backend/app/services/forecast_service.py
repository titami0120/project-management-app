from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.forecast_snapshot import ForecastSnapshot
from app.models.forecast_version import ForecastVersion
from app.models.monthly_workload import MonthlyWorkload


class ForecastService:
    def create_version_with_snapshot(
        self, db: Session, name: str, description: str | None = None
    ) -> int:
        max_no = db.execute(select(func.max(ForecastVersion.version_no))).scalar() or 0
        version = ForecastVersion(
            version_no=max_no + 1,
            name=name,
            description=description,
        )
        db.add(version)
        db.flush()

        workloads = db.execute(select(MonthlyWorkload)).scalars().all()
        snapshots = [
            ForecastSnapshot(
                version_id=version.id,
                member_id=wl.member_id,
                project_id=wl.project_id,
                year=wl.year,
                month=wl.month,
                forecast_mm=wl.planned_mm,
            )
            for wl in workloads
            if wl.planned_mm is not None
        ]
        if snapshots:
            db.add_all(snapshots)

        db.commit()
        return version.version_no

    def restore_from_version(self, db: Session, version_id: int) -> int:
        snapshots = db.execute(
            select(ForecastSnapshot).where(ForecastSnapshot.version_id == version_id)
        ).scalars().all()

        if not snapshots:
            return 0

        snap_map: dict[tuple[int, int, int, int], ForecastSnapshot] = {
            (s.member_id, s.project_id, s.year, s.month): s
            for s in snapshots
        }

        workloads = db.execute(select(MonthlyWorkload)).scalars().all()
        existing_keys: set[tuple[int, int, int, int]] = set()

        for wl in workloads:
            key = (wl.member_id, wl.project_id, wl.year, wl.month)
            existing_keys.add(key)
            if key in snap_map:
                wl.planned_mm = snap_map[key].forecast_mm
                wl.simulated_mm = None
            else:
                # スナップショット時点では存在しなかったレコードを削除
                db.delete(wl)

        for key, snap in snap_map.items():
            if key not in existing_keys:
                db.add(MonthlyWorkload(
                    member_id=snap.member_id,
                    project_id=snap.project_id,
                    year=snap.year,
                    month=snap.month,
                    planned_mm=snap.forecast_mm,
                    simulated_mm=None,
                ))

        db.commit()
        return len(snapshots)
