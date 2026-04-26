import { getApiUrl } from '../lib/config'
import type { ApiError } from '../types/api'

/**
 * Generic fetch wrapper with error handling
 */
export async function fetchApi<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${getApiUrl()}${endpoint}`

  const { headers: optionHeaders, ...restOptions } = options ?? {}
  const config: RequestInit = {
    ...restOptions,
    headers: {
      'Content-Type': 'application/json',
      ...optionHeaders,
    },
  }

  const response = await fetch(url, config)

  if (!response.ok) {
    const error = await response.json().catch(() => ({})) as ApiError
    // FastAPI validation errors return detail as array of objects
    let detail: string
    if (Array.isArray(error.detail)) {
      detail = error.detail.map((e: any) => e.msg || String(e)).join('; ')
    } else if (typeof error.detail === 'string') {
      detail = error.detail
    } else {
      detail = `HTTP ${response.status}: ${response.statusText}`
    }
    throw new Error(detail)
  }

  // Handle 204 No Content gracefully
  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

/**
 * GET request helper
 */
export function get<T>(endpoint: string, options?: RequestInit): Promise<T> {
  return fetchApi<T>(endpoint, { ...options, method: 'GET' })
}

/**
 * POST request helper
 */
export function post<T>(
  endpoint: string,
  data?: unknown,
  options?: RequestInit
): Promise<T> {
  return fetchApi<T>(endpoint, {
    ...options,
    method: 'POST',
    body: data ? JSON.stringify(data) : undefined,
  })
}

/**
 * PATCH request helper
 */
export function patch<T>(
  endpoint: string,
  data: unknown,
  options?: RequestInit
): Promise<T> {
  return fetchApi<T>(endpoint, {
    ...options,
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

/**
 * DELETE request helper
 */
export function del<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  return fetchApi<T>(endpoint, {
    ...options,
    method: 'DELETE',
  })
}

/**
 * PUT request helper
 */
export function put<T>(
  endpoint: string,
  data: unknown,
  options?: RequestInit
): Promise<T> {
  return fetchApi<T>(endpoint, {
    ...options,
    method: 'PUT',
    body: JSON.stringify(data),
  })
}
