"""案件一覧・新規登録APIのテスト (GET/POST /api/v1/matters)"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 — 全モデルをBaseに登録
from app.database import Base, get_db
from app.main import app
from app.models.matter import Matter
from app.models.project import Project


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def api_client():  # type: ignore[return]
    """StaticPool を使った APIテスト用 TestClient fixture（空DB）"""
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
def api_client_with_matters():  # type: ignore[return]
    """案件・プロジェクトデータ入り TestClient fixture"""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(test_engine)
    TestingSession = sessionmaker(bind=test_engine)

    with TestingSession() as seed_db:
        m1 = Matter(name="案件A", code="M001", client_name="顧客X", status="進行中")
        m2 = Matter(name="案件B", code="M002", status="計画中")
        seed_db.add_all([m1, m2])
        seed_db.flush()
        p1 = Project(wbs_tmp="WBS-001", name="PJ1", matter_id=m1.id)
        p2 = Project(wbs_tmp="WBS-002", name="PJ2", matter_id=m1.id)
        seed_db.add_all([p1, p2])
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
# GET /api/v1/matters
# ---------------------------------------------------------------------------

class TestGetMatters:
    def test_get_matters_returns_200(self, api_client: TestClient) -> None:
        """案件がない場合 HTTP 200 が返る"""
        response = api_client.get("/api/v1/matters")
        assert response.status_code == 200

    def test_get_matters_returns_empty_list(self, api_client: TestClient) -> None:
        """案件がない場合空のリストを返す"""
        response = api_client.get("/api/v1/matters")
        assert response.json() == []

    def test_get_matters_returns_all_matters(
        self, api_client_with_matters: TestClient
    ) -> None:
        """案件一覧が全件返る"""
        response = api_client_with_matters.get("/api/v1/matters")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_matters_includes_project_count(
        self, api_client_with_matters: TestClient
    ) -> None:
        """案件に配下プロジェクト数（project_count）が含まれる"""
        response = api_client_with_matters.get("/api/v1/matters")
        data = response.json()
        m001 = next(d for d in data if d["code"] == "M001")
        m002 = next(d for d in data if d["code"] == "M002")
        assert m001["project_count"] == 2
        assert m002["project_count"] == 0

    def test_get_matters_response_fields(
        self, api_client_with_matters: TestClient
    ) -> None:
        """レスポンスに必須フィールドが含まれる"""
        response = api_client_with_matters.get("/api/v1/matters")
        item = response.json()[0]
        assert "id" in item
        assert "name" in item
        assert "code" in item
        assert "status" in item
        assert "project_count" in item
        assert "created_at" in item


# ---------------------------------------------------------------------------
# POST /api/v1/matters
# ---------------------------------------------------------------------------

class TestCreateMatter:
    def test_create_matter_returns_201(self, api_client: TestClient) -> None:
        """正常登録で HTTP 201 が返る"""
        response = api_client.post(
            "/api/v1/matters",
            json={"name": "新規案件", "code": "NEW001"},
        )
        assert response.status_code == 201

    def test_create_matter_returns_created_content(self, api_client: TestClient) -> None:
        """登録内容がレスポンスボディに含まれる"""
        response = api_client.post(
            "/api/v1/matters",
            json={"name": "新規案件", "code": "NEW001", "client_name": "クライアントA"},
        )
        data = response.json()
        assert data["name"] == "新規案件"
        assert data["code"] == "NEW001"
        assert data["client_name"] == "クライアントA"
        assert data["project_count"] == 0
        assert "id" in data

    def test_create_matter_status_defaults_to_planning(
        self, api_client: TestClient
    ) -> None:
        """status 省略時は「計画中」になる"""
        response = api_client.post(
            "/api/v1/matters",
            json={"name": "案件X", "code": "X001"},
        )
        assert response.json()["status"] == "計画中"

    def test_create_matter_duplicate_code_returns_409(
        self, api_client: TestClient
    ) -> None:
        """案件コード重複時は HTTP 409 が返る"""
        api_client.post("/api/v1/matters", json={"name": "案件1", "code": "DUP001"})
        response = api_client.post(
            "/api/v1/matters",
            json={"name": "案件2", "code": "DUP001"},
        )
        assert response.status_code == 409

    def test_create_matter_409_has_error_message(
        self, api_client: TestClient
    ) -> None:
        """HTTP 409 レスポンスにエラーメッセージが含まれる"""
        api_client.post("/api/v1/matters", json={"name": "案件1", "code": "DUP002"})
        response = api_client.post(
            "/api/v1/matters",
            json={"name": "案件2", "code": "DUP002"},
        )
        assert "detail" in response.json()

    def test_create_matter_missing_name_returns_422(
        self, api_client: TestClient
    ) -> None:
        """name 欠如時は HTTP 422 が返る"""
        response = api_client.post(
            "/api/v1/matters",
            json={"code": "NO_NAME"},
        )
        assert response.status_code == 422

    def test_create_matter_missing_code_returns_422(
        self, api_client: TestClient
    ) -> None:
        """code 欠如時は HTTP 422 が返る"""
        response = api_client.post(
            "/api/v1/matters",
            json={"name": "コードなし案件"},
        )
        assert response.status_code == 422

    def test_create_matter_empty_name_returns_422(
        self, api_client: TestClient
    ) -> None:
        """name が空文字の場合は HTTP 422 が返る"""
        response = api_client.post(
            "/api/v1/matters",
            json={"name": "", "code": "EMPTY001"},
        )
        assert response.status_code == 422

    def test_create_matter_empty_code_returns_422(
        self, api_client: TestClient
    ) -> None:
        """code が空文字の場合は HTTP 422 が返る"""
        response = api_client.post(
            "/api/v1/matters",
            json={"name": "テスト案件", "code": ""},
        )
        assert response.status_code == 422
