import type {
  TeamCreateRequest,
  TeamMemberResponse,
  TeamResponse,
  TeamUpdateRequest,
} from '../types/projectTypes'
import apiClient from './client'

export const getTeams = async (): Promise<TeamResponse[]> => {
  const { data } = await apiClient.get<TeamResponse[]>('/api/v1/teams')
  return data
}

export const createTeam = async (body: TeamCreateRequest): Promise<TeamResponse> => {
  const { data } = await apiClient.post<TeamResponse>('/api/v1/teams', body)
  return data
}

export const updateTeam = async (id: number, body: TeamUpdateRequest): Promise<TeamResponse> => {
  const { data } = await apiClient.put<TeamResponse>(`/api/v1/teams/${id}`, body)
  return data
}

export const deleteTeam = async (id: number): Promise<void> => {
  await apiClient.delete(`/api/v1/teams/${id}`)
}

export const getTeamMembers = async (teamId: number): Promise<TeamMemberResponse[]> => {
  const { data } = await apiClient.get<TeamMemberResponse[]>(`/api/v1/teams/${teamId}/members`)
  return data
}

export const addTeamMember = async (teamId: number, memberId: number): Promise<void> => {
  await apiClient.post(`/api/v1/teams/${teamId}/members/${memberId}`)
}

export const removeTeamMember = async (teamId: number, memberId: number): Promise<void> => {
  await apiClient.delete(`/api/v1/teams/${teamId}/members/${memberId}`)
}
