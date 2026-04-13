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
  attempt_id: number
  standard_code: string | null
  standard_description: string | null
  score: number
  total_questions: number
  time_spent_seconds: number | null
  completed_at: string | null
}

export interface LinkRequestData {
  student_email_or_username: string
}

export interface LinkRequestResponse {
  message: string
  link_id: number
  status: string
}