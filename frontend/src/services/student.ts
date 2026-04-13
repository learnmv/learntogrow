import { get, post } from './api'
import { getAuthHeaders } from './auth'
import type { StudentProgress, AnswerSubmit } from '../types/student'

export async function getOwnProgress(): Promise<StudentProgress> {
  return get<StudentProgress>('/student/progress', { headers: getAuthHeaders() })
}

export async function getOwnAttempts(): Promise<StudentProgress> {
  return get<StudentProgress>('/student/attempts', { headers: getAuthHeaders() })
}

export async function recordAnswer(data: AnswerSubmit): Promise<{ message: string }> {
  return post<{ message: string }>('/questions/answer', data, { headers: getAuthHeaders() })
}