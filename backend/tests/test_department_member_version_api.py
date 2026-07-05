"""部門一覧・要員一覧・バージョン一覧APIのテスト"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.database import Base, get_db
from app.main import app
from app.models.department import Department
from app.models.forecast_version import ForecastVersion
from app.models.member import Member


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def api_client():  # type: ignore[return]
    """空DB TestClient fixture"""
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
def api_client_with_data():  # type: ignore[return]
    """部門・要員・バージョンデータ入り TestClient fixture"""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(test_engine)
    TestingSession = sessionmaker(bind=test_engine)

    with TestingSession() as seed_db:
        d1 = Department(code="D01", name="開発部")
        d2 = Department(code="D02", name="営業部")
        seed_db.add_all([d1, d2])
        seed_db.flush()
        m1 = Member(employee_code="E001", name="山田太郎", department_id=d1.id)
        m2 = Member(employee_code="E002", name="佐藤二郎", department_id=d1.id)
        m3 = Member(employee_code="E003", name="田中三郎", department_id=d2.id)
        seed_db.add_all([m1, m2, m3])
        v1 = ForecastVersion(version_no=1, name="バージョン1")
        v2 = ForecastVersion(version_no=2, name="バージョン2")
        seed_db.add_all([v1, v2])
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


# ---------------------------------------------------------------------------
# GET /api/v1/departments
# ---------------------------------------------------------------------------

class TestGetDepartments:
    def test_get_departments_returns_200(self, api_client: TestClient) -> None:
        """HTTP 200 が返る"""
        assert api_client.get("/api/v1/departments").status_code == 200

    def test_get_departments_returns_empty_list(self, api_client: TestClient) -> None:
        """データがない場合空のリストを返す"""
        assert api_client.get("/api/v1/departments").json() == []

    def test_get_departments_returns_all(
        self, api_client_with_data: TestClient
    ) -> None:
        """全件返る"""
        data = api_client_with_data.get("/api/v1/departments").json()
        assert len(data) == 2

    def test_get_departments_response_fields(
        self, api_client_with_data: TestClient
    ) -> None:
        """レスポンスに id・code・name が含まれる"""
        item = api_client_with_data.get("/api/v1/departments").json()[0]
        assert "id" in item
        assert "code" in item
        assert "name" in item

    def test_get_departments_sorted_by_code(
        self, api_client_with_data: TestClient
    ) -> None:
        """コード順で返る"""
        data = api_client_with_data.get("/api/v1/departments").json()
        codes = [d["code"] for d in data]
        assert codes == sorted(codes)


# ---------------------------------------------------------------------------
# GET /api/v1/members
# ---------------------------------------------------------------------------

class TestGetMembers:
    def test_get_members_returns_200(self, api_client: TestClient) -> None:
        """HTTP 200 が返る"""
        assert api_client.get("/api/v1/members").status_code == 200

    def test_get_members_returns_empty_list(self, api_client: TestClient) -> None:
        """データがない場合空のリストを返す"""
        assert api_client.get("/api/v1/members").json() == []

    def test_get_members_returns_all(
        self, api_client_with_data: TestClient
    ) -> None:
        """フィルタなしで全件返る"""
        data = api_client_with_data.get("/api/v1/members").json()
        assert len(data) == 3

    def test_get_members_response_fields(
        self, api_client_with_data: TestClient
    ) -> None:
        """レスポンスに id・employee_code・name・department_id が含まれる"""
        item = api_client_with_data.get("/api/v1/members").json()[0]
        assert "id" in item
        assert "employee_code" in item
        assert "name" in item
        assert "department_id" in item

    def test_get_members_filter_by_dept_id(
        self, api_client_with_data: TestClient
    ) -> None:
        """dept_id フィルタで該当部門の要員のみ返る"""
        departments = api_client_with_data.get("/api/v1/departments").json()
        d1 = next(d for d in departments if d["code"] == "D01")
        data = api_client_with_data.get(
            "/api/v1/members", params={"dept_id": d1["id"]}
        ).json()
        assert len(data) == 2
        assert all(m["department_id"] == d1["id"] for m in data)

    def test_get_members_filter_by_dept_id_other_dept(
        self, api_client_with_data: TestClient
    ) -> None:
        """別部門フィルタで対象部門の要員のみ返る"""
        departments = api_client_with_data.get("/api/v1/departments").json()
        d2 = next(d for d in departments if d["code"] == "D02")
        data = api_client_with_data.get(
            "/api/v1/members", params={"dept_id": d2["id"]}
        ).json()
        assert len(data) == 1
        assert data[0]["employee_code"] == "E003"

    def test_get_members_sorted_by_employee_code(
        self, api_client_with_data: TestClient
    ) -> None:
        """社員コード順で返る"""
        data = api_client_with_data.get("/api/v1/members").json()
        codes = [m["employee_code"] for m in data]
        assert codes == sorted(codes)


# ---------------------------------------------------------------------------
# GET /api/v1/forecast-versions
# ---------------------------------------------------------------------------

class TestGetForecastVersions:
    def test_get_versions_returns_200(self, api_client: TestClient) -> None:
        """HTTP 200 が返る"""
        assert api_client.get("/api/v1/forecast-versions").status_code == 200

    def test_get_versions_returns_empty_list(self, api_client: TestClient) -> None:
        """データがない場合空のリストを返す"""
        assert api_client.get("/api/v1/forecast-versions").json() == []

    def test_get_versions_returns_all(
        self, api_client_with_data: TestClient
    ) -> None:
        """全件返る"""
        data = api_client_with_data.get("/api/v1/forecast-versions").json()
        assert len(data) == 2

    def test_get_versions_response_fields(
        self, api_client_with_data: TestClient
    ) -> None:
        """レスポンスに id・version_no・name・description・snapshot_count・created_at が含まれる"""
        item = api_client_with_data.get("/api/v1/forecast-versions").json()[0]
        assert "id" in item
        assert "version_no" in item
        assert "name" in item
        assert "description" in item
        assert "snapshot_count" in item
        assert "created_at" in item

    def test_get_versions_sorted_descending(
        self, api_client_with_data: TestClient
    ) -> None:
        """作成日時降順（version_no 降順）で返る"""
        data = api_client_with_data.get("/api/v1/forecast-versions").json()
        version_nos = [v["version_no"] for v in data]
        assert version_nos == sorted(version_nos, reverse=True)
