"""WorkloadService: 見込工数の取得・シミュレーション保存・リセット"""
import csv
import io
from collections import defaultdict
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.orm import Session, joinedload

from app.models.department import Department
from app.models.member import Member
from app.models.monthly_workload import MonthlyWorkload
from app.models.project import Project
from app.models.team_member import TeamMember
from app.schemas.workload_schema import (
    ForecastCell,
    ForecastMemberRow,
    ForecastProjectRow,
    ForecastWorkloadResponse,
    SimulationUpdateItem,
)


def _generate_months(
    year_from: int, month_from: int, year_to: int, month_to: int
) -> list[str]:
    months: list[str] = []
    y, m = year_from, month_from
    while (y, m) <= (year_to, month_to):
        months.append(f"{y:04d}-{m:02d}")
        m += 1
        if m > 12:
            m = 1
            y += 1
    return months


class WorkloadService:
    def get_participating_projects(
        self,
        db: Session,
        dept_id: int | None,
    ) -> list:
        """部門に所属する要員が工数登録しているプロジェクト一覧を返す。"""
        stmt = (
            select(Project)
            .join(MonthlyWorkload, MonthlyWorkload.project_id == Project.id)
            .join(Member, MonthlyWorkload.member_id == Member.id)
            .distinct()
            .order_by(Project.wbs_tmp)
        )
        if dept_id is not None:
            stmt = stmt.where(Member.department_id == dept_id)
        return db.execute(stmt).scalars().unique().all()

    def get_forecast(
        self,
        db: Session,
        dept_id: int | None,
        team_id: int | None,
        year_from: int,
        month_from: int,
        year_to: int,
        month_to: int,
        project_id: int | None = None,
    ) -> ForecastWorkloadResponse:
        months = _generate_months(year_from, month_from, year_to, month_to)

        ym_from = year_from * 100 + month_from
        ym_to = year_to * 100 + month_to

        stmt = (
            select(MonthlyWorkload)
            .join(MonthlyWorkload.member)
            .join(MonthlyWorkload.project)
            .outerjoin(Project.matter)
            .options(
                joinedload(MonthlyWorkload.member),
                joinedload(MonthlyWorkload.project).joinedload(Project.matter),
            )
            .where(
                (MonthlyWorkload.year * 100 + MonthlyWorkload.month) >= ym_from,
                (MonthlyWorkload.year * 100 + MonthlyWorkload.month) <= ym_to,
            )
        )

        if dept_id is not None:
            stmt = stmt.where(Member.department_id == dept_id)

        if team_id is not None:
            team_member_subq = select(TeamMember.member_id).where(
                TeamMember.team_id == team_id
            )
            stmt = stmt.where(MonthlyWorkload.member_id.in_(team_member_subq))

        if project_id is not None:
            stmt = stmt.where(MonthlyWorkload.project_id == project_id)

        workloads = db.execute(stmt).scalars().unique().all()

        # member_id → { member, projects: { project_id → { project, cells, raw_sums } } }
        member_map: dict[int, dict] = {}

        for wl in workloads:
            forecast_mm: Decimal | None = (
                wl.simulated_mm if wl.simulated_mm is not None else wl.planned_mm
            )
            if forecast_mm is None:
                continue

            member = wl.member
            project = wl.project

            if member.id not in member_map:
                member_map[member.id] = {
                    "member": member,
                    "projects": {},
                    "raw_sums": defaultdict(Decimal),
                }

            project_map: dict[int, dict] = member_map[member.id]["projects"]
            if project.id not in project_map:
                project_map[project.id] = {"project": project, "cells": {}}

            month_key = f"{wl.year:04d}-{wl.month:02d}"
            project_map[project.id]["cells"][month_key] = ForecastCell(
                planned_mm=wl.planned_mm,
                simulated_mm=wl.simulated_mm,
                forecast_mm=forecast_mm,
            )
            member_map[member.id]["raw_sums"][month_key] += forecast_mm

        result_rows: list[ForecastMemberRow] = []
        for member_data in member_map.values():
            member = member_data["member"]
            raw_sums: dict[str, Decimal] = member_data["raw_sums"]
            project_rows: list[ForecastProjectRow] = []

            for proj_data in member_data["projects"].values():
                project = proj_data["project"]
                cells: dict[str, ForecastCell] = proj_data["cells"]

                matter = project.matter
                project_rows.append(
                    ForecastProjectRow(
                        project_id=project.id,
                        project_name=project.name,
                        wbs_tmp=project.wbs_tmp,
                        matter_id=matter.id if matter else None,
                        matter_name=matter.name if matter else None,
                        cells=cells,
                    )
                )

            result_rows.append(
                ForecastMemberRow(
                    member_id=member.id,
                    member_name=member.name,
                    employee_code=member.employee_code,
                    monthly_sums={k: float(v) for k, v in raw_sums.items()},
                    projects=project_rows,
                )
            )

        return ForecastWorkloadResponse(months=months, rows=result_rows)

    def save_simulation(
        self, db: Session, updates: list[SimulationUpdateItem]
    ) -> None:
        for item in updates:
            wl = db.execute(
                select(MonthlyWorkload).where(
                    MonthlyWorkload.member_id == item.member_id,
                    MonthlyWorkload.project_id == item.project_id,
                    MonthlyWorkload.year == item.year,
                    MonthlyWorkload.month == item.month,
                )
            ).scalar_one_or_none()
            if wl is not None:
                wl.simulated_mm = item.simulated_mm
            else:
                db.add(MonthlyWorkload(
                    member_id=item.member_id,
                    project_id=item.project_id,
                    year=item.year,
                    month=item.month,
                    simulated_mm=item.simulated_mm,
                ))
        db.commit()

    def reset_simulation(
        self, db: Session, member_id: int | None, project_id: int | None
    ) -> None:
        stmt = update(MonthlyWorkload).values(simulated_mm=None)
        if member_id is not None:
            stmt = stmt.where(MonthlyWorkload.member_id == member_id)
        if project_id is not None:
            stmt = stmt.where(MonthlyWorkload.project_id == project_id)
        db.execute(stmt)
        db.commit()

    # 会計年度の月列（アップロードCSVと同じ順序）
    _MONTH_COLS = [
        "4月", "5月", "6月", "7月", "8月", "9月",
        "10月", "11月", "12月", "1月", "2月", "3月",
    ]

    def download_forecast_csv(
        self,
        db: Session,
        dept_id: int | None,
        team_id: int | None,
        year_from: int,
        month_from: int,
        year_to: int,
        month_to: int,
        project_id: int | None = None,
    ) -> bytes:
        """計画工数CSVと同一フォーマット（Shift-JIS、会計年度×月列）でダウンロードする。"""
        ym_from = year_from * 100 + month_from
        ym_to = year_to * 100 + month_to

        stmt = (
            select(MonthlyWorkload)
            .join(MonthlyWorkload.member)
            .join(Member.department)
            .join(MonthlyWorkload.project)
            .options(
                joinedload(MonthlyWorkload.member).joinedload(Member.department),
                joinedload(MonthlyWorkload.project),
            )
            .where(
                (MonthlyWorkload.year * 100 + MonthlyWorkload.month) >= ym_from,
                (MonthlyWorkload.year * 100 + MonthlyWorkload.month) <= ym_to,
            )
            .order_by(
                Member.employee_code,
                Project.wbs_tmp,
                MonthlyWorkload.year,
                MonthlyWorkload.month,
            )
        )

        if dept_id is not None:
            stmt = stmt.where(Member.department_id == dept_id)

        if team_id is not None:
            team_member_subq = select(TeamMember.member_id).where(
                TeamMember.team_id == team_id
            )
            stmt = stmt.where(MonthlyWorkload.member_id.in_(team_member_subq))

        if project_id is not None:
            stmt = stmt.where(MonthlyWorkload.project_id == project_id)

        workloads = db.execute(stmt).scalars().unique().all()

        # (社員コード, WBS仮コード, 会計年度) → 月列値
        rows_map: dict[tuple[str, str, int], dict[str, Decimal]] = {}
        # メタ情報（部門・氏名・WBS名称）を保持
        meta_map: dict[tuple[str, str, int], tuple[str, str, str, str, str, str]] = {}

        for wl in workloads:
            forecast_mm: Decimal | None = (
                wl.simulated_mm if wl.simulated_mm is not None else wl.planned_mm
            )
            if forecast_mm is None:
                continue

            month = wl.month
            year = wl.year
            fy = year if month >= 4 else year - 1
            month_col = f"{month}月"

            member = wl.member
            project = wl.project
            dept = member.department
            group_key = (member.employee_code, project.wbs_tmp, fy)

            if group_key not in rows_map:
                rows_map[group_key] = {col: Decimal(0) for col in self._MONTH_COLS}
                meta_map[group_key] = (
                    dept.code, dept.name,
                    member.employee_code, member.name,
                    project.wbs_tmp, project.name,
                )
            rows_map[group_key][month_col] = forecast_mm

        headers = [
            "所属部門コード", "所属部門名", "社員コード", "氏名",
            "WBS仮コード", "WBS名称", "会計年度",
            *self._MONTH_COLS,
        ]
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=headers)
        writer.writeheader()

        for group_key, month_vals in rows_map.items():
            dept_code, dept_name, emp_code, emp_name, wbs_tmp, proj_name = meta_map[group_key]
            _, _, fy = group_key
            row: dict[str, object] = {
                "所属部門コード": dept_code,
                "所属部門名": dept_name,
                "社員コード": emp_code,
                "氏名": emp_name,
                "WBS仮コード": wbs_tmp,
                "WBS名称": proj_name,
                "会計年度": fy,
            }
            for col in self._MONTH_COLS:
                row[col] = f"{month_vals[col]:.2f}"
            writer.writerow(row)

        return buf.getvalue().encode("shift_jis")
