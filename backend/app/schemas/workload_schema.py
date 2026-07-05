from pydantic import BaseModel


class ImportCount(BaseModel):
    created: int
    updated: int


class ImportSummary(BaseModel):
    departments: ImportCount
    members: ImportCount
    projects: ImportCount
    workloads: ImportCount


class CsvUploadResponse(BaseModel):
    version_no: int
    summary: ImportSummary


class CsvValidationError(BaseModel):
    row_no: int | None
    column: str
    message: str


class CsvUploadErrorResponse(BaseModel):
    errors: list[CsvValidationError]


class ForecastCell(BaseModel):
    planned_mm: float | None = None
    simulated_mm: float | None = None
    forecast_mm: float


class ForecastProjectRow(BaseModel):
    project_id: int
    project_name: str
    wbs_tmp: str
    matter_id: int | None = None
    matter_name: str | None = None
    cells: dict[str, ForecastCell]


class ForecastMemberRow(BaseModel):
    member_id: int
    member_name: str
    employee_code: str
    monthly_sums: dict[str, float]
    projects: list[ForecastProjectRow]


class ForecastWorkloadResponse(BaseModel):
    months: list[str]
    rows: list[ForecastMemberRow]


class SimulationUpdateItem(BaseModel):
    member_id: int
    project_id: int
    year: int
    month: int
    simulated_mm: float | None


class SimulationUpdateRequest(BaseModel):
    updates: list[SimulationUpdateItem]


class ParticipatingProject(BaseModel):
    id: int
    wbs_tmp: str
    name: str
