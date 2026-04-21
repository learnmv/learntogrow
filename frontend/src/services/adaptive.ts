import { get } from './api';
import { getAuthHeaders } from './auth';
import type { QuestionFromDB } from '../types/questions';

export interface DomainProgress {
  domain_id: number;
  domain_name: string;
  domain_code: string;
  total_answered: number;
  correct_count: number;
  accuracy: number;
  current_difficulty: number;
  last_answered_at: string | null;
}

export interface StrengthWeaknessItem {
  domain_id: number;
  domain_name: string;
  domain_code: string;
  accuracy: number;
  total_answered: number;
  recommendation: string;
}

export interface StrengthsWeaknesses {
  strengths: StrengthWeaknessItem[];
  weaknesses: StrengthWeaknessItem[];
  recommendations: string[];
}

/**
 * Get an adaptively-selected question for a grade
 */
export async function getAdaptiveQuestion(gradeId: number): Promise<QuestionFromDB> {
  return get<QuestionFromDB>(`/questions/adaptive/${gradeId}`, { headers: getAuthHeaders() });
}

/**
 * Get per-domain progress
 */
export async function getDomainProgress(): Promise<DomainProgress[]> {
  return get<DomainProgress[]>('/student/domain-progress', { headers: getAuthHeaders() });
}

/**
 * Get strengths and weaknesses
 */
export async function getStrengthsWeaknesses(): Promise<StrengthsWeaknesses> {
  return get<StrengthsWeaknesses>('/student/strengths-weaknesses', { headers: getAuthHeaders() });
}
