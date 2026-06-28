"""プロジェクト一覧・編集・案件紐づけAPIのテスト"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.database import Base, get_db
from app.main import app
from app.models.matter import Matter
from app.models.project import Project


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
    """案件・プロジェクトデータ入り TestClient fixture"""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(test_engine)
    TestingSession = sessionmaker(bind=test_engine)

    with TestingSession() as seed_db:
        m = Matter(name="案件A", code="M001", status="進行中")
        seed_db.add(m)
        seed_db.flush()
        p1 = Project(wbs_tmp="WBS-001", name="紐づき済みPJ", matter_id=m.id)
        p2 = Project(wbs_tmp="WBS-002", name="未紐づきPJ")
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
# GET /api/v1/projects
# ---------------------------------------------------------------------------

class TestGetProjects:
    def test_get_projects_returns_200(self, api_client: TestClient) -> None:
        """HTTP 200 が返る"""
        response = api_client.get("/api/v1/projects")
        assert response.status_code == 200

    def test_get_projects_returns_empty_list(self, api_client: TestClient) -> None:
        """プロジェクトがない場合空のリストを返す"""
        assert api_client.get("/api/v1/projects").json() == []

    def test_get_projects_returns_all_projects(
        self, api_client_with_data: TestClient
    ) -> None:
        """全件返る"""
        data = api_client_with_data.get("/api/v1/projects").json()
        assert len(data) == 2

    def test_get_projects_includes_matter_name(
        self, api_client_with_data: TestClient
    ) -> None:
        """案件紐づき済みプロジェクトに matter_name が含まれる"""
        data = api_client_with_data.get("/api/v1/projects").json()
        assigned = next(d for d in data if d["wbs_tmp"] == "WBS-001")
        assert assigned["matter_name"] == "案件A"
        unassigned = next(d for d in data if d["wbs_tmp"] == "WBS-002")
        assert unassigned["matter_name"] is None

    def test_get_projects_response_fields(
        self, api_client_with_data: TestClient
    ) -> None:
        """レスポンスに必須フィールドが含まれる"""
        item = api_client_with_data.get("/api/v1/projects").json()[0]
        for field in ["id", "wbs_tmp", "name", "code", "display_order", "matter_id", "matter_name"]:
            assert field in item

    def test_get_projects_unassigned_true_filters(
        self, api_client_with_data: TestClient
    ) -> None:
        """unassigned=true で matter_id IS NULL のみ返る"""
        data = api_client_with_data.get("/api/v1/projects", params={"unassigned": "true"}).json()
        assert len(data) == 1
        assert data[0]["wbs_tmp"] == "WBS-002"

    def test_get_projects_unassigned_false_returns_all(
        self, api_client_with_data: TestClient
    ) -> None:
        """unassigned=false（デフォルト）で全件返る"""
        data = api_client_with_data.get("/api/v1/projects", params={"unassigned": "false"}).json()
        assert len(data) == 2


# ---------------------------------------------------------------------------
# PUT /api/v1/projects/{id}
# ---------------------------------------------------------------------------

class TestUpdateProject:
    def test_update_project_returns_200(self, api_client_with_data: TestClient) -> None:
        """更新成功時 HTTP 200 が返る"""
        projects = api_client_with_data.get("/api/v1/projects").json()
        pid = projects[0]["id"]
        response = api_client_with_data.put(
            f"/api/v1/projects/{pid}",
            json={"name": "更新後PJ"},
        )
        assert response.status_code == 200

    def test_update_project_name(self, api_client_with_data: TestClient) -> None:
        """WBS名称が更新される"""
        projects = api_client_with_data.get("/api/v1/projects").json()
        pid = projects[0]["id"]
        api_client_with_data.put(f"/api/v1/projects/{pid}", json={"name": "変更済みPJ"})
        updated = next(
            p for p in api_client_with_data.get("/api/v1/projects").json()
            if p["id"] == pid
        )
        assert updated["name"] == "変更済みPJ"

    def test_update_project_code(self, api_client_with_data: TestClient) -> None:
        """WBSコードが更新される"""
        projects = api_client_with_data.get("/api/v1/projects").json()
        pid = projects[0]["id"]
        api_client_with_data.put(f"/api/v1/projects/{pid}", json={"code": "NEW-CODE"})
        updated = next(
            p for p in api_client_with_data.get("/api/v1/projects").json()
            if p["id"] == pid
        )
        assert updated["code"] == "NEW-CODE"

    def test_update_project_display_order(self, api_client_with_data: TestClient) -> None:
        """表示順が更新される"""
        projects = api_client_with_data.get("/api/v1/projects").json()
        pid = projects[0]["id"]
        api_client_with_data.put(f"/api/v1/projects/{pid}", json={"display_order": 99})
        updated = next(
            p for p in api_client_with_data.get("/api/v1/projects").json()
            if p["id"] == pid
        )
        assert updated["display_order"] == 99

    def test_update_project_not_found_returns_404(
        self, api_client: TestClient
    ) -> None:
        """存在しないIDで HTTP 404 が返る"""
        response = api_client.put("/api/v1/projects/99999", json={"name": "X"})
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# PUT /api/v1/projects/{id}/matter
# ---------------------------------------------------------------------------

class TestAssignMatter:
    def test_assign_matter_returns_200(self, api_client_with_data: TestClient) -> None:
        """案件紐づけ成功時 HTTP 200 が返る"""
        projects = api_client_with_data.get("/api/v1/projects").json()
        unassigned = next(p for p in projects if p["matter_id"] is None)
        matters = api_client_with_data.get("/api/v1/matters").json()
        response = api_client_with_data.put(
            f"/api/v1/projects/{unassigned['id']}/matter",
            json={"matter_id": matters[0]["id"]},
        )
        assert response.status_code == 200

    def test_assign_matter_updates_matter_id(
        self, api_client_with_data: TestClient
    ) -> None:
        """紐づけ後に matter_id が更新される"""
        projects = api_client_with_data.get("/api/v1/projects").json()
        unassigned = next(p for p in projects if p["matter_id"] is None)
        matters = api_client_with_data.get("/api/v1/matters").json()
        mid = matters[0]["id"]
        api_client_with_data.put(
            f"/api/v1/projects/{unassigned['id']}/matter",
            json={"matter_id": mid},
        )
        updated = next(
            p for p in api_client_with_data.get("/api/v1/projects").json()
            if p["id"] == unassigned["id"]
        )
        assert updated["matter_id"] == mid

    def test_assign_matter_removes_from_unassigned_list(
        self, api_client_with_data: TestClient
    ) -> None:
        """紐づけ後に unassigned=true リストから消える"""
        projects = api_client_with_data.get("/api/v1/projects").json()
        unassigned = next(p for p in projects if p["matter_id"] is None)
        matters = api_client_with_data.get("/api/v1/matters").json()
        api_client_with_data.put(
            f"/api/v1/projects/{unassigned['id']}/matter",
            json={"matter_id": matters[0]["id"]},
        )
        unassigned_after = api_client_with_data.get(
            "/api/v1/projects", params={"unassigned": "true"}
        ).json()
        assert all(p["id"] != unassigned["id"] for p in unassigned_after)

    def test_assign_matter_project_not_found_returns_404(
        self, api_client_with_data: TestClient
    ) -> None:
        """存在しないプロジェクトIDで HTTP 404 が返る"""
        matters = api_client_with_data.get("/api/v1/matters").json()
        response = api_client_with_data.put(
            "/api/v1/projects/99999/matter",
            json={"matter_id": matters[0]["id"]},
        )
        assert response.status_code == 404

    def test_assign_matter_invalid_matter_returns_404(
        self, api_client_with_data: TestClient
    ) -> None:
        """存在しない案件IDで HTTP 404 が返る"""
        projects = api_client_with_data.get("/api/v1/projects").json()
        unassigned = next(p for p in projects if p["matter_id"] is None)
        response = api_client_with_data.put(
            f"/api/v1/projects/{unassigned['id']}/matter",
            json={"matter_id": 99999},
        )
        assert response.status_code == 404

    def test_unassign_matter_with_null_matter_id(
        self, api_client_with_data: TestClient
    ) -> None:
        """matter_id=null で案件紐づけを解除できる"""
        projects = api_client_with_data.get("/api/v1/projects").json()
        assigned = next(p for p in projects if p["matter_id"] is not None)
        api_client_with_data.put(
            f"/api/v1/projects/{assigned['id']}/matter",
            json={"matter_id": None},
        )
        updated = next(
            p for p in api_client_with_data.get("/api/v1/projects").json()
            if p["id"] == assigned["id"]
        )
        assert updated["matter_id"] is None
