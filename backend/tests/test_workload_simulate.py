"""WorkloadService.save_simulation() / reset_simulation() のテスト"""
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.member import Member
from app.models.monthly_workload import MonthlyWorkload
from app.models.project import Project
from app.schemas.workload_schema import SimulationUpdateItem
from app.services.workload_service import WorkloadService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _dept(db: Session) -> Department:
    d = Department(code="D01", name="開発部")
    db.add(d)
    db.flush()
    return d


def _member(db: Session, dept: Department, code: str = "E001", name: str = "山田太郎") -> Member:
    m = Member(employee_code=code, name=name, department_id=dept.id)
    db.add(m)
    db.flush()
    return m


def _project(db: Session, wbs_tmp: str = "WBS-001") -> Project:
    p = Project(wbs_tmp=wbs_tmp, name="テストPJ")
    db.add(p)
    db.flush()
    return p


def _workload(
    db: Session,
    member: Member,
    project: Project,
    year: int = 2025,
    month: int = 4,
    planned_mm: Decimal | None = Decimal("1.00"),
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
# save_simulation テスト
# ---------------------------------------------------------------------------

class TestSaveSimulation:
    def test_save_updates_simulated_mm(self, db_session: Session) -> None:
        """存在するレコードの simulated_mm が更新される"""
        dept = _dept(db_session)
        member = _member(db_session, dept)
        project = _project(db_session)
        wl = _workload(db_session, member, project, 2025, 4, planned_mm=Decimal("1.00"))
        db_session.commit()

        svc = WorkloadService()
        updates = [
            SimulationUpdateItem(
                member_id=member.id,
                project_id=project.id,
                year=2025,
                month=4,
                simulated_mm=Decimal("0.50"),
            )
        ]
        svc.save_simulation(db_session, updates)

        db_session.refresh(wl)
        assert wl.simulated_mm == Decimal("0.50")

    def test_save_does_not_change_planned_mm(self, db_session: Session) -> None:
        """save_simulation は planned_mm を変更しない"""
        dept = _dept(db_session)
        member = _member(db_session, dept)
        project = _project(db_session)
        wl = _workload(db_session, member, project, 2025, 4, planned_mm=Decimal("1.00"))
        db_session.commit()

        svc = WorkloadService()
        updates = [
            SimulationUpdateItem(
                member_id=member.id,
                project_id=project.id,
                year=2025,
                month=4,
                simulated_mm=Decimal("0.30"),
            )
        ]
        svc.save_simulation(db_session, updates)

        db_session.refresh(wl)
        assert wl.planned_mm == Decimal("1.00")

    def test_save_does_not_change_actual_mm(self, db_session: Session) -> None:
        """save_simulation は actual_mm を変更しない"""
        dept = _dept(db_session)
        member = _member(db_session, dept)
        project = _project(db_session)
        wl = _workload(db_session, member, project, 2025, 4)
        wl.actual_mm = Decimal("0.80")
        db_session.commit()

        svc = WorkloadService()
        updates = [
            SimulationUpdateItem(
                member_id=member.id,
                project_id=project.id,
                year=2025,
                month=4,
                simulated_mm=Decimal("0.50"),
            )
        ]
        svc.save_simulation(db_session, updates)

        db_session.refresh(wl)
        assert wl.actual_mm == Decimal("0.80")

    def test_save_can_set_simulated_mm_to_none(self, db_session: Session) -> None:
        """simulated_mm=None でNULLに更新できる"""
        dept = _dept(db_session)
        member = _member(db_session, dept)
        project = _project(db_session)
        wl = _workload(
            db_session, member, project, 2025, 4, simulated_mm=Decimal("0.50")
        )
        db_session.commit()

        svc = WorkloadService()
        updates = [
            SimulationUpdateItem(
                member_id=member.id,
                project_id=project.id,
                year=2025,
                month=4,
                simulated_mm=None,
            )
        ]
        svc.save_simulation(db_session, updates)

        db_session.refresh(wl)
        assert wl.simulated_mm is None

    def test_save_multiple_updates_applied(self, db_session: Session) -> None:
        """複数更新が一括で適用される"""
        dept = _dept(db_session)
        member = _member(db_session, dept)
        project1 = _project(db_session, wbs_tmp="WBS-001")
        project2 = _project(db_session, wbs_tmp="WBS-002")
        wl1 = _workload(db_session, member, project1, 2025, 4)
        wl2 = _workload(db_session, member, project2, 2025, 4)
        db_session.commit()

        svc = WorkloadService()
        updates = [
            SimulationUpdateItem(
                member_id=member.id,
                project_id=project1.id,
                year=2025,
                month=4,
                simulated_mm=Decimal("0.30"),
            ),
            SimulationUpdateItem(
                member_id=member.id,
                project_id=project2.id,
                year=2025,
                month=4,
                simulated_mm=Decimal("0.20"),
            ),
        ]
        svc.save_simulation(db_session, updates)

        db_session.refresh(wl1)
        db_session.refresh(wl2)
        assert wl1.simulated_mm == Decimal("0.30")
        assert wl2.simulated_mm == Decimal("0.20")

    def test_save_ignores_nonexistent_record(self, db_session: Session) -> None:
        """存在しないレコードへの更新はエラーなくスキップされる"""
        dept = _dept(db_session)
        member = _member(db_session, dept)
        project = _project(db_session)
        db_session.commit()

        svc = WorkloadService()
        updates = [
            SimulationUpdateItem(
                member_id=member.id,
                project_id=project.id,
                year=2025,
                month=4,
                simulated_mm=Decimal("0.50"),
            )
        ]
        # エラーが発生しないことを確認
        svc.save_simulation(db_session, updates)


# ---------------------------------------------------------------------------
# reset_simulation テスト
# ---------------------------------------------------------------------------

class TestResetSimulation:
    def test_reset_all_clears_all_simulated_mm(self, db_session: Session) -> None:
        """member_id/project_id なしでリセットすると全 simulated_mm が NULL になる"""
        dept = _dept(db_session)
        member1 = _member(db_session, dept, code="E001")
        member2 = _member(db_session, dept, code="E002", name="佐藤二郎")
        project = _project(db_session)
        wl1 = _workload(
            db_session, member1, project, 2025, 4, simulated_mm=Decimal("0.50")
        )
        wl2 = _workload(
            db_session, member2, project, 2025, 4, simulated_mm=Decimal("0.30")
        )
        db_session.commit()

        svc = WorkloadService()
        svc.reset_simulation(db_session, member_id=None, project_id=None)

        db_session.refresh(wl1)
        db_session.refresh(wl2)
        assert wl1.simulated_mm is None
        assert wl2.simulated_mm is None

    def test_reset_by_member_id_only_affects_that_member(
        self, db_session: Session
    ) -> None:
        """member_id 指定リセットは対象要員のみ simulated_mm を NULL にする"""
        dept = _dept(db_session)
        member1 = _member(db_session, dept, code="E001")
        member2 = _member(db_session, dept, code="E002", name="佐藤二郎")
        project = _project(db_session)
        wl1 = _workload(
            db_session, member1, project, 2025, 4, simulated_mm=Decimal("0.50")
        )
        wl2 = _workload(
            db_session, member2, project, 2025, 4, simulated_mm=Decimal("0.30")
        )
        db_session.commit()

        svc = WorkloadService()
        svc.reset_simulation(db_session, member_id=member1.id, project_id=None)

        db_session.refresh(wl1)
        db_session.refresh(wl2)
        assert wl1.simulated_mm is None
        assert wl2.simulated_mm == Decimal("0.30")  # 変更されない

    def test_reset_by_project_id_only_affects_that_project(
        self, db_session: Session
    ) -> None:
        """project_id 指定リセットは対象プロジェクトのみ simulated_mm を NULL にする"""
        dept = _dept(db_session)
        member = _member(db_session, dept)
        project1 = _project(db_session, wbs_tmp="WBS-001")
        project2 = _project(db_session, wbs_tmp="WBS-002")
        wl1 = _workload(
            db_session, member, project1, 2025, 4, simulated_mm=Decimal("0.50")
        )
        wl2 = _workload(
            db_session, member, project2, 2025, 4, simulated_mm=Decimal("0.30")
        )
        db_session.commit()

        svc = WorkloadService()
        svc.reset_simulation(db_session, member_id=None, project_id=project1.id)

        db_session.refresh(wl1)
        db_session.refresh(wl2)
        assert wl1.simulated_mm is None
        assert wl2.simulated_mm == Decimal("0.30")  # 変更されない

    def test_reset_does_not_change_planned_mm(self, db_session: Session) -> None:
        """リセット後も planned_mm は変更されない"""
        dept = _dept(db_session)
        member = _member(db_session, dept)
        project = _project(db_session)
        wl = _workload(
            db_session, member, project, 2025, 4,
            planned_mm=Decimal("1.00"),
            simulated_mm=Decimal("0.50"),
        )
        db_session.commit()

        svc = WorkloadService()
        svc.reset_simulation(db_session, member_id=None, project_id=None)

        db_session.refresh(wl)
        assert wl.planned_mm == Decimal("1.00")
        assert wl.simulated_mm is None

    def test_reset_with_member_and_project_filters_combined(
        self, db_session: Session
    ) -> None:
        """member_id と project_id を両方指定すると AND 条件でリセットされる"""
        dept = _dept(db_session)
        member1 = _member(db_session, dept, code="E001")
        member2 = _member(db_session, dept, code="E002", name="佐藤二郎")
        project1 = _project(db_session, wbs_tmp="WBS-001")
        project2 = _project(db_session, wbs_tmp="WBS-002")
        wl_target = _workload(
            db_session, member1, project1, 2025, 4, simulated_mm=Decimal("0.50")
        )
        wl_other_member = _workload(
            db_session, member2, project1, 2025, 4, simulated_mm=Decimal("0.30")
        )
        wl_other_project = _workload(
            db_session, member1, project2, 2025, 4, simulated_mm=Decimal("0.20")
        )
        db_session.commit()

        svc = WorkloadService()
        svc.reset_simulation(db_session, member_id=member1.id, project_id=project1.id)

        db_session.refresh(wl_target)
        db_session.refresh(wl_other_member)
        db_session.refresh(wl_other_project)
        assert wl_target.simulated_mm is None          # リセット対象
        assert wl_other_member.simulated_mm == Decimal("0.30")   # 変更されない
        assert wl_other_project.simulated_mm == Decimal("0.20")  # 変更されない

    def test_reset_no_simulated_data_no_error(self, db_session: Session) -> None:
        """simulated_mm が設定されていなくてもエラーなくリセットできる"""
        dept = _dept(db_session)
        member = _member(db_session, dept)
        project = _project(db_session)
        _workload(db_session, member, project, 2025, 4, simulated_mm=None)
        db_session.commit()

        svc = WorkloadService()
        svc.reset_simulation(db_session, member_id=None, project_id=None)
