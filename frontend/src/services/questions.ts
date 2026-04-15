import { get, post } from './api'
import { getAuthHeaders } from './auth'
import type { GeneratedQuestion, QuestionGenerationRequest, QuestionFromDB } from '../types/questions'

/**
 * Generate a question based on a standard
 */
export async function generateQuestion(
  request: QuestionGenerationRequest
): Promise<GeneratedQuestion> {
  return post<GeneratedQuestion>('/questions/generate', request)
}

export async function fetchQuestionsByStandard(
  standardId: number,
  limit?: number
): Promise<QuestionFromDB[]> {
  const params = limit ? `?limit=${limit}` : ''
  return get<QuestionFromDB[]>(`/questions/standard/${standardId}${params}`, {
    headers: getAuthHeaders()
  })
}
