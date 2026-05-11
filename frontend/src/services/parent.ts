import { get, post } from './api'
import { getAuthHeaders } from './auth'
import type {
  ParentStudentLink,
  LinkRequestData,
  LinkRequestResponse,
  ParentAssistantChatRequest,
  ParentAssistantChatResponse,
  StudentDetailForParent,
} from '../types/parent'
import type {
  QuizAssignmentCreateRequest,
  QuizAssignmentDetail,
  QuizAssignmentSummary,
} from '../types/quizAssignment'

export async function getLinkedChildren(): Promise<ParentStudentLink[]> {
  return get<ParentStudentLink[]>('/parent/children', { headers: getAuthHeaders() })
}

export async function requestStudentLink(data: LinkRequestData): Promise<LinkRequestResponse> {
  return post<LinkRequestResponse>('/parent/link-request', data, { headers: getAuthHeaders() })
}

export async function getChildProgress(studentId: number): Promise<StudentDetailForParent> {
  return get<StudentDetailForParent>(`/parent/child/${studentId}/progress`, { headers: getAuthHeaders() })
}

export async function sendParentAssistantMessage(
  data: ParentAssistantChatRequest
): Promise<ParentAssistantChatResponse> {
  return post<ParentAssistantChatResponse>('/parent/assistant/chat', data, {
    headers: getAuthHeaders(),
  })
}

export async function createQuizAssignment(
  data: QuizAssignmentCreateRequest
): Promise<QuizAssignmentDetail> {
  return post<QuizAssignmentDetail>('/parent/quiz-assignments', data, {
    headers: getAuthHeaders(),
  })
}

export async function getParentQuizAssignments(): Promise<QuizAssignmentSummary[]> {
  return get<QuizAssignmentSummary[]>('/parent/quiz-assignments', {
    headers: getAuthHeaders(),
  })
}
