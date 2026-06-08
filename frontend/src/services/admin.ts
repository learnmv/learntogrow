import { get, post, patch, del } from './api';
import { getAuthHeaders } from './auth';
import type {
  QuestionGenerateRequest,
  QuestionGenerateResponse,
  CreateGenerationJobRequest,
  GenerationJob,
  AdminDashboardStats,
  PendingParentLink,
  UserCreateRequest,
  UserStatusUpdate,
  QuestionInsightsResponse,
  SmartFillRequest,
  SmartFillResponse,
  ClusterCoveragePlanRequest,
  ClusterCoverageJobRequest,
  ClusterCoveragePlanResponse,
  AdminChatRequest,
  AdminChatResponse,
} from '../types/admin';
import type { User } from '../types/auth';
import type { QuestionFromDB } from '../types/questions';

/**
 * Get admin dashboard statistics
 */
export async function getDashboardStats(): Promise<AdminDashboardStats> {
  return get<AdminDashboardStats>('/admin/dashboard/stats', { headers: getAuthHeaders() });
}

/**
 * Get all users
 */
export async function getUsers(role?: string): Promise<User[]> {
  const params = role ? `?role=${role}` : '';
  return get<User[]>(`/admin/users${params}`, { headers: getAuthHeaders() });
}

/**
 * Create new user
 */
export async function createUser(data: UserCreateRequest): Promise<User> {
  return post<User>('/admin/users', data, { headers: getAuthHeaders() });
}

/**
 * Update user status
 */
export async function updateUserStatus(userId: number, data: UserStatusUpdate): Promise<User> {
  return patch<User>(`/admin/users/${userId}/status`, data, { headers: getAuthHeaders() });
}

/**
 * Delete user
 */
export async function deleteUser(userId: number): Promise<void> {
  return del(`/admin/users/${userId}`, { headers: getAuthHeaders() });
}

/**
 * Get pending parent links
 */
export async function getPendingLinks(): Promise<PendingParentLink[]> {
  return get<PendingParentLink[]>('/admin/pending-links', { headers: getAuthHeaders() });
}

/**
 * Approve parent link
 */
export async function approveParentLink(linkId: number): Promise<{ message: string }> {
  return post(`/admin/approve-link/${linkId}`, {}, { headers: getAuthHeaders() });
}

/**
 * Reject parent link
 */
export async function rejectParentLink(linkId: number, reason?: string): Promise<{ message: string }> {
  return post(`/admin/reject-link/${linkId}`, { reason }, { headers: getAuthHeaders() });
}

/**
 * Get questions with filters
 */
export async function getAdminQuestions(
  standardId?: number,
  domainId?: number,
  gradeId?: number,
  isActive?: boolean
): Promise<QuestionFromDB[]> {
  const params = new URLSearchParams();
  if (standardId) params.append('standard_id', standardId.toString());
  if (domainId) params.append('domain_id', domainId.toString());
  if (gradeId) params.append('grade_id', gradeId.toString());
  if (isActive !== undefined) params.append('is_active', isActive.toString());

  const queryString = params.toString();
  return get<QuestionFromDB[]>(`/admin/questions${queryString ? `?${queryString}` : ''}`, {
    headers: getAuthHeaders(),
  });
}

/**
 * Update question
 */
export async function updateQuestion(questionId: number, updates: Partial<QuestionFromDB>): Promise<QuestionFromDB> {
  return patch<QuestionFromDB>(`/admin/questions/${questionId}`, updates, { headers: getAuthHeaders() });
}

/**
 * Delete question
 */
export async function deleteQuestion(questionId: number): Promise<void> {
  return del(`/admin/questions/${questionId}`, { headers: getAuthHeaders() });
}

/**
 * Bulk delete questions
 */
export async function bulkDeleteQuestions(data: {
  question_ids?: number[];
  standard_id?: number;
  domain_id?: number;
  grade_id?: number;
  is_active?: boolean;
  all_matching?: boolean;
}): Promise<{ deleted: number }> {
  return post<{ deleted: number }>('/admin/questions/bulk-delete', data, { headers: getAuthHeaders() });
}

/**
 * Toggle question status
 */
export async function toggleQuestionStatus(questionId: number): Promise<QuestionFromDB> {
  return post<QuestionFromDB>(`/admin/questions/${questionId}/toggle-status`, {}, { headers: getAuthHeaders() });
}

/**
 * Generate questions (legacy endpoint - now returns a GenerationJob)
 */
export async function generateQuestions(data: QuestionGenerateRequest): Promise<QuestionGenerateResponse> {
  return post<QuestionGenerateResponse>('/admin/generate-questions', data, { headers: getAuthHeaders() });
}

// --- Async Generation Jobs ---

/**
 * Create a new generation job
 */
export async function createGenerationJob(data: CreateGenerationJobRequest): Promise<GenerationJob> {
  return post<GenerationJob>('/admin/generation-jobs', data, { headers: getAuthHeaders() });
}

/**
 * List generation jobs
 */
export async function listGenerationJobs(status?: string): Promise<GenerationJob[]> {
  const params = status ? `?status=${status}` : '';
  return get<GenerationJob[]>(`/admin/generation-jobs${params}`, { headers: getAuthHeaders() });
}

/**
 * Get a single generation job with details
 */
export async function getGenerationJob(jobId: number): Promise<GenerationJob> {
  return get<GenerationJob>(`/admin/generation-jobs/${jobId}`, { headers: getAuthHeaders() });
}

/**
 * Cancel a generation job
 */
export async function cancelGenerationJob(jobId: number): Promise<void> {
  return del(`/admin/generation-jobs/${jobId}`, { headers: getAuthHeaders() });
}

/**
 * Retry failed standards from a job
 */
export async function retryFailedStandards(jobId: number): Promise<GenerationJob> {
  return post<GenerationJob>(`/admin/generation-jobs/${jobId}/retry`, {}, { headers: getAuthHeaders() });
}

/**
 * Get question insights
 */
export async function getQuestionInsights(subjectId?: number, gradeId?: number): Promise<QuestionInsightsResponse> {
  const params = new URLSearchParams();
  if (subjectId) params.append('subject_id', subjectId.toString());
  if (gradeId) params.append('grade_id', gradeId.toString());
  const qs = params.toString();
  return get<QuestionInsightsResponse>(`/admin/question-insights${qs ? `?${qs}` : ''}`, { headers: getAuthHeaders() });
}

/**
 * Get smart fill suggestions
 */
export async function getSmartFillSuggestions(data: SmartFillRequest): Promise<SmartFillResponse> {
  return post<SmartFillResponse>('/admin/smart-fill-suggestions', data, { headers: getAuthHeaders() });
}

/**
 * Preview cluster coverage generation plan
 */
export async function getClusterCoveragePlan(
  data: ClusterCoveragePlanRequest
): Promise<ClusterCoveragePlanResponse> {
  return post<ClusterCoveragePlanResponse>('/admin/coverage-plan', data, { headers: getAuthHeaders() });
}

/**
 * Create cluster coverage generation job
 */
export async function createClusterCoverageJob(data: ClusterCoverageJobRequest): Promise<GenerationJob> {
  return post<GenerationJob>('/admin/coverage-jobs', data, { headers: getAuthHeaders() });
}

/**
 * Chat directly with the configured admin Ollama model
 */
export async function sendAdminChatMessage(data: AdminChatRequest): Promise<AdminChatResponse> {
  return post<AdminChatResponse>('/admin/chat', data, { headers: getAuthHeaders() });
}
