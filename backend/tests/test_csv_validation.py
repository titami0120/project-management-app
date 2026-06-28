"""CsvImportService._validate_headers / _validate_rows のユニットテスト"""
import csv
import io

import pytest

from app.services.csv_import_service import CsvImportService
from app.services.exceptions import CsvValidationException

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

REQUIRED_HEADERS = [
    "所属部門コード", "所属部門名", "社員コード", "氏名",
    "WBS仮コード", "WBS名称", "会計年度",
    "4月", "5月", "6月", "7月", "8月", "9月",
    "10月", "11月", "12月", "1月", "2月", "3月",
]

OPTIONAL_HEADERS = ["WBSコード", "プロダクトコード", "プロダクト名", "所属会社コード", "所属会社名"]


def _make_csv(headers: list[str], rows: list[dict[str, str]]) -> bytes:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=headers, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buf.getvalue().encode("shift_jis")


def _valid_row(**overrides: str) -> dict[str, str]:
    base: dict[str, str] = {
        "所属部門コード": "D01", "所属部門名": "開発部", "社員コード": "E001",
        "氏名": "山田太郎", "WBS仮コード": "WBS-001", "WBS名称": "システム開発",
        "会計年度": "2026",
        "4月": "0.50", "5月": "1.00", "6月": "0.00", "7月": "0.00",
        "8月": "0.00", "9月": "0.00", "10月": "0.00", "11月": "0.00",
        "12月": "0.00", "1月": "0.00", "2月": "0.00", "3月": "0.00",
    }
    base.update(overrides)
    return base


service = CsvImportService()


# ---------------------------------------------------------------------------
# ヘッダー検証
# ---------------------------------------------------------------------------

class TestValidateHeaders:
    def test_all_required_headers_present_returns_no_errors(self) -> None:
        errors = service._validate_headers(REQUIRED_HEADERS)
        assert errors == []

    def test_optional_headers_present_returns_no_errors(self) -> None:
        errors = service._validate_headers(REQUIRED_HEADERS + OPTIONAL_HEADERS)
        assert errors == []

    @pytest.mark.parametrize("missing_col", REQUIRED_HEADERS)
    def test_missing_required_header_returns_error(self, missing_col: str) -> None:
        headers = [h for h in REQUIRED_HEADERS if h != missing_col]
        errors = service._validate_headers(headers)
        assert len(errors) == 1
        assert errors[0].row_no is None
        assert errors[0].column == missing_col
        assert f'列"{missing_col}"が見つかりません' in errors[0].message

    def test_multiple_missing_headers_returns_multiple_errors(self) -> None:
        headers = [h for h in REQUIRED_HEADERS if h not in ("4月", "5月", "会計年度")]
        errors = service._validate_headers(headers)
        assert len(errors) == 3
        columns = {e.column for e in errors}
        assert columns == {"4月", "5月", "会計年度"}


# ---------------------------------------------------------------------------
# 行バリデーション
# ---------------------------------------------------------------------------

class TestValidateRows:
    def test_valid_row_returns_no_errors(self) -> None:
        rows = [_valid_row()]
        errors = service._validate_rows(rows)
        assert errors == []

    # --- 必須文字列の空白チェック ---
    @pytest.mark.parametrize("col", [
        "所属部門コード", "所属部門名", "社員コード", "氏名", "WBS仮コード", "WBS名称"
    ])
    def test_empty_required_string_returns_error(self, col: str) -> None:
        rows = [_valid_row(**{col: ""})]
        errors = service._validate_rows(rows)
        assert any(e.column == col and e.row_no == 1 for e in errors)

    @pytest.mark.parametrize("col", [
        "所属部門コード", "所属部門名", "社員コード", "氏名", "WBS仮コード", "WBS名称"
    ])
    def test_whitespace_only_required_string_returns_error(self, col: str) -> None:
        rows = [_valid_row(**{col: "   "})]
        errors = service._validate_rows(rows)
        assert any(e.column == col and e.row_no == 1 for e in errors)

    # --- 会計年度バリデーション ---
    def test_fiscal_year_not_integer_returns_error(self) -> None:
        rows = [_valid_row(**{"会計年度": "abc"})]
        errors = service._validate_rows(rows)
        assert any(e.column == "会計年度" and e.row_no == 1 for e in errors)

    def test_fiscal_year_too_small_returns_error(self) -> None:
        rows = [_valid_row(**{"会計年度": "0"})]
        errors = service._validate_rows(rows)
        assert any(e.column == "会計年度" for e in errors)

    def test_fiscal_year_too_large_returns_error(self) -> None:
        rows = [_valid_row(**{"会計年度": "2101"})]
        errors = service._validate_rows(rows)
        assert any(e.column == "会計年度" for e in errors)

    def test_fiscal_year_boundary_1900_is_valid(self) -> None:
        rows = [_valid_row(**{"会計年度": "1900"})]
        errors = service._validate_rows(rows)
        assert not any(e.column == "会計年度" for e in errors)

    def test_fiscal_year_boundary_2100_is_valid(self) -> None:
        rows = [_valid_row(**{"会計年度": "2100"})]
        errors = service._validate_rows(rows)
        assert not any(e.column == "会計年度" for e in errors)

    def test_fiscal_year_error_message_contains_value(self) -> None:
        rows = [_valid_row(**{"会計年度": "abc"})]
        errors = service._validate_rows(rows)
        fy_error = next(e for e in errors if e.column == "会計年度")
        assert "abc" in fy_error.message

    # --- 月次工数バリデーション ---
    @pytest.mark.parametrize("month_col", ["4月", "12月", "1月", "3月"])
    def test_monthly_workload_non_numeric_returns_error(self, month_col: str) -> None:
        rows = [_valid_row(**{month_col: "abc"})]
        errors = service._validate_rows(rows)
        assert any(e.column == month_col and e.row_no == 1 for e in errors)

    @pytest.mark.parametrize("month_col", ["4月", "8月", "3月"])
    def test_monthly_workload_negative_returns_error(self, month_col: str) -> None:
        rows = [_valid_row(**{month_col: "-0.50"})]
        errors = service._validate_rows(rows)
        assert any(e.column == month_col for e in errors)

    def test_monthly_workload_zero_is_valid(self) -> None:
        rows = [_valid_row(**{"4月": "0.00"})]
        errors = service._validate_rows(rows)
        assert not any(e.column == "4月" for e in errors)

    def test_monthly_workload_error_message_contains_value(self) -> None:
        rows = [_valid_row(**{"4月": "-0.50"})]
        errors = service._validate_rows(rows)
        err = next(e for e in errors if e.column == "4月")
        assert "-0.50" in err.message

    # --- 複数エラーの一括収集 ---
    def test_multiple_errors_in_one_row_all_collected(self) -> None:
        rows = [_valid_row(**{"会計年度": "bad", "4月": "-1", "氏名": ""})]
        errors = service._validate_rows(rows)
        columns = {e.column for e in errors}
        assert "会計年度" in columns
        assert "4月" in columns
        assert "氏名" in columns

    def test_errors_across_multiple_rows_all_collected(self) -> None:
        rows = [
            _valid_row(**{"会計年度": "bad"}),
            _valid_row(**{"4月": "x"}),
            _valid_row(),
        ]
        errors = service._validate_rows(rows)
        row_nos = {e.row_no for e in errors}
        assert 1 in row_nos
        assert 2 in row_nos
        assert 3 not in row_nos

    # --- WBSコードは空でもエラーにしない ---
    def test_empty_wbs_code_is_not_an_error(self) -> None:
        rows = [_valid_row(**{"WBSコード": ""})]
        errors = service._validate_rows(rows)
        assert errors == []


# ---------------------------------------------------------------------------
# import_plan_csv 統合（バリデーション→例外）
# ---------------------------------------------------------------------------

class TestImportPlanCsvValidation:
    def test_missing_header_raises_validation_exception(self) -> None:
        headers = [h for h in REQUIRED_HEADERS if h != "4月"]
        csv_bytes = _make_csv(headers, [])
        with pytest.raises(CsvValidationException) as exc_info:
            service._validate_and_parse(csv_bytes)
        assert any(e.column == "4月" for e in exc_info.value.errors)

    def test_valid_csv_returns_parsed_rows(self) -> None:
        csv_bytes = _make_csv(REQUIRED_HEADERS, [_valid_row()])
        headers, rows = service._validate_and_parse(csv_bytes)
        assert headers is not None
        assert len(rows) == 1

    def test_row_errors_raise_validation_exception_with_all_errors(self) -> None:
        rows = [
            _valid_row(**{"会計年度": "bad"}),
            _valid_row(**{"4月": "-1"}),
        ]
        csv_bytes = _make_csv(REQUIRED_HEADERS, rows)
        with pytest.raises(CsvValidationException) as exc_info:
            service._validate_and_parse(csv_bytes)
        columns = {e.column for e in exc_info.value.errors}
        assert "会計年度" in columns
        assert "4月" in columns
