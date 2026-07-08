"""WorkloadService.download_forecast_csv() とダウンロードAPIのテスト"""
import csv
import io
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 — 全モデルをBaseに登録
from app.database import Base, get_db
from app.main import app
from app.models.department import Department
from app.models.member import Member
from app.models.monthly_workload import MonthlyWorkload
from app.models.project import Project
from app.services.workload_service import WorkloadService

EXPECTED_HEADERS = [
    "所属部門コード", "所属部門名", "社員コード", "氏名",
    "WBS仮コード", "WBSコード", "WBS名称", "会計年度",
    "4月", "5月", "6月", "7月", "8月", "9月",
    "10月", "11月", "12月", "1月", "2月", "3月",
]

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


def _project(
    db: Session,
    wbs_tmp: str = "WBS-001",
    name: str = "システム開発",
    code: str | None = None,
) -> Project:
    p = Project(wbs_tmp=wbs_tmp, name=name, code=code)
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


def _parse_csv(csv_bytes: bytes) -> list[dict[str, str]]:
    """CP932（Windows Shift-JIS）でデコードしてDictReaderでパース"""
    text = csv_bytes.decode("cp932")
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)


def _parse_csv_headers(csv_bytes: bytes) -> list[str]:
    text = csv_bytes.decode("cp932")
    reader = csv.reader(io.StringIO(text))
    return next(reader)


# ---------------------------------------------------------------------------
# WorkloadService.download_forecast_csv() テスト
# ---------------------------------------------------------------------------

class TestDownloadForecastCsv:
    def test_csv_has_correct_headers(self, db_session: Session) -> None:
        """CSVの1行目が計画工数CSVと同じヘッダー行になっている"""
        svc = WorkloadService()
        result = svc.download_forecast_csv(db_session, None, None, 2025, 4, 2025, 4)
        headers = _parse_csv_headers(result)
        assert headers == EXPECTED_HEADERS

    def test_csv_empty_when_no_data(self, db_session: Session) -> None:
        """データがない場合はヘッダー行のみのCSVを返す"""
        svc = WorkloadService()
        result = svc.download_forecast_csv(db_session, None, None, 2025, 4, 2025, 4)
        rows = _parse_csv(result)
        assert rows == []

    def test_csv_uses_planned_mm_when_simulated_is_none(
        self, db_session: Session
    ) -> None:
        """simulated_mmがNULLのとき見込工数はplanned_mm（4月列に格納）"""
        dept = _dept(db_session)
        member = _member(db_session, dept, code="E001", name="山田太郎")
        project = _project(db_session, wbs_tmp="WBS-001", name="システム開発")
        _workload(
            db_session, member, project, 2025, 4,
            planned_mm=Decimal("1.00"), simulated_mm=None
        )
        db_session.commit()

        svc = WorkloadService()
        result = svc.download_forecast_csv(db_session, None, None, 2025, 4, 2025, 4)
        rows = _parse_csv(result)

        assert len(rows) == 1
        assert rows[0]["4月"] == "1.00"

    def test_csv_uses_simulated_mm_when_set(self, db_session: Session) -> None:
        """simulated_mmが設定されているとき見込工数はsimulated_mm"""
        dept = _dept(db_session)
        member = _member(db_session, dept)
        project = _project(db_session)
        _workload(
            db_session, member, project, 2025, 4,
            planned_mm=Decimal("1.00"), simulated_mm=Decimal("0.50")
        )
        db_session.commit()

        svc = WorkloadService()
        result = svc.download_forecast_csv(db_session, None, None, 2025, 4, 2025, 4)
        rows = _parse_csv(result)

        assert rows[0]["4月"] == "0.50"

    def test_csv_row_contains_correct_columns(self, db_session: Session) -> None:
        """CSV行に部門・要員・プロジェクト・会計年度・月別工数が含まれる"""
        dept = _dept(db_session)
        member = _member(db_session, dept, code="E999", name="鈴木三郎")
        project = _project(db_session, wbs_tmp="WBS-XYZ", name="基盤開発", code="WBS-XYZ-REAL")
        _workload(
            db_session, member, project, 2025, 7,
            planned_mm=Decimal("0.75")
        )
        db_session.commit()

        svc = WorkloadService()
        result = svc.download_forecast_csv(db_session, None, None, 2025, 7, 2025, 7)
        rows = _parse_csv(result)

        assert rows[0]["所属部門コード"] == "D01"
        assert rows[0]["所属部門名"] == "開発部"
        assert rows[0]["社員コード"] == "E999"
        assert rows[0]["氏名"] == "鈴木三郎"
        assert rows[0]["WBS仮コード"] == "WBS-XYZ"
        assert rows[0]["WBSコード"] == "WBS-XYZ-REAL"
        assert rows[0]["WBS名称"] == "基盤開発"
        assert rows[0]["会計年度"] == "2025"
        assert rows[0]["7月"] == "0.75"

    def test_csv_wbs_code_empty_when_not_set(self, db_session: Session) -> None:
        """WBSコードが未設定のプロジェクトはWBSコード列が空文字"""
        dept = _dept(db_session)
        member = _member(db_session, dept)
        project = _project(db_session)  # code=None
        _workload(db_session, member, project, 2025, 4, planned_mm=Decimal("1.00"))
        db_session.commit()

        svc = WorkloadService()
        result = svc.download_forecast_csv(db_session, None, None, 2025, 4, 2025, 4)
        rows = _parse_csv(result)

        assert rows[0]["WBSコード"] == ""

    def test_csv_filters_by_date_range(self, db_session: Session) -> None:
        """期間外の月はCSVに含まれない（期間内の月のみ値が入る）"""
        dept = _dept(db_session)
        member = _member(db_session, dept)
        project = _project(db_session)
        _workload(db_session, member, project, 2025, 4, planned_mm=Decimal("1.00"))
        _workload(db_session, member, project, 2025, 7, planned_mm=Decimal("0.50"))
        db_session.commit()

        svc = WorkloadService()
        # 4〜6月のみ取得 → 7月データは除外される
        result = svc.download_forecast_csv(db_session, None, None, 2025, 4, 2025, 6)
        rows = _parse_csv(result)

        assert len(rows) == 1
        assert rows[0]["4月"] == "1.00"
        assert rows[0]["7月"] == "0.00"  # 範囲外のためデフォルト値

    def test_csv_multiple_rows_sorted(self, db_session: Session) -> None:
        """複数行が社員コード→WBS仮コードの順でソートされる"""
        dept = _dept(db_session)
        member1 = _member(db_session, dept, code="E002", name="佐藤二郎")
        member2 = _member(db_session, dept, code="E001", name="山田太郎")
        project1 = _project(db_session, wbs_tmp="WBS-002", name="PJ2")
        project2 = _project(db_session, wbs_tmp="WBS-001", name="PJ1")
        _workload(db_session, member1, project1, 2025, 5, planned_mm=Decimal("0.30"))
        _workload(db_session, member2, project2, 2025, 4, planned_mm=Decimal("1.00"))
        _workload(db_session, member2, project1, 2025, 4, planned_mm=Decimal("0.50"))
        db_session.commit()

        svc = WorkloadService()
        result = svc.download_forecast_csv(db_session, None, None, 2025, 4, 2025, 6)
        rows = _parse_csv(result)

        assert len(rows) == 3
        # E001が先、その中でWBS-001 → WBS-002
        assert rows[0]["社員コード"] == "E001"
        assert rows[0]["WBS仮コード"] == "WBS-001"
        assert rows[1]["社員コード"] == "E001"
        assert rows[1]["WBS仮コード"] == "WBS-002"
        assert rows[2]["社員コード"] == "E002"

    def test_csv_skips_null_forecast_mm(self, db_session: Session) -> None:
        """planned_mm・simulated_mmが両方NULLのレコードはスキップされる"""
        dept = _dept(db_session)
        member = _member(db_session, dept)
        project = _project(db_session)
        _workload(
            db_session, member, project, 2025, 4,
            planned_mm=None, simulated_mm=None
        )
        db_session.commit()

        svc = WorkloadService()
        result = svc.download_forecast_csv(db_session, None, None, 2025, 4, 2025, 4)
        rows = _parse_csv(result)
        assert rows == []

    def test_csv_pivot_by_fiscal_year(self, db_session: Session) -> None:
        """同一(社員・PJ・会計年度)の複数月は1行にピボットされる"""
        dept = _dept(db_session)
        member = _member(db_session, dept)
        project = _project(db_session)
        _workload(db_session, member, project, 2025, 4, planned_mm=Decimal("0.50"))
        _workload(db_session, member, project, 2025, 5, planned_mm=Decimal("0.30"))
        db_session.commit()

        svc = WorkloadService()
        result = svc.download_forecast_csv(db_session, None, None, 2025, 4, 2025, 5)
        rows = _parse_csv(result)

        assert len(rows) == 1  # 2ヶ月分が1行に集約される
        assert rows[0]["4月"] == "0.50"
        assert rows[0]["5月"] == "0.30"

    def test_csv_fiscal_year_boundary(self, db_session: Session) -> None:
        """1月〜3月は前年度会計年度に属する"""
        dept = _dept(db_session)
        member = _member(db_session, dept)
        project = _project(db_session)
        _workload(db_session, member, project, 2026, 1, planned_mm=Decimal("0.20"))
        db_session.commit()

        svc = WorkloadService()
        result = svc.download_forecast_csv(db_session, None, None, 2026, 1, 2026, 1)
        rows = _parse_csv(result)

        assert len(rows) == 1
        assert rows[0]["会計年度"] == "2025"  # 2026年1月 → FY2025
        assert rows[0]["1月"] == "0.20"


# ---------------------------------------------------------------------------
# ダウンロードAPIエンドポイントのテスト
# ---------------------------------------------------------------------------

@pytest.fixture()
def api_client() -> TestClient:  # type: ignore[return]
    """StaticPool を使った APIテスト用 TestClient fixture"""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(test_engine)
    TestingSession = sessionmaker(bind=test_engine)

    def override_get_db():  # type: ignore[return]
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(test_engine)
        test_engine.dispose()


@pytest.fixture()
def api_client_with_data() -> TestClient:  # type: ignore[return]
    """データ入り APIテスト用 TestClient fixture"""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(test_engine)
    TestingSession = sessionmaker(bind=test_engine)

    with TestingSession() as seed_db:
        dept = Department(code="D01", name="開発部")
        seed_db.add(dept)
        seed_db.flush()
        member = Member(employee_code="E001", name="山田太郎", department_id=dept.id)
        seed_db.add(member)
        seed_db.flush()
        project = Project(wbs_tmp="WBS-001", name="テストPJ")
        seed_db.add(project)
        seed_db.flush()
        seed_db.add(MonthlyWorkload(
            member_id=member.id,
            project_id=project.id,
            year=2025,
            month=4,
            planned_mm=Decimal("1.00"),
        ))
        seed_db.commit()

    def override_get_db():  # type: ignore[return]
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(test_engine)
        test_engine.dispose()


class TestDownloadEndpoint:
    def test_endpoint_returns_200(self, api_client: TestClient) -> None:
        """GETリクエストでHTTP 200が返る"""
        response = api_client.get(
            "/api/v1/workloads/forecast/download",
            params={"from": "2025-04", "to": "2025-09"},
        )
        assert response.status_code == 200

    def test_endpoint_content_type_is_csv(self, api_client: TestClient) -> None:
        """レスポンスのContent-Typeがtext/csvである"""
        response = api_client.get(
            "/api/v1/workloads/forecast/download",
            params={"from": "2025-04", "to": "2025-09"},
        )
        assert "text/csv" in response.headers["content-type"]

    def test_endpoint_content_disposition_filename(
        self, api_client: TestClient
    ) -> None:
        """Content-Dispositionにworkload_{from}_{to}.csvのファイル名が含まれる"""
        response = api_client.get(
            "/api/v1/workloads/forecast/download",
            params={"from": "2025-04", "to": "2025-09"},
        )
        disposition = response.headers.get("content-disposition", "")
        assert "workload_2025-04_2025-09.csv" in disposition
        assert "attachment" in disposition

    def test_endpoint_returns_csv_with_data(
        self, api_client_with_data: TestClient
    ) -> None:
        """DBにデータがある場合、CSVにデータ行が含まれる（CP932デコード）"""
        response = api_client_with_data.get(
            "/api/v1/workloads/forecast/download",
            params={"from": "2025-04", "to": "2025-09"},
        )
        rows = _parse_csv(response.content)
        assert len(rows) == 1
        assert rows[0]["社員コード"] == "E001"
        assert rows[0]["4月"] == "1.00"
