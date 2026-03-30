import { post } from './api'
import type { GeneratedQuestion, QuestionGenerationRequest } from '../types/questions'

/**
 * Generate a question based on a standard
 */
export async function generateQuestion(
  request: QuestionGenerationRequest
): Promise<GeneratedQuestion> {
  return post<GeneratedQuestion>('/questions/generate', request)
}
