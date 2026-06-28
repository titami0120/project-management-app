import type {
  CsvUploadResponse,
  ForecastQueryParams,
  ForecastWorkloadResponse,
  ParticipatingProject,
  SimulationUpdateRequest,
} from '../types/workloadTypes'
import apiClient from './client'

export const uploadPlanCsv = async (file: File): Promise<CsvUploadResponse> => {
  const form = new FormData()
  form.append('file', file)
  const { data } = await apiClient.post<CsvUploadResponse>(
    '/api/v1/workloads/plan/upload',
    form,
    { headers: { 'Content-Type': undefined } }
  )
  return data
}

export const getForecast = async (
  params: ForecastQueryParams
): Promise<ForecastWorkloadResponse> => {
  const { data } = await apiClient.get<ForecastWorkloadResponse>('/api/v1/workloads/forecast', {
    params,
  })
  return data
}

export const saveSimulation = async (request: SimulationUpdateRequest): Promise<void> => {
  await apiClient.put('/api/v1/workloads/simulate', request)
}

export const resetSimulation = async (
  memberId?: number,
  projectId?: number
): Promise<void> => {
  await apiClient.delete('/api/v1/workloads/simulate', {
    params: { member_id: memberId, project_id: projectId },
  })
}

export const getParticipatingProjects = async (
  deptId?: number
): Promise<ParticipatingProject[]> => {
  const { data } = await apiClient.get<ParticipatingProject[]>(
    '/api/v1/workloads/participating-projects',
    { params: deptId !== undefined ? { dept_id: deptId } : {} }
  )
  return data
}

export const downloadForecastCsv = async (params: ForecastQueryParams): Promise<Blob> => {
  const { data } = await apiClient.get<Blob>('/api/v1/workloads/forecast/download', {
    params,
    responseType: 'blob',
  })
  return data
}
