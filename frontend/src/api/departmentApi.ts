import type { DepartmentResponse } from '../types/projectTypes'
import apiClient from './client'

export const getDepartments = async (): Promise<DepartmentResponse[]> => {
  const { data } = await apiClient.get<DepartmentResponse[]>('/api/v1/departments')
  return data
}
