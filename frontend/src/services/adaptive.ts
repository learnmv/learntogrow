import { get, post } from './api'
import { getAuthHeaders } from './auth'
import type { QuestionFromDB } from '../types/questions'

/**
 * Fetch the next adaptive question for a domain based on the student's theta.
 */
export async function fetchAdaptiveQuestion(domainId: number): Promise<QuestionFromDB> {
  return get<QuestionFromDB>(`/questions/adaptive?domain_id=${domainId}`, {
    headers: getAuthHeaders(),
  })
}

/**
 * Record an answer and get theta update info.
 */
export async function recordAdaptiveAnswer(data: {
  question_id: number
  selected_answer: string
  is_correct: boolean
}): Promise<{
  message: string
  adaptive: {
    theta?: number
    previous_theta?: number
    updated?: boolean
    reason?: string
  }
}> {
  return post(`/questions/answer`, data)
}

/**
 * Get the student's theta for a domain.
 */
export async function fetchDomainTheta(domainId: number): Promise<{
  domain_id: number
  domain_name: string
  theta: number
  questions_attempted: number
  correct_streak: number
}> {
  return get(`/questions/adaptive-domain?domain_id=${domainId}`, {
    headers: getAuthHeaders(),
  })
}
