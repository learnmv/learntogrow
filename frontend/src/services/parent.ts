import { get, post } from './api'
import { getAuthHeaders } from './auth'
import type {
  ParentStudentLink,
  LinkRequestData,
  LinkRequestResponse,
  StudentDetailForParent,
} from '../types/parent'

export async function getLinkedChildren(): Promise<ParentStudentLink[]> {
  return get<ParentStudentLink[]>('/parent/children', { headers: getAuthHeaders() })
}

export async function requestStudentLink(data: LinkRequestData): Promise<LinkRequestResponse> {
  return post<LinkRequestResponse>('/parent/link-request', data, { headers: getAuthHeaders() })
}

export async function getChildProgress(studentId: number): Promise<StudentDetailForParent> {
  return get<StudentDetailForParent>(`/parent/child/${studentId}/progress`, { headers: getAuthHeaders() })
}