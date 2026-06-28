export interface ProjectResponse {
  id: number
  wbs_tmp: string
  name: string
  code: string | null
  display_order: number | null
  matter_id: number | null
  matter_name: string | null
  created_at: string
}

export interface ProjectUpdateRequest {
  name?: string
  code?: string
  display_order?: number
}

export interface ProjectMatterAssignRequest {
  matter_id: number
}

export interface DepartmentResponse {
  id: number
  name: string
  code: string
}

export interface MemberResponse {
  id: number
  name: string
  employee_code: string
  department_id: number
  department_name: string
}

export interface ForecastVersionResponse {
  id: number
  version_no: number
  trigger_type: string
  note: string | null
  created_at: string
}
