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
  quality_mode?: 'reviewed' | 'quality';
  candidate_count?: number;
  max_repair_attempts?: number;
  min_review_score?: number;
}

export interface QuestionGenerateResponse {
  message: string;
  standards_matched: number;
  standards_completed: number;
  standards_failed: number;
  questions_created: number;
  errors: string[] | null;
}

// --- Generation Jobs (async) ---

export type JobStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
export type JobStandardStatus = 'pending' | 'running' | 'done' | 'failed';

export interface GenerationJobStandard {
  id: number;
  standard_id: number;
  standard_code?: string | null;
  cluster_id?: number | null;
  target_difficulty?: number | null;
  difficulty_band?: string | null;
  generation_reason?: string | null;
  questions_requested: number;
  questions_created: number;
  status: JobStandardStatus;
  error?: string | null;
  avg_quality_score?: number | null;
  last_review_notes?: string | null;
  quality_summary?: {
    planner_runs?: number;
    candidate_runs?: number;
    review_runs?: number;
    repair_runs?: number;
    best_review_score?: number | null;
  };
  started_at?: string | null;
  completed_at?: string | null;
}

export interface GenerationJob {
  id: number;
  status: JobStatus;
  subject_id?: number | null;
  grade_id?: number | null;
  total_standards: number;
  completed_standards: number;
  failed_standards: number;
  questions_created: number;
  question_type: string;
  model?: string | null;
  timeout: number;
  quality_mode: 'fast' | 'reviewed' | 'quality';
  candidate_count: number;
  max_repair_attempts: number;
  min_review_score: number;
  errors: string[];
  created_by?: number | null;
  started_at?: string | null;
  completed_at?: string | null;
  created_at?: string | null;
  job_standards?: GenerationJobStandard[];
}

export interface CreateGenerationJobRequest {
  standard_ids: number[];
  questions_per_standard?: number;
  question_type?: 'multiple_choice' | 'open_ended';
  model?: string;
  timeout?: number;
  quality_mode?: 'reviewed' | 'quality';
  candidate_count?: number;
  max_repair_attempts?: number;
  min_review_score?: number;
  subject_id?: number;
  grade_id?: number;
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
  fill_mode: 'gaps' | 'struggling' | 'balanced' | 'difficulty' | 'diagrams';
  max_standards: number;
}

export interface SmartFillResponse {
  suggestions: SmartFillSuggestion[];
  total_suggested: number;
  estimated_generation_time: string;
}

export type CoverageGoal = 'fill_missing' | 'full_ladder' | 'top_up' | 'challenge_heavy';

export interface ClusterCoveragePlanRequest {
  subject_id: number;
  grade_id: number;
  cluster_ids: number[];
  coverage_goal: CoverageGoal;
  target_per_band: number;
}

export interface ClusterCoverageJobRequest extends ClusterCoveragePlanRequest {
  question_type?: 'multiple_choice' | 'open_ended';
  model?: string;
  timeout?: number;
  quality_mode?: 'reviewed' | 'quality';
  candidate_count?: number;
  max_repair_attempts?: number;
  min_review_score?: number;
}

export interface DifficultyBandInfo {
  band: string;
  min: number;
  max: number;
  target: number;
}

export interface ClusterCoveragePlanItem {
  standard_id: number;
  standard_code: string;
  standard_description: string;
  cluster_id: number;
  cluster_code?: string | null;
  cluster_name?: string | null;
  difficulty_band: string;
  target_difficulty: number;
  existing_count: number;
  reason: string;
}

export interface ClusterCoverageStandardReport {
  standard_id: number;
  standard_code: string;
  standard_description: string;
  cluster_id: number;
  cluster_code?: string | null;
  cluster_name?: string | null;
  band_counts: Record<string, number>;
  planned_bands: string[];
  planned_count: number;
}

export interface ClusterCoverageClusterReport {
  cluster_id: number;
  cluster_code: string;
  cluster_name: string;
  standard_count: number;
  planned_count: number;
}

export interface ClusterCoveragePlanResponse {
  coverage_goal: CoverageGoal;
  grade_id: number;
  cluster_ids: number[];
  difficulty_bands: DifficultyBandInfo[];
  coverage_before: number;
  coverage_after: number;
  total_planned: number;
  estimated_generation_time: string;
  clusters: ClusterCoverageClusterReport[];
  standards: ClusterCoverageStandardReport[];
  items: ClusterCoveragePlanItem[];
}

export interface AdminChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface AdminChatRequest {
  messages: AdminChatMessage[];
  temperature?: number;
}

export interface AdminChatResponse {
  message: AdminChatMessage;
  model: string;
}
