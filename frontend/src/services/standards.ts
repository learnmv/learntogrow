import { get } from './api'
import type { Subject, Grade, Domain, Cluster, Standard, HierarchyFilter } from '../types/standards'

/**
 * Fetch all subjects
 */
export async function fetchSubjects(): Promise<Subject[]> {
  return get<Subject[]>('/subjects')
}

/**
 * Fetch grades, optionally filtered by subject
 */
export async function fetchGrades(subjectId?: number): Promise<Grade[]> {
  const query = subjectId ? `?subject_id=${subjectId}` : ''
  return get<Grade[]>(`/grades${query}`)
}

/**
 * Fetch domains, optionally filtered by subject
 */
export async function fetchDomains(subjectId?: number): Promise<Domain[]> {
  const query = subjectId ? `?subject_id=${subjectId}` : ''
  return get<Domain[]>(`/domains${query}`)
}

/**
 * Fetch clusters with optional filters
 */
export async function fetchClusters(filters?: HierarchyFilter): Promise<Cluster[]> {
  const params = new URLSearchParams()
  if (filters?.domain_id) params.append('domain_id', filters.domain_id.toString())
  if (filters?.subject_id) params.append('subject_id', filters.subject_id.toString())

  const query = params.toString() ? `?${params.toString()}` : ''
  return get<Cluster[]>(`/clusters${query}`)
}

/**
 * Fetch standards with optional filters
 */
export async function fetchStandards(
  filters?: HierarchyFilter & { min_difficulty?: number; max_difficulty?: number }
): Promise<Standard[]> {
  const params = new URLSearchParams()

  if (filters?.subject_id) params.append('subject_id', filters.subject_id.toString())
  if (filters?.grade_id) params.append('grade_id', filters.grade_id.toString())
  if (filters?.domain_id) params.append('domain_id', filters.domain_id.toString())
  if (filters?.cluster_id) params.append('cluster_id', filters.cluster_id.toString())
  if (filters?.min_difficulty !== undefined) params.append('min_difficulty', filters.min_difficulty.toString())
  if (filters?.max_difficulty !== undefined) params.append('max_difficulty', filters.max_difficulty.toString())

  const query = params.toString()
  return get<Standard[]>(`/standards${query ? `?${query}` : ''}`)
}

/**
 * Fetch a single standard by ID
 */
export async function fetchStandardById(id: number): Promise<Standard> {
  const standards = await fetchStandards()
  const standard = standards.find(s => s.id === id)
  if (!standard) throw new Error(`Standard with ID ${id} not found`)
  return standard
}

/**
 * Fetch grades by subject (alias for fetchGrades)
 */
export async function fetchGradesBySubject(subjectId: number): Promise<Grade[]> {
  return fetchGrades(subjectId)
}

/**
 * Fetch domains by grade
 * Note: Backend doesn't have grade filter for domains, so we fetch all domains for the subject
 * and filter client-side, or return all domains
 */
export async function fetchDomainsByGrade(gradeId: number): Promise<Domain[]> {
  // Since backend doesn't support grade filter, we fetch domains without filter
  // In a real app, you might want to add backend support for this
  return fetchDomains()
}
