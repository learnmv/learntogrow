export interface StudentProgress {
  total_answered: number
  correct_count: number
  accuracy: number | null
  standards_attempted: number
}

export interface AnswerSubmit {
  question_id: number
  selected_answer: string
  is_correct: boolean
}