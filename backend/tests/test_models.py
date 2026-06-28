from app.models.department import Department
from app.models.forecast_snapshot import ForecastSnapshot
from app.models.forecast_version import ForecastVersion
from app.models.matter import Matter
from app.models.member import Member
from app.models.monthly_workload import MonthlyWorkload
from app.models.project import Project
from app.models.team import Team
from app.models.team_member import TeamMember


def test_all_models_have_correct_table_names() -> None:
    assert Department.__tablename__ == "departments"
    assert Team.__tablename__ == "teams"
    assert TeamMember.__tablename__ == "team_members"
    assert Member.__tablename__ == "members"
    assert Matter.__tablename__ == "matters"
    assert Project.__tablename__ == "projects"
    assert MonthlyWorkload.__tablename__ == "monthly_workloads"
    assert ForecastVersion.__tablename__ == "forecast_versions"
    assert ForecastSnapshot.__tablename__ == "forecast_snapshots"


def test_project_matter_id_is_nullable() -> None:
    col = Project.__table__.c["matter_id"]
    assert col.nullable is True


def test_monthly_workload_mm_columns_are_nullable() -> None:
    table = MonthlyWorkload.__table__
    for col_name in ("planned_mm", "simulated_mm", "actual_mm"):
        assert table.c[col_name].nullable is True, f"{col_name} should be nullable"


def test_monthly_workload_has_unique_constraint() -> None:
    names = {c.name for c in MonthlyWorkload.__table__.constraints}
    assert "uq_monthly_workload" in names


def test_forecast_snapshot_has_unique_constraint() -> None:
    names = {c.name for c in ForecastSnapshot.__table__.constraints}
    assert "uq_forecast_snapshot" in names
