import { get } from './api'
import type { Subject, Grade, Domain, Cluster, Standard, HierarchyFilter } from '../types/standards'
import type { PaginatedResponse } from '../types/api'

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
 * Fetch standards with optional filters and pagination
 */
export async function fetchStandards(
  filters?: HierarchyFilter & { min_difficulty?: number; max_difficulty?: number },
  skip = 0,
  limit = 100
): Promise<PaginatedResponse<Standard>> {
  const params = new URLSearchParams()

  if (filters?.subject_id) params.append('subject_id', filters.subject_id.toString())
  if (filters?.grade_id) params.append('grade_id', filters.grade_id.toString())
  if (filters?.domain_id) params.append('domain_id', filters.domain_id.toString())
  if (filters?.cluster_id) params.append('cluster_id', filters.cluster_id.toString())
  if (filters?.min_difficulty !== undefined) params.append('min_difficulty', filters.min_difficulty.toString())
  if (filters?.max_difficulty !== undefined) params.append('max_difficulty', filters.max_difficulty.toString())

  params.append('skip', skip.toString())
  params.append('limit', limit.toString())

  return get<PaginatedResponse<Standard>>(`/standards?${params.toString()}`)
}

/**
 * Fetch a single standard by ID
 */
export async function fetchStandardById(id: number): Promise<Standard> {
  const response = await fetchStandards({ subject_id: id })
  const standard = response.items.find(s => s.id === id)
  if (!standard) throw new Error(`Standard with ID ${id} not found`)
  return standard
}
