import type { CreateVersionRequest, ForecastVersionResponse } from '../types/projectTypes'
import apiClient from './client'

export const getForecastVersions = async (): Promise<ForecastVersionResponse[]> => {
  const { data } = await apiClient.get<ForecastVersionResponse[]>('/api/v1/forecast-versions')
  return data
}

export const createForecastVersion = async (
  req: CreateVersionRequest
): Promise<ForecastVersionResponse> => {
  const { data } = await apiClient.post<ForecastVersionResponse>('/api/v1/forecast-versions', req)
  return data
}

export const restoreForecastVersion = async (
  versionId: number
): Promise<{ restored_count: number }> => {
  const { data } = await apiClient.post<{ restored_count: number }>(
    `/api/v1/forecast-versions/${versionId}/restore`
  )
  return data
}

export const deleteForecastVersion = async (versionId: number): Promise<void> => {
  await apiClient.delete(`/api/v1/forecast-versions/${versionId}`)
}
