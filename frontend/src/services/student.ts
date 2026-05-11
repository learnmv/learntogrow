import { get, post } from './api'
import { getAuthHeaders } from './auth'
import type { Standard } from '../types/standards'
import type { StudentProgress, AnswerSubmit, DailyGoal, SkillMapDomain } from '../types/student'

export async function getOwnProgress(): Promise<StudentProgress> {
  return get<StudentProgress>('/student/progress', { headers: getAuthHeaders() })
}

export async function recordAnswer(data: AnswerSubmit): Promise<{ message: string }> {
  return post<{ message: string }>('/questions/answer', data, { headers: getAuthHeaders() })
}

export async function getDailyGoal(target = 10): Promise<DailyGoal> {
  return get<DailyGoal>(`/student/daily-goal?target=${target}`, { headers: getAuthHeaders() })
}

export async function getSkillMap(
  params: { subject_id?: number; grade_id?: number } = {}
): Promise<SkillMapDomain[]> {
  const query = new URLSearchParams()
  if (params.subject_id !== undefined) query.set('subject_id', String(params.subject_id))
  if (params.grade_id !== undefined) query.set('grade_id', String(params.grade_id))
  const qs = query.toString()
  return get<SkillMapDomain[]>(`/student/skill-map${qs ? `?${qs}` : ''}`, {
    headers: getAuthHeaders(),
  })
}

export async function fetchMistakeStandards(
  params: { subject_id?: number; grade_id?: number } = {}
): Promise<Standard[]> {
  const url = '/student/mistake-standards'
  const query = new URLSearchParams()
  if (params.subject_id !== undefined) query.set('subject_id', String(params.subject_id))
  if (params.grade_id !== undefined) query.set('grade_id', String(params.grade_id))
  const qs = query.toString()
  return get<Standard[]>(qs ? `${url}?${qs}` : url, { headers: getAuthHeaders() })
}
