export interface StudentProgress {
  total_answered: number
  correct_count: number
  accuracy: number | null
  standards_attempted: number
  recent_answers: RecentAnswer[]
}

export interface RecentAnswer {
  question_id: number
  standard_code: string
  is_correct: boolean
  answered_at: string
}

export interface AnswerSubmit {
  question_id: number
  selected_answer: string
  is_correct: boolean
}