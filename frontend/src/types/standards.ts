export interface Subject {
  id: number
  name: string
  code: string
}

export interface Grade {
  id: number
  subject_id: number
  level: number
  display_name: string
}

export interface Domain {
  id: number
  subject_id?: number
  code: string
  name: string
  description?: string
}

export interface Cluster {
  id: number
  domain_id: number
  code: string
  description: string
}

export interface Standard {
  id: number
  cluster_id: number
  grade_id: number
  domain_id: number
  code: string
  description: string
  difficulty_base: number
  keywords: string[]
  conceptual_category: string
  created_at: string
}

export interface HierarchyFilter {
  subject_id?: number
  grade_id?: number
  domain_id?: number
  cluster_id?: number
  domain_ids?: number[]
}
