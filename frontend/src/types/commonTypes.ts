export interface ImportCount {
  created: number
  updated: number
}

export interface ImportSummary {
  departments: ImportCount
  members: ImportCount
  projects: ImportCount
  workloads: ImportCount
}

export interface ApiError {
  detail: string
}
