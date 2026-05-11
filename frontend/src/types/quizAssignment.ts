import type { QuestionFromDB } from './questions'

export type QuizAssignmentStatus = 'assigned' | 'in_progress' | 'completed'
export type QuizAssignmentDifficulty = 'easy' | 'medium' | 'hard' | 'mixed'

export interface QuizAssignmentCreateRequest {
  student_id: number
  title: string
  description?: string
  subject_id?: number
  grade_id?: number
  domain_ids?: number[]
  standard_ids?: number[]
  difficulty: QuizAssignmentDifficulty
  question_count: number
  due_at?: string
}

export interface QuizAssignmentSummary {
  id: number
  parent_id: number
  student_id: number
  student_name: string | null
  title: string
  description: string | null
  difficulty: QuizAssignmentDifficulty
  status: QuizAssignmentStatus
  question_count: number
  answered_count: number
  correct_count: number
  subject_id: number | null
  subject_name: string | null
  grade_id: number | null
  grade_name: string | null
  created_at: string | null
  started_at: string | null
  completed_at: string | null
  due_at: string | null
}

export interface QuizAssignmentAnswerState {
  question_id: number
  selected_answer: string | null
  is_correct: boolean
  answered_at: string | null
}

export interface QuizAssignmentDetail extends QuizAssignmentSummary {
  questions: QuestionFromDB[]
  answers: QuizAssignmentAnswerState[]
}
