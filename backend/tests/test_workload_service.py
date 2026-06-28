"""WorkloadService.get_forecast() のユニットテスト"""
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.matter import Matter
from app.models.member import Member
from app.models.monthly_workload import MonthlyWorkload
from app.models.project import Project
from app.models.team import Team
from app.models.team_member import TeamMember
from app.services.workload_service import WorkloadService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _dept(db: Session, code: str = "D01", name: str = "開発部") -> Department:
    dept = Department(code=code, name=name)
    db.add(dept)
    db.flush()
    return dept


def _member(
    db: Session,
    dept: Department,
    code: str = "E001",
    name: str = "山田太郎",
) -> Member:
    m = Member(employee_code=code, name=name, department_id=dept.id)
    db.add(m)
    db.flush()
    return m


def _project(
    db: Session,
    wbs_tmp: str = "WBS-001",
    name: str = "システム開発",
    matter: Matter | None = None,
) -> Project:
    p = Project(
        wbs_tmp=wbs_tmp,
        name=name,
        matter_id=matter.id if matter else None,
    )
    db.add(p)
    db.flush()
    return p


def _workload(
    db: Session,
    member: Member,
    project: Project,
    year: int,
    month: int,
    planned_mm: Decimal | None = None,
    simulated_mm: Decimal | None = None,
) -> MonthlyWorkload:
    wl = MonthlyWorkload(
        member_id=member.id,
        project_id=project.id,
        year=year,
        month=month,
        planned_mm=planned_mm,
        simulated_mm=simulated_mm,
    )
    db.add(wl)
    db.flush()
    return wl


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestGetForecastMonthsList:
    def test_months_list_single_month(self, db_session: Session) -> None:
        """fromとtoが同じ月の場合、1件のmonthsリストが返る"""
        svc = WorkloadService()
        result = svc.get_forecast(db_session, None, None, 2025, 4, 2025, 4)
        assert result.months == ["2025-04"]

    def test_months_list_multiple_months(self, db_session: Session) -> None:
        """複数月の範囲で正しいmonthsリストが返る"""
        svc = WorkloadService()
        result = svc.get_forecast(db_session, None, None, 2025, 11, 2026, 2)
        assert result.months == ["2025-11", "2025-12", "2026-01", "2026-02"]

    def test_months_list_full_year(self, db_session: Session) -> None:
        """1年分（4月〜3月）のmonthsリストが12件"""
        svc = WorkloadService()
        result = svc.get_forecast(db_session, None, None, 2025, 4, 2026, 3)
        assert len(result.months) == 12
        assert result.months[0] == "2025-04"
        assert result.months[-1] == "2026-03"


class TestGetForecastEmptyDb:
    def test_empty_db_returns_empty_rows(self, db_session: Session) -> None:
        """DBにデータがない場合は空のrowsを返す"""
        svc = WorkloadService()
        result = svc.get_forecast(db_session, None, None, 2025, 4, 2025, 9)
        assert result.rows == []
        assert len(result.months) == 6


class TestGetForecastForecastMm:
    def test_forecast_mm_uses_planned_when_simulated_is_none(
        self, db_session: Session
    ) -> None:
        """simulated_mmがNULLのとき forecast_mm = planned_mm"""
        dept = _dept(db_session)
        member = _member(db_session, dept)
        project = _project(db_session)
        _workload(
            db_session, member, project, 2025, 4,
            planned_mm=Decimal("1.00"), simulated_mm=None
        )
        db_session.commit()

        svc = WorkloadService()
        result = svc.get_forecast(db_session, None, None, 2025, 4, 2025, 4)

        assert len(result.rows) == 1
        row = result.rows[0]
        assert len(row.projects) == 1
        cell = row.projects[0].cells["2025-04"]
        assert cell.forecast_mm == Decimal("1.00")
        assert cell.planned_mm == Decimal("1.00")
        assert cell.simulated_mm is None

    def test_forecast_mm_uses_simulated_when_set(
        self, db_session: Session
    ) -> None:
        """simulated_mmが設定されているとき forecast_mm = simulated_mm"""
        dept = _dept(db_session)
        member = _member(db_session, dept)
        project = _project(db_session)
        _workload(
            db_session, member, project, 2025, 4,
            planned_mm=Decimal("1.00"), simulated_mm=Decimal("0.50")
        )
        db_session.commit()

        svc = WorkloadService()
        result = svc.get_forecast(db_session, None, None, 2025, 4, 2025, 4)

        cell = result.rows[0].projects[0].cells["2025-04"]
        assert cell.forecast_mm == Decimal("0.50")
        assert cell.planned_mm == Decimal("1.00")
        assert cell.simulated_mm == Decimal("0.50")

    def test_forecast_mm_simulated_zero_overrides_planned(
        self, db_session: Session
    ) -> None:
        """simulated_mm=0.00 のとき forecast_mm=0.00（0.00でもsimulatedが優先）"""
        dept = _dept(db_session)
        member = _member(db_session, dept)
        project = _project(db_session)
        _workload(
            db_session, member, project, 2025, 4,
            planned_mm=Decimal("1.00"), simulated_mm=Decimal("0.00")
        )
        db_session.commit()

        svc = WorkloadService()
        result = svc.get_forecast(db_session, None, None, 2025, 4, 2025, 4)

        cell = result.rows[0].projects[0].cells["2025-04"]
        assert cell.forecast_mm == Decimal("0.00")


class TestGetForecastRangeFilter:
    def test_only_months_in_range_are_included(self, db_session: Session) -> None:
        """期間外の月のデータはcellsに含まれない"""
        dept = _dept(db_session)
        member = _member(db_session, dept)
        project = _project(db_session)
        # 期間内: 2025-04
        _workload(db_session, member, project, 2025, 4, planned_mm=Decimal("1.00"))
        # 期間外: 2025-06
        _workload(db_session, member, project, 2025, 6, planned_mm=Decimal("0.50"))
        db_session.commit()

        svc = WorkloadService()
        result = svc.get_forecast(db_session, None, None, 2025, 4, 2025, 5)

        cells = result.rows[0].projects[0].cells
        assert "2025-04" in cells
        assert "2025-06" not in cells

    def test_cross_year_range(self, db_session: Session) -> None:
        """年をまたぐ期間フィルタが正しく動作する"""
        dept = _dept(db_session)
        member = _member(db_session, dept)
        project = _project(db_session)
        _workload(db_session, member, project, 2025, 12, planned_mm=Decimal("1.00"))
        _workload(db_session, member, project, 2026, 1, planned_mm=Decimal("0.50"))
        _workload(db_session, member, project, 2026, 4, planned_mm=Decimal("0.30"))
        db_session.commit()

        svc = WorkloadService()
        result = svc.get_forecast(db_session, None, None, 2025, 12, 2026, 2)

        cells = result.rows[0].projects[0].cells
        assert "2025-12" in cells
        assert "2026-01" in cells
        assert "2026-04" not in cells


class TestGetForecastDeptFilter:
    def test_dept_filter_returns_only_target_dept_members(
        self, db_session: Session
    ) -> None:
        """dept_idフィルタで対象部門の要員のみが返る"""
        dept1 = _dept(db_session, code="D01", name="開発部")
        dept2 = _dept(db_session, code="D02", name="営業部")
        member1 = _member(db_session, dept1, code="E001", name="田中一郎")
        member2 = _member(db_session, dept2, code="E002", name="佐藤二郎")
        project = _project(db_session)
        _workload(db_session, member1, project, 2025, 4, planned_mm=Decimal("1.00"))
        _workload(db_session, member2, project, 2025, 4, planned_mm=Decimal("0.50"))
        db_session.commit()

        svc = WorkloadService()
        result = svc.get_forecast(db_session, dept1.id, None, 2025, 4, 2025, 4)

        assert len(result.rows) == 1
        assert result.rows[0].member_id == member1.id

    def test_no_dept_filter_returns_all_members(self, db_session: Session) -> None:
        """dept_id=Noneのとき全要員が返る"""
        dept1 = _dept(db_session, code="D01", name="開発部")
        dept2 = _dept(db_session, code="D02", name="営業部")
        member1 = _member(db_session, dept1, code="E001", name="田中一郎")
        member2 = _member(db_session, dept2, code="E002", name="佐藤二郎")
        project = _project(db_session)
        _workload(db_session, member1, project, 2025, 4, planned_mm=Decimal("1.00"))
        _workload(db_session, member2, project, 2025, 4, planned_mm=Decimal("0.50"))
        db_session.commit()

        svc = WorkloadService()
        result = svc.get_forecast(db_session, None, None, 2025, 4, 2025, 4)

        member_ids = {r.member_id for r in result.rows}
        assert member_ids == {member1.id, member2.id}


class TestGetForecastTeamFilter:
    def test_team_filter_returns_only_team_members(
        self, db_session: Session
    ) -> None:
        """team_idフィルタでチームに所属する要員のみが返る"""
        dept = _dept(db_session)
        member1 = _member(db_session, dept, code="E001", name="田中一郎")
        member2 = _member(db_session, dept, code="E002", name="佐藤二郎")
        team = Team(name="Aチーム", department_id=dept.id)
        db_session.add(team)
        db_session.flush()
        db_session.add(TeamMember(team_id=team.id, member_id=member1.id))
        db_session.flush()

        project = _project(db_session)
        _workload(db_session, member1, project, 2025, 4, planned_mm=Decimal("1.00"))
        _workload(db_session, member2, project, 2025, 4, planned_mm=Decimal("0.50"))
        db_session.commit()

        svc = WorkloadService()
        result = svc.get_forecast(db_session, None, team.id, 2025, 4, 2025, 4)

        assert len(result.rows) == 1
        assert result.rows[0].member_id == member1.id


class TestGetForecastMonthlySums:
    def test_monthly_sums_aggregates_all_projects(self, db_session: Session) -> None:
        """同一要員の複数プロジェクトのforecast_mmが月次合計に集約される"""
        dept = _dept(db_session)
        member = _member(db_session, dept)
        project1 = _project(db_session, wbs_tmp="WBS-001", name="PJ1")
        project2 = _project(db_session, wbs_tmp="WBS-002", name="PJ2")
        _workload(db_session, member, project1, 2025, 4, planned_mm=Decimal("0.50"))
        _workload(db_session, member, project2, 2025, 4, planned_mm=Decimal("0.30"))
        db_session.commit()

        svc = WorkloadService()
        result = svc.get_forecast(db_session, None, None, 2025, 4, 2025, 4)

        row = result.rows[0]
        assert row.monthly_sums["2025-04"] == pytest.approx(0.80)

    def test_monthly_sums_per_month(self, db_session: Session) -> None:
        """月ごとに別々の合計が計算される"""
        dept = _dept(db_session)
        member = _member(db_session, dept)
        project = _project(db_session)
        _workload(db_session, member, project, 2025, 4, planned_mm=Decimal("1.00"))
        _workload(db_session, member, project, 2025, 5, planned_mm=Decimal("0.50"))
        db_session.commit()

        svc = WorkloadService()
        result = svc.get_forecast(db_session, None, None, 2025, 4, 2025, 5)

        row = result.rows[0]
        assert row.monthly_sums["2025-04"] == pytest.approx(1.00)
        assert row.monthly_sums["2025-05"] == pytest.approx(0.50)


class TestGetForecastMatterInfo:
    def test_matter_info_included_in_project_row(self, db_session: Session) -> None:
        """案件紐づきプロジェクトの matter_id・matter_name が返る"""
        dept = _dept(db_session)
        member = _member(db_session, dept)
        matter = Matter(name="テスト案件", code="M001", status="計画中")
        db_session.add(matter)
        db_session.flush()
        project = _project(db_session, matter=matter)
        _workload(db_session, member, project, 2025, 4, planned_mm=Decimal("1.00"))
        db_session.commit()

        svc = WorkloadService()
        result = svc.get_forecast(db_session, None, None, 2025, 4, 2025, 4)

        proj_row = result.rows[0].projects[0]
        assert proj_row.matter_id == matter.id
        assert proj_row.matter_name == "テスト案件"

    def test_no_matter_returns_none(self, db_session: Session) -> None:
        """案件未紐づきプロジェクトのmatter_id・matter_nameはNone"""
        dept = _dept(db_session)
        member = _member(db_session, dept)
        project = _project(db_session, matter=None)
        _workload(db_session, member, project, 2025, 4, planned_mm=Decimal("1.00"))
        db_session.commit()

        svc = WorkloadService()
        result = svc.get_forecast(db_session, None, None, 2025, 4, 2025, 4)

        proj_row = result.rows[0].projects[0]
        assert proj_row.matter_id is None
        assert proj_row.matter_name is None


class TestGetForecastMemberInfo:
    def test_member_info_in_response(self, db_session: Session) -> None:
        """レスポンスにmember_id・member_name・employee_codeが含まれる"""
        dept = _dept(db_session)
        member = _member(db_session, dept, code="E999", name="鈴木三郎")
        project = _project(db_session)
        _workload(db_session, member, project, 2025, 4, planned_mm=Decimal("1.00"))
        db_session.commit()

        svc = WorkloadService()
        result = svc.get_forecast(db_session, None, None, 2025, 4, 2025, 4)

        row = result.rows[0]
        assert row.member_id == member.id
        assert row.member_name == "鈴木三郎"
        assert row.employee_code == "E999"
