import type {
  ProjectMatterAssignRequest,
  ProjectResponse,
  ProjectUpdateRequest,
} from '../types/projectTypes'
import apiClient from './client'

export const getProjects = async (unassigned?: boolean): Promise<ProjectResponse[]> => {
  const { data } = await apiClient.get<ProjectResponse[]>('/api/v1/projects', {
    params: unassigned ? { unassigned: true } : undefined,
  })
  return data
}

export const updateProject = async (
  id: number,
  request: ProjectUpdateRequest
): Promise<ProjectResponse> => {
  const { data } = await apiClient.put<ProjectResponse>(`/api/v1/projects/${id}`, request)
  return data
}

export const assignProjectMatter = async (
  id: number,
  request: ProjectMatterAssignRequest
): Promise<ProjectResponse> => {
  const { data } = await apiClient.put<ProjectResponse>(`/api/v1/projects/${id}/matter`, request)
  return data
}
