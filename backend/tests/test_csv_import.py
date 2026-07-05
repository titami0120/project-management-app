"""CsvImportService のupsert・ForecastService の統合テスト"""
import csv
import io
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.forecast_snapshot import ForecastSnapshot
from app.models.forecast_version import ForecastVersion
from app.models.member import Member
from app.models.monthly_workload import MonthlyWorkload
from app.models.project import Project
from app.services.csv_import_service import CsvImportService
from app.services.exceptions import CsvValidationException
from app.services.forecast_service import ForecastService

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

REQUIRED_HEADERS = [
    "所属部門コード", "所属部門名", "社員コード", "氏名",
    "WBS仮コード", "WBS名称", "会計年度",
    "4月", "5月", "6月", "7月", "8月", "9月",
    "10月", "11月", "12月", "1月", "2月", "3月",
]


def _make_csv(rows: list[dict[str, str]], extra_headers: list[str] | None = None) -> bytes:
    headers = REQUIRED_HEADERS + (extra_headers or [])
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=headers, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buf.getvalue().encode("shift_jis")


def _row(
    dept_code: str = "D01", dept_name: str = "開発部",
    emp_code: str = "E001", emp_name: str = "山田太郎",
    wbs_tmp: str = "WBS-001", wbs_name: str = "システム開発",
    fy: str = "2026",
    apr: str = "1.00", may: str = "0.00", jun: str = "0.00",
    jul: str = "0.00", aug: str = "0.00", sep: str = "0.00",
    oct: str = "0.00", nov: str = "0.00", dec: str = "0.00",
    jan: str = "0.00", feb: str = "0.00", mar: str = "0.00",
    wbs_code: str = "",
) -> dict[str, str]:
    return {
        "所属部門コード": dept_code, "所属部門名": dept_name,
        "社員コード": emp_code, "氏名": emp_name,
        "WBS仮コード": wbs_tmp, "WBS名称": wbs_name,
        "WBSコード": wbs_code, "会計年度": fy,
        "4月": apr, "5月": may, "6月": jun, "7月": jul, "8月": aug,
        "9月": sep, "10月": oct, "11月": nov, "12月": dec,
        "1月": jan, "2月": feb, "3月": mar,
    }


service = CsvImportService()


# ---------------------------------------------------------------------------
# タスク3.2: マスタデータupsert
# ---------------------------------------------------------------------------

class TestMasterUpsert:
    def test_new_department_is_inserted(self, db_session: Session) -> None:
        csv_bytes = _make_csv([_row()], extra_headers=["WBSコード"])
        service.import_plan_csv(csv_bytes, db_session)
        depts = db_session.query(Department).all()
        assert len(depts) == 1
        assert depts[0].code == "D01"
        assert depts[0].name == "開発部"

    def test_existing_department_name_is_updated(self, db_session: Session) -> None:
        csv_bytes = _make_csv([_row()], extra_headers=["WBSコード"])
        service.import_plan_csv(csv_bytes, db_session)
        csv2 = _make_csv([_row(dept_name="開発部（更新）")], extra_headers=["WBSコード"])
        service.import_plan_csv(csv2, db_session)
        depts = db_session.query(Department).all()
        assert len(depts) == 1
        assert depts[0].name == "開発部（更新）"

    def test_department_is_deleted_flag_not_changed_on_update(self, db_session: Session) -> None:
        csv_bytes = _make_csv([_row()], extra_headers=["WBSコード"])
        service.import_plan_csv(csv_bytes, db_session)
        dept = db_session.query(Department).first()
        assert dept is not None
        dept.is_deleted = True
        db_session.commit()
        csv2 = _make_csv([_row(dept_name="開発部（更新）")], extra_headers=["WBSコード"])
        service.import_plan_csv(csv2, db_session)
        db_session.expire_all()
        dept = db_session.query(Department).first()
        assert dept is not None
        assert dept.is_deleted is True

    def test_new_member_is_inserted(self, db_session: Session) -> None:
        csv_bytes = _make_csv([_row()], extra_headers=["WBSコード"])
        service.import_plan_csv(csv_bytes, db_session)
        members = db_session.query(Member).all()
        assert len(members) == 1
        assert members[0].employee_code == "E001"
        assert members[0].name == "山田太郎"

    def test_existing_member_name_is_updated(self, db_session: Session) -> None:
        csv_bytes = _make_csv([_row()], extra_headers=["WBSコード"])
        service.import_plan_csv(csv_bytes, db_session)
        csv2 = _make_csv([_row(emp_name="山田次郎")], extra_headers=["WBSコード"])
        service.import_plan_csv(csv2, db_session)
        members = db_session.query(Member).all()
        assert len(members) == 1
        assert members[0].name == "山田次郎"

    def test_new_project_is_inserted(self, db_session: Session) -> None:
        csv_bytes = _make_csv([_row()], extra_headers=["WBSコード"])
        service.import_plan_csv(csv_bytes, db_session)
        projects = db_session.query(Project).all()
        assert len(projects) == 1
        assert projects[0].wbs_tmp == "WBS-001"
        assert projects[0].matter_id is None

    def test_new_project_with_wbs_code_sets_code(self, db_session: Session) -> None:
        csv_bytes = _make_csv([_row(wbs_code="WBS-001-REAL")], extra_headers=["WBSコード"])
        service.import_plan_csv(csv_bytes, db_session)
        project = db_session.query(Project).first()
        assert project is not None
        assert project.code == "WBS-001-REAL"

    def test_existing_project_name_is_updated(self, db_session: Session) -> None:
        csv_bytes = _make_csv([_row()], extra_headers=["WBSコード"])
        service.import_plan_csv(csv_bytes, db_session)
        csv2 = _make_csv([_row(wbs_name="更新後名称")], extra_headers=["WBSコード"])
        service.import_plan_csv(csv2, db_session)
        project = db_session.query(Project).first()
        assert project is not None
        assert project.name == "更新後名称"

    def test_import_returns_summary_counts(self, db_session: Session) -> None:
        csv_bytes = _make_csv([_row()], extra_headers=["WBSコード"])
        result = service.import_plan_csv(csv_bytes, db_session)
        assert result.summary.departments.created == 1
        assert result.summary.members.created == 1
        assert result.summary.projects.created == 1


# ---------------------------------------------------------------------------
# タスク3.3: 月次工数upsert
# ---------------------------------------------------------------------------

class TestMonthlyWorkloadUpsert:
    def test_positive_workload_is_inserted(self, db_session: Session) -> None:
        csv_bytes = _make_csv([_row(apr="1.00")], extra_headers=["WBSコード"])
        service.import_plan_csv(csv_bytes, db_session)
        records = db_session.query(MonthlyWorkload).all()
        assert any(r.month == 4 and r.planned_mm == Decimal("1.00") for r in records)

    def test_zero_workload_is_not_inserted(self, db_session: Session) -> None:
        csv_bytes = _make_csv([_row(apr="0.00")], extra_headers=["WBSコード"])
        service.import_plan_csv(csv_bytes, db_session)
        records = db_session.query(MonthlyWorkload).filter_by(month=4).all()
        assert len(records) == 0

    def test_zero_workload_updates_existing_record(self, db_session: Session) -> None:
        csv_bytes = _make_csv([_row(apr="1.00")], extra_headers=["WBSコード"])
        service.import_plan_csv(csv_bytes, db_session)
        csv2 = _make_csv([_row(apr="0.00")], extra_headers=["WBSコード"])
        service.import_plan_csv(csv2, db_session)
        records = db_session.query(MonthlyWorkload).filter_by(month=4).all()
        assert len(records) == 1
        assert records[0].planned_mm == Decimal("0.00")

    def test_simulated_mm_not_changed_on_update(self, db_session: Session) -> None:
        csv_bytes = _make_csv([_row(apr="1.00")], extra_headers=["WBSコード"])
        service.import_plan_csv(csv_bytes, db_session)
        record = db_session.query(MonthlyWorkload).filter_by(month=4).first()
        assert record is not None
        record.simulated_mm = Decimal("0.50")
        db_session.commit()
        csv2 = _make_csv([_row(apr="2.00")], extra_headers=["WBSコード"])
        service.import_plan_csv(csv2, db_session)
        db_session.expire_all()
        record = db_session.query(MonthlyWorkload).filter_by(month=4).first()
        assert record is not None
        assert record.simulated_mm == Decimal("0.50")
        assert record.planned_mm == Decimal("2.00")

    def test_fiscal_year_conversion_april(self, db_session: Session) -> None:
        csv_bytes = _make_csv([_row(fy="2026", apr="1.00")], extra_headers=["WBSコード"])
        service.import_plan_csv(csv_bytes, db_session)
        r = db_session.query(MonthlyWorkload).filter_by(year=2026, month=4).first()
        assert r is not None

    def test_fiscal_year_conversion_january_is_fy_plus_1(self, db_session: Session) -> None:
        csv_bytes = _make_csv([_row(fy="2026", jan="1.00")], extra_headers=["WBSコード"])
        service.import_plan_csv(csv_bytes, db_session)
        r = db_session.query(MonthlyWorkload).filter_by(year=2027, month=1).first()
        assert r is not None

    def test_all_zero_row_creates_master_but_no_workloads(self, db_session: Session) -> None:
        csv_bytes = _make_csv([_row(apr="0.00")], extra_headers=["WBSコード"])
        service.import_plan_csv(csv_bytes, db_session)
        assert db_session.query(Department).count() == 1
        assert db_session.query(Member).count() == 1
        assert db_session.query(Project).count() == 1
        assert db_session.query(MonthlyWorkload).count() == 0


# ---------------------------------------------------------------------------
# バージョン保存とスナップショット（CSVアップロードでは作成しない）
# ---------------------------------------------------------------------------

forecast_service = ForecastService()


class TestForecastVersionAndSnapshot:
    def test_csv_upload_creates_version(self, db_session: Session) -> None:
        csv_bytes = _make_csv([_row(apr="1.00")], extra_headers=["WBSコード"])
        result = service.import_plan_csv(csv_bytes, db_session, version_name="テスト版")
        assert result.version_no == 1
        versions = db_session.query(ForecastVersion).all()
        assert len(versions) == 1
        assert versions[0].name == "テスト版"

    def test_csv_upload_creates_snapshot(self, db_session: Session) -> None:
        csv_bytes = _make_csv([_row(apr="1.00")], extra_headers=["WBSコード"])
        service.import_plan_csv(csv_bytes, db_session, version_name="テスト版")
        snapshots = db_session.query(ForecastSnapshot).all()
        assert len(snapshots) == 1
        assert snapshots[0].forecast_mm == Decimal("1.00")

    def test_second_upload_increments_version_no(self, db_session: Session) -> None:
        csv_bytes = _make_csv([_row(apr="1.00")], extra_headers=["WBSコード"])
        service.import_plan_csv(csv_bytes, db_session, version_name="v1")
        result2 = service.import_plan_csv(csv_bytes, db_session, version_name="v2")
        assert result2.version_no == 2

    def test_snapshot_uses_planned_mm_not_simulated(self, db_session: Session) -> None:
        csv_bytes = _make_csv([_row(apr="1.00")], extra_headers=["WBSコード"])
        service.import_plan_csv(csv_bytes, db_session, version_name="テスト版")
        record = db_session.query(MonthlyWorkload).first()
        assert record is not None
        record.simulated_mm = Decimal("0.75")
        db_session.commit()
        forecast_service.create_version_with_snapshot(db_session, name="追加版")
        # CSV upload snapshot (v1) は simulated_mm 設定前なので planned_mm=1.00
        snap_v1 = db_session.query(ForecastSnapshot).filter_by(
            version_id=db_session.query(ForecastVersion).filter_by(version_no=1).first().id, month=4
        ).first()
        assert snap_v1 is not None
        assert snap_v1.forecast_mm == Decimal("1.00")

    def test_restore_from_version(self, db_session: Session) -> None:
        csv_bytes = _make_csv([_row(apr="1.00")], extra_headers=["WBSコード"])
        service.import_plan_csv(csv_bytes, db_session, version_name="テスト版")
        version = db_session.query(ForecastVersion).first()
        record = db_session.query(MonthlyWorkload).first()
        assert record is not None
        record.planned_mm = Decimal("0.50")
        db_session.commit()
        restored = forecast_service.restore_from_version(db_session, version.id)
        assert restored == 1
        db_session.expire_all()
        record = db_session.query(MonthlyWorkload).first()
        assert record is not None
        assert record.planned_mm == Decimal("1.00")
        assert record.simulated_mm is None

    def test_restore_deletes_extra_records(self, db_session: Session) -> None:
        """スナップショット後に追加されたレコードは復元時に削除される"""
        csv_bytes = _make_csv([_row(apr="1.00")], extra_headers=["WBSコード"])
        service.import_plan_csv(csv_bytes, db_session, version_name="v1")
        # CSV upload で作成されたバージョン（snapshot: 4月の1件）を取得
        version = db_session.query(ForecastVersion).filter_by(version_no=1).first()

        # スナップショット後にレコードを追加
        existing = db_session.query(MonthlyWorkload).first()
        assert existing is not None
        extra = MonthlyWorkload(
            member_id=existing.member_id,
            project_id=existing.project_id,
            year=existing.year,
            month=5,
            planned_mm=Decimal("0.30"),
        )
        db_session.add(extra)
        db_session.commit()
        assert db_session.query(MonthlyWorkload).count() == 2

        forecast_service.restore_from_version(db_session, version.id)
        db_session.expire_all()
        assert db_session.query(MonthlyWorkload).count() == 1


# ---------------------------------------------------------------------------
# ロールバック検証
# ---------------------------------------------------------------------------

class TestRollback:
    def test_validation_error_prevents_any_db_write(self, db_session: Session) -> None:
        bad_csv = _make_csv([_row(fy="bad_year", apr="1.00")], extra_headers=["WBSコード"])
        with pytest.raises(CsvValidationException):
            service.import_plan_csv(bad_csv, db_session)
        assert db_session.query(Department).count() == 0
        assert db_session.query(Member).count() == 0
        assert db_session.query(Project).count() == 0
        assert db_session.query(MonthlyWorkload).count() == 0
