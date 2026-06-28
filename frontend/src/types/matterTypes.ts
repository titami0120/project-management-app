export interface MatterResponse {
  id: number
  name: string
  code: string
  client_name: string | null
  status: string
  pm_member_id: number | null
  project_count: number
  created_at: string
}

export interface MatterCreateRequest {
  name: string
  code: string
  client_name?: string
  status?: string
  pm_member_id?: number
}
