import type { ForecastVersionResponse } from '../types/projectTypes'
import apiClient from './client'

export const getForecastVersions = async (): Promise<ForecastVersionResponse[]> => {
  const { data } = await apiClient.get<ForecastVersionResponse[]>('/api/v1/forecast-versions')
  return data
}
