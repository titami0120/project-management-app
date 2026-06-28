import type { MemberResponse } from '../types/projectTypes'
import apiClient from './client'

export const getMembers = async (deptId?: number): Promise<MemberResponse[]> => {
  const { data } = await apiClient.get<MemberResponse[]>('/api/v1/members', {
    params: deptId !== undefined ? { dept_id: deptId } : undefined,
  })
  return data
}
