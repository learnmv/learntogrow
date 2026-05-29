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
  if (filters?.grade_id) params.append('grade_id', filters.grade_id.toString())

  const query = params.toString() ? `?${params.toString()}` : ''
  return get<Cluster[]>(`/clusters${query}`)
}

/**
 * Fetch standards with optional filters
 */
export async function fetchStandards(
  filters?: HierarchyFilter & { min_difficulty?: number; max_difficulty?: number }
): Promise<Standard[]> {
  // Backend only supports a single domain_id query param, so when multiple
  // domains are selected we fetch in parallel and merge the results.
  if (filters?.domain_ids && filters.domain_ids.length > 0) {
    const { domain_ids, ...rest } = filters
    const results = await Promise.all(
      domain_ids.map(domainId => fetchStandards({ ...rest, domain_id: domainId }))
    )
    const seen = new Set<number>()
    const merged: Standard[] = []
    results.forEach(list => {
      list.forEach(s => {
        if (!seen.has(s.id)) {
          seen.add(s.id)
          merged.push(s)
        }
      })
    })
    return merged
  }

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
 * Fetch grades by subject (alias for fetchGrades)
 */
export async function fetchGradesBySubject(subjectId: number): Promise<Grade[]> {
  return fetchGrades(subjectId)
}

export async function fetchDomainsBySubject(subjectId: number): Promise<Domain[]> {
  return fetchDomains(subjectId)
}
