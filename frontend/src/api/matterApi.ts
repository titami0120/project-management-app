import type { MatterCreateRequest, MatterResponse } from '../types/matterTypes'
import apiClient from './client'

export const getMatters = async (): Promise<MatterResponse[]> => {
  const { data } = await apiClient.get<MatterResponse[]>('/api/v1/matters')
  return data
}

export const createMatter = async (request: MatterCreateRequest): Promise<MatterResponse> => {
  const { data } = await apiClient.post<MatterResponse>('/api/v1/matters', request)
  return data
}
