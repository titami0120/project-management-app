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

export interface ProjectCreateRequest {
  wbs_tmp: string
  name: string
  code?: string
  display_order?: number
  matter_id?: number | null
}

export interface ProjectUpdateRequest {
  name?: string
  code?: string
  display_order?: number
  matter_id?: number | null
}

export interface ProjectMatterAssignRequest {
  matter_id: number
}

export interface DepartmentResponse {
  id: number
  name: string
  code: string
}

export interface DepartmentCreateRequest {
  code: string
  name: string
}

export interface DepartmentUpdateRequest {
  name: string
}

export interface MemberResponse {
  id: number
  name: string
  employee_code: string
  department_id: number
  department_name: string
}

export interface MemberCreateRequest {
  employee_code: string
  name: string
  department_id: number
}

export interface MemberUpdateRequest {
  name: string
  department_id: number
}

export interface TeamResponse {
  id: number
  name: string
  department_id: number
  department_name: string
  member_count: number
}

export interface TeamMemberResponse {
  member_id: number
  employee_code: string
  name: string
  department_name: string
}

export interface TeamCreateRequest {
  name: string
  department_id: number
}

export interface TeamUpdateRequest {
  name: string
  department_id: number
}

export interface ForecastVersionResponse {
  id: number
  version_no: number
  name: string
  description: string | null
  snapshot_count: number
  created_at: string
}

export interface CreateVersionRequest {
  name: string
  description?: string
}
