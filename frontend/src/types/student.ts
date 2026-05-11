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

export interface DailyGoal {
  target: number
  answered_today: number
  correct_today: number
  remaining: number
  completed: boolean
  progress: number
  message: string
}

export interface SkillMapDomain {
  domain_id: number
  domain_name: string
  domain_code: string
  progress: number
  level: string
  level_description: string
  questions_attempted: number
  correct_count: number
  incorrect_count: number
  accuracy: number | null
  correct_streak: number
  total_standards: number
  active_questions: number
  recommended: boolean
  recommendation_reason: string
  sort_priority: number
}
