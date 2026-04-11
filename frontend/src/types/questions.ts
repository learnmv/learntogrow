export type QuestionType = 'multiple_choice' | 'open_ended'

interface QuestionContent {
  question_type: QuestionType
  options: string[] | null
  explanation: string | null
}

export interface GeneratedQuestion extends QuestionContent {
  question: string
  answer: string
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

export interface QuestionFromDB extends QuestionContent {
  id: number
  standard_id: number
  question_text: string
  correct_answer: string
  difficulty: number | null
  is_active: boolean
  created_at: string | null
  updated_at: string | null
  generated_by: string | null
}
