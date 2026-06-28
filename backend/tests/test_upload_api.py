"""POST /api/v1/workloads/plan/upload のAPIテスト"""
import csv
import io

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.database import Base, get_db
from app.main import app

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

REQUIRED_HEADERS = [
    "所属部門コード", "所属部門名", "社員コード", "氏名",
    "WBS仮コード", "WBS名称", "会計年度",
    "4月", "5月", "6月", "7月", "8月", "9月",
    "10月", "11月", "12月", "1月", "2月", "3月",
]


def _valid_csv_bytes(emp_code: str = "E001") -> bytes:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=REQUIRED_HEADERS)
    writer.writeheader()
    writer.writerow({
        "所属部門コード": "D01", "所属部門名": "開発部", "社員コード": emp_code,
        "氏名": "山田太郎", "WBS仮コード": "WBS-001", "WBS名称": "システム開発",
        "会計年度": "2026",
        "4月": "1.00", "5月": "0.00", "6月": "0.00", "7月": "0.00",
        "8月": "0.00", "9月": "0.00", "10月": "0.00", "11月": "0.00",
        "12月": "0.00", "1月": "0.00", "2月": "0.00", "3月": "0.00",
    })
    return buf.getvalue().encode("shift_jis")


def _invalid_csv_bytes() -> bytes:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=REQUIRED_HEADERS)
    writer.writeheader()
    writer.writerow({
        "所属部門コード": "D01", "所属部門名": "開発部", "社員コード": "E001",
        "氏名": "山田太郎", "WBS仮コード": "WBS-001", "WBS名称": "システム開発",
        "会計年度": "not_a_year",
        "4月": "1.00", "5月": "0.00", "6月": "0.00", "7月": "0.00",
        "8月": "0.00", "9月": "0.00", "10月": "0.00", "11月": "0.00",
        "12月": "0.00", "1月": "0.00", "2月": "0.00", "3月": "0.00",
    })
    return buf.getvalue().encode("shift_jis")


@pytest.fixture()
def api_client() -> TestClient:  # type: ignore[return]
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


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_upload_valid_csv_returns_200(api_client: TestClient) -> None:
    resp = api_client.post(
        "/api/v1/workloads/plan/upload",
        files={"file": ("plan.csv", _valid_csv_bytes(), "text/csv")},
    )
    assert resp.status_code == 200


def test_upload_valid_csv_response_has_version_no(api_client: TestClient) -> None:
    resp = api_client.post(
        "/api/v1/workloads/plan/upload",
        files={"file": ("plan.csv", _valid_csv_bytes(), "text/csv")},
    )
    body = resp.json()
    assert "version_no" in body
    assert body["version_no"] == 1


def test_upload_valid_csv_response_has_summary(api_client: TestClient) -> None:
    resp = api_client.post(
        "/api/v1/workloads/plan/upload",
        files={"file": ("plan.csv", _valid_csv_bytes(), "text/csv")},
    )
    body = resp.json()
    assert "summary" in body
    assert body["summary"]["departments"]["created"] == 1
    assert body["summary"]["members"]["created"] == 1
    assert body["summary"]["projects"]["created"] == 1
    assert body["summary"]["workloads"]["created"] == 1


def test_upload_invalid_csv_returns_422(api_client: TestClient) -> None:
    resp = api_client.post(
        "/api/v1/workloads/plan/upload",
        files={"file": ("plan.csv", _invalid_csv_bytes(), "text/csv")},
    )
    assert resp.status_code == 422


def test_upload_invalid_csv_response_has_errors(api_client: TestClient) -> None:
    resp = api_client.post(
        "/api/v1/workloads/plan/upload",
        files={"file": ("plan.csv", _invalid_csv_bytes(), "text/csv")},
    )
    body = resp.json()
    assert "detail" in body
    assert "errors" in body["detail"]
    errors = body["detail"]["errors"]
    assert len(errors) > 0
    assert any(e["column"] == "会計年度" for e in errors)
