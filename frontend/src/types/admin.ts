export interface QuestionGenerateRequest {
  subject_id: number;
  grade_id?: number;
  domain_ids?: number[];
  standard_ids?: number[];
  difficulty_min?: number;
  difficulty_max?: number;
  questions_per_standard: number;
  question_type: 'multiple_choice' | 'open_ended';
  model?: string;
  timeout?: number;
}

export interface QuestionGenerateResponse {
  message: string;
  standards_matched: number;
  standards_completed: number;
  standards_failed: number;
  questions_created: number;
  errors: string[] | null;
}

export interface AdminDashboardStats {
  total_users: number;
  total_students: number;
  total_parents: number;
  total_admins: number;
  total_questions: number;
  total_quiz_attempts: number;
  pending_parent_links: number;
  recent_quiz_attempts: number;
}

export interface PendingParentLink {
  id: number;
  parent_name: string;
  parent_email: string;
  parent_username: string;
  student_name: string;
  student_email: string;
  student_username: string;
  requested_at: string;
}

export interface UserCreateRequest {
  username: string;
  email: string;
  password: string;
  role: 'student' | 'parent' | 'admin';
  full_name?: string;
  is_active?: boolean;
}

export interface UserStatusUpdate {
  is_active: boolean;
}

export interface DomainInsight {
  domain_id: number;
  domain_name: string;
  domain_code: string;
  standard_count: number;
  question_count: number;
  answered_count: number;
  accuracy: number | null;
  coverage_status: string;
  avg_difficulty: number | null;
}

export interface QuestionInsightsResponse {
  total_standards: number;
  total_questions: number;
  coverage_percent: number;
  domains: DomainInsight[];
}

export interface SmartFillSuggestion {
  standard_id: number;
  standard_code: string;
  standard_description: string;
  domain_name: string;
  reason: string;
  suggested_difficulty: number;
  suggested_count: number;
}

export interface SmartFillRequest {
  subject_id: number;
  grade_id?: number;
  fill_mode: 'gaps' | 'struggling' | 'balanced';
  max_standards: number;
}

export interface SmartFillResponse {
  suggestions: SmartFillSuggestion[];
  total_suggested: number;
  estimated_generation_time: string;
}
