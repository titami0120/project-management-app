import csv
import io
from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.member import Member
from app.models.monthly_workload import MonthlyWorkload
from app.models.project import Project
from app.schemas.workload_schema import (
    CsvUploadResponse,
    CsvValidationError,
    ImportCount,
    ImportSummary,
)
from app.services.exceptions import CsvValidationException
from app.services.forecast_service import ForecastService
REQUIRED_HEADERS: list[str] = [
    "所属部門コード", "所属部門名", "社員コード", "氏名",
    "WBS仮コード", "WBS名称", "会計年度",
    "4月", "5月", "6月", "7月", "8月", "9月",
    "10月", "11月", "12月", "1月", "2月", "3月",
]

MONTH_COLS: list[str] = [
    "4月", "5月", "6月", "7月", "8月", "9月",
    "10月", "11月", "12月", "1月", "2月", "3月",
]

REQUIRED_STR_COLS: list[str] = [
    "所属部門コード", "所属部門名", "社員コード", "氏名", "WBS仮コード", "WBS名称",
]

# 月列名 → (year_offset, month_number)
_MONTH_MAP: dict[str, tuple[int, int]] = {
    "4月": (0, 4), "5月": (0, 5), "6月": (0, 6), "7月": (0, 7),
    "8月": (0, 8), "9月": (0, 9), "10月": (0, 10), "11月": (0, 11),
    "12月": (0, 12), "1月": (1, 1), "2月": (1, 2), "3月": (1, 3),
}


class CsvImportService:
    def __init__(self) -> None:
        self._forecast_service = ForecastService()

    # ------------------------------------------------------------------
    # 公開: メインエントリ
    # ------------------------------------------------------------------

    def import_plan_csv(
        self,
        file_content: bytes,
        db: Session,
        version_name: str | None = None,
        version_description: str | None = None,
    ) -> CsvUploadResponse:
        """CSVをインポートし、バリデーション → upsert → バージョン作成 を行う。"""
        fieldnames, rows = self._validate_and_parse(file_content)
        has_wbs_code = "WBSコード" in fieldnames

        try:
            summary = self._upsert_all(rows, has_wbs_code, db)
            db.flush()
            name = version_name or "CSV インポート"
            version_no = self._forecast_service.create_version_with_snapshot(
                db, name=name, description=version_description
            )
        except Exception:
            db.rollback()
            raise

        return CsvUploadResponse(version_no=version_no, summary=summary)

    # ------------------------------------------------------------------
    # 公開: バリデーション + パース
    # ------------------------------------------------------------------

    def _validate_and_parse(
        self, file_content: bytes
    ) -> tuple[list[str], list[dict[str, str]]]:
        for encoding in ("cp932", "utf-8-sig", "utf-8"):
            try:
                text = file_content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise CsvValidationException(["ファイルのエンコーディングを判別できません。CP932 (Shift-JIS) または UTF-8 で保存してください。"])
        reader = csv.DictReader(io.StringIO(text))
        fieldnames: list[str] = list(reader.fieldnames or [])

        header_errors = self._validate_headers(fieldnames)
        if header_errors:
            raise CsvValidationException(header_errors)

        rows = list(reader)
        row_errors = self._validate_rows(rows)
        if row_errors:
            raise CsvValidationException(row_errors)

        return fieldnames, rows

    # ------------------------------------------------------------------
    # ヘッダー検証
    # ------------------------------------------------------------------

    def _validate_headers(self, headers: list[str]) -> list[CsvValidationError]:
        errors: list[CsvValidationError] = []
        header_set = set(headers)
        for col in REQUIRED_HEADERS:
            if col not in header_set:
                errors.append(CsvValidationError(
                    row_no=None,
                    column=col,
                    message=f'列"{col}"が見つかりません',
                ))
        return errors

    # ------------------------------------------------------------------
    # 行バリデーション
    # ------------------------------------------------------------------

    def _validate_rows(self, rows: list[dict[str, str]]) -> list[CsvValidationError]:
        errors: list[CsvValidationError] = []
        for row_idx, row in enumerate(rows, start=1):
            errors.extend(self._validate_row(row_idx, row))
        return errors

    def _validate_row(self, row_no: int, row: dict[str, str]) -> list[CsvValidationError]:
        errors: list[CsvValidationError] = []

        for col in REQUIRED_STR_COLS:
            if not row.get(col, "").strip():
                errors.append(CsvValidationError(
                    row_no=row_no,
                    column=col,
                    message=f"{col}は空にできません",
                ))

        fy_val = row.get("会計年度", "").strip()
        try:
            fy = int(fy_val)
            if not (1900 <= fy <= 2100):
                raise ValueError
        except (ValueError, TypeError):
            errors.append(CsvValidationError(
                row_no=row_no,
                column="会計年度",
                message=(
                    f"会計年度の値が不正です: '{fy_val}'"
                    "（整数で1900〜2100の範囲を指定してください）"
                ),
            ))

        for col in MONTH_COLS:
            val = row.get(col, "").strip()
            try:
                num = Decimal(val)
                if num < 0:
                    raise ValueError
            except (InvalidOperation, ValueError):
                errors.append(CsvValidationError(
                    row_no=row_no,
                    column=col,
                    message=f"{col}の値が不正です: '{val}'（0以上の数値を指定してください）",
                ))

        return errors

    # ------------------------------------------------------------------
    # DB upsert オーケストレーション
    # ------------------------------------------------------------------

    def _upsert_all(
        self, rows: list[dict[str, str]], has_wbs_code: bool, db: Session
    ) -> ImportSummary:
        dept_counts = self._upsert_departments(rows, db)
        member_counts = self._upsert_members(rows, db)
        project_counts = self._upsert_projects(rows, has_wbs_code, db)
        workload_counts = self._upsert_monthly_workloads(rows, db)
        return ImportSummary(
            departments=dept_counts,
            members=member_counts,
            projects=project_counts,
            workloads=workload_counts,
        )

    def _upsert_departments(
        self, rows: list[dict[str, str]], db: Session
    ) -> ImportCount:
        seen: set[str] = set()
        unique_depts: list[dict[str, str]] = []
        for row in rows:
            code = row["所属部門コード"].strip()
            if code not in seen:
                seen.add(code)
                unique_depts.append({"code": code, "name": row["所属部門名"].strip()})

        existing_codes = {
            r[0] for r in db.execute(select(Department.code)).all()
        }
        created = updated = 0
        for dept in unique_depts:
            stmt = (
                sqlite_insert(Department)
                .values(code=dept["code"], name=dept["name"], is_deleted=False)
                .on_conflict_do_update(
                    index_elements=["code"],
                    set_={"name": dept["name"], "is_deleted": False},
                )
            )
            db.execute(stmt)
            if dept["code"] in existing_codes:
                updated += 1
            else:
                created += 1
        db.flush()
        return ImportCount(created=created, updated=updated)

    def _upsert_members(
        self, rows: list[dict[str, str]], db: Session
    ) -> ImportCount:
        dept_map: dict[str, int] = {
            r[0]: r[1]
            for r in db.execute(select(Department.code, Department.id)).all()
        }
        seen: set[str] = set()
        unique_members: list[dict] = []  # type: ignore[type-arg]
        for row in rows:
            code = row["社員コード"].strip()
            if code not in seen:
                seen.add(code)
                dept_id = dept_map[row["所属部門コード"].strip()]
                unique_members.append({
                    "employee_code": code,
                    "name": row["氏名"].strip(),
                    "department_id": dept_id,
                })

        existing_codes = {
            r[0] for r in db.execute(select(Member.employee_code)).all()
        }
        created = updated = 0
        for m in unique_members:
            stmt = (
                sqlite_insert(Member)
                .values(
                    employee_code=m["employee_code"],
                    name=m["name"],
                    department_id=m["department_id"],
                    is_deleted=False,
                )
                .on_conflict_do_update(
                    index_elements=["employee_code"],
                    set_={"name": m["name"], "department_id": m["department_id"], "is_deleted": False},
                )
            )
            db.execute(stmt)
            if m["employee_code"] in existing_codes:
                updated += 1
            else:
                created += 1
        db.flush()
        return ImportCount(created=created, updated=updated)

    def _upsert_projects(
        self, rows: list[dict[str, str]], has_wbs_code: bool, db: Session
    ) -> ImportCount:
        seen: set[str] = set()
        unique_projects: list[dict] = []  # type: ignore[type-arg]
        for row in rows:
            wbs_tmp = row["WBS仮コード"].strip()
            if wbs_tmp not in seen:
                seen.add(wbs_tmp)
                wbs_code: str | None = None
                if has_wbs_code:
                    raw = row.get("WBSコード", "").strip()
                    wbs_code = raw if raw else None
                unique_projects.append({
                    "wbs_tmp": wbs_tmp,
                    "name": row["WBS名称"].strip(),
                    "code": wbs_code,
                })

        existing_wbs = {
            r[0] for r in db.execute(select(Project.wbs_tmp)).all()
        }
        created = updated = 0
        for p in unique_projects:
            insert_vals: dict = {  # type: ignore[type-arg]
                "wbs_tmp": p["wbs_tmp"],
                "name": p["name"],
                "matter_id": None,
                "is_deleted": False,
            }
            update_vals: dict = {"name": p["name"]}  # type: ignore[type-arg]
            if p["code"] is not None:
                insert_vals["code"] = p["code"]
                update_vals["code"] = p["code"]

            stmt = (
                sqlite_insert(Project)
                .values(**insert_vals)
                .on_conflict_do_update(
                    index_elements=["wbs_tmp"],
                    set_=update_vals,
                )
            )
            db.execute(stmt)
            if p["wbs_tmp"] in existing_wbs:
                updated += 1
            else:
                created += 1
        db.flush()
        return ImportCount(created=created, updated=updated)

    def _upsert_monthly_workloads(
        self, rows: list[dict[str, str]], db: Session
    ) -> ImportCount:
        member_map: dict[str, int] = {
            r[0]: r[1]
            for r in db.execute(select(Member.employee_code, Member.id)).all()
        }
        project_map: dict[str, int] = {
            r[0]: r[1]
            for r in db.execute(select(Project.wbs_tmp, Project.id)).all()
        }

        existing_keys: set[tuple[int, int, int, int]] = {
            (r[0], r[1], r[2], r[3])
            for r in db.execute(
                select(
                    MonthlyWorkload.member_id,
                    MonthlyWorkload.project_id,
                    MonthlyWorkload.year,
                    MonthlyWorkload.month,
                )
            ).all()
        }

        created = updated = 0
        for row in rows:
            fy = int(row["会計年度"].strip())
            member_id = member_map[row["社員コード"].strip()]
            project_id = project_map[row["WBS仮コード"].strip()]

            for col, (year_offset, month) in _MONTH_MAP.items():
                year = fy + year_offset
                val = Decimal(row[col].strip())
                key = (member_id, project_id, year, month)

                if key in existing_keys:
                    db.execute(
                        MonthlyWorkload.__table__.update()
                        .where(
                            (MonthlyWorkload.member_id == member_id)
                            & (MonthlyWorkload.project_id == project_id)
                            & (MonthlyWorkload.year == year)
                            & (MonthlyWorkload.month == month)
                        )
                        .values(planned_mm=val)
                    )
                    updated += 1
                elif val > 0:
                    db.execute(
                        MonthlyWorkload.__table__.insert().values(
                            member_id=member_id,
                            project_id=project_id,
                            year=year,
                            month=month,
                            planned_mm=val,
                        )
                    )
                    existing_keys.add(key)
                    created += 1

        db.flush()
        return ImportCount(created=created, updated=updated)
