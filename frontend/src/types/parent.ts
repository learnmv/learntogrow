export interface ParentStudentLink {
  id: number
  parent_id: number
  student_id: number
  student_name: string
  student_email: string
  student_username: string
  status: 'pending' | 'approved' | 'rejected'
  requested_at: string
  approved_at: string | null
}

export interface StudentDetailForParent {
  student_id: number
  student_name: string
  student_username: string
  email: string
  total_attempts: number
  average_score: number | null
  standards_attempted: number
  recent_attempts: DetailedAttempt[]
}

export interface DetailedAttempt {
  answer_id: number
  question_id: number
  standard_code: string | null
  standard_description: string | null
  is_correct: boolean
  answered_at: string | null
}

export interface LinkRequestData {
  student_email_or_username: string
}

export interface LinkRequestResponse {
  message: string
  link_id: number
  status: string
}

export interface ParentAssistantChatRequest {
  message: string
  student_id?: number
  subject_id?: number
  grade_id?: number
}

export interface ParentAssistantChatResponse {
  intent: string
  answer: string
  requires_student: boolean
  requires_subject: boolean
  suggestions: string[]
  data: Record<string, unknown>
}
