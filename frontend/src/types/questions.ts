export type QuestionType = 'multiple_choice' | 'open_ended'

export interface GeneratedQuestion {
  question: string
  question_type: QuestionType
  options: string[]
  answer: string
  explanation: string
  standard_code: string
  difficulty: number
}

export interface QuestionGenerationRequest {
  standard_id: number
  difficulty?: number
  question_type?: QuestionType
  custom_prompt?: string
  model?: string
}
