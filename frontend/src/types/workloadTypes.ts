import type { ImportSummary } from './commonTypes'

export interface CsvUploadResponse {
  summary: ImportSummary
}

export interface CsvValidationError {
  row_no: number | null
  column: string
  message: string
}

export interface CsvUploadErrorResponse {
  errors: CsvValidationError[]
}

export interface ForecastCell {
  planned_mm: number | null
  simulated_mm: number | null
  forecast_mm: number
}

export interface ForecastProjectRow {
  project_id: number
  project_name: string
  wbs_tmp: string
  matter_id: number | null
  matter_name: string | null
  cells: Record<string, ForecastCell>
}

export interface ForecastMemberRow {
  member_id: number
  member_name: string
  employee_code: string
  monthly_sums: Record<string, number>
  projects: ForecastProjectRow[]
}

export interface ForecastWorkloadResponse {
  months: string[]
  rows: ForecastMemberRow[]
}

export interface SimulationUpdateItem {
  member_id: number
  project_id: number
  year: number
  month: number
  simulated_mm: number | null
}

export interface SimulationUpdateRequest {
  updates: SimulationUpdateItem[]
}

export interface ForecastQueryParams {
  dept_id?: number
  team_id?: number
  project_id?: number
  from: string
  to: string
}

export interface ParticipatingProject {
  id: number
  wbs_tmp: string
  name: string
}
