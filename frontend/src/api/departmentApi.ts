import type {
  DepartmentCreateRequest,
  DepartmentResponse,
  DepartmentUpdateRequest,
} from '../types/projectTypes'
import apiClient from './client'

export const getDepartments = async (): Promise<DepartmentResponse[]> => {
  const { data } = await apiClient.get<DepartmentResponse[]>('/api/v1/departments')
  return data
}

export const createDepartment = async (body: DepartmentCreateRequest): Promise<DepartmentResponse> => {
  const { data } = await apiClient.post<DepartmentResponse>('/api/v1/departments', body)
  return data
}

export const updateDepartment = async (id: number, body: DepartmentUpdateRequest): Promise<DepartmentResponse> => {
  const { data } = await apiClient.put<DepartmentResponse>(`/api/v1/departments/${id}`, body)
  return data
}

export const deleteDepartment = async (id: number): Promise<void> => {
  await apiClient.delete(`/api/v1/departments/${id}`)
}
