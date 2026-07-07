import type {
  MemberCreateRequest,
  MemberResponse,
  MemberUpdateRequest,
} from '../types/projectTypes'
import apiClient from './client'

export const getMembers = async (deptId?: number): Promise<MemberResponse[]> => {
  const { data } = await apiClient.get<MemberResponse[]>('/api/v1/members', {
    params: deptId !== undefined ? { dept_id: deptId } : undefined,
  })
  return data
}

export const createMember = async (body: MemberCreateRequest): Promise<MemberResponse> => {
  const { data } = await apiClient.post<MemberResponse>('/api/v1/members', body)
  return data
}

export const updateMember = async (id: number, body: MemberUpdateRequest): Promise<MemberResponse> => {
  const { data } = await apiClient.put<MemberResponse>(`/api/v1/members/${id}`, body)
  return data
}

export const deleteMember = async (id: number): Promise<void> => {
  await apiClient.delete(`/api/v1/members/${id}`)
}
