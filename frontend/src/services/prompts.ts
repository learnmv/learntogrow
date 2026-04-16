import { get, put } from './api';
import { getAuthHeaders } from './auth';
import type { PromptResponse, PromptPlaceholdersResponse } from '../types/prompt';

/**
 * Get all prompt templates
 */
export async function getPrompts(): Promise<PromptResponse[]> {
  return get<PromptResponse[]>('/admin/prompts', { headers: getAuthHeaders() });
}

/**
 * Get a specific prompt template by name
 */
export async function getPrompt(name: string): Promise<PromptResponse> {
  return get<PromptResponse>(`/admin/prompts/${name}`, { headers: getAuthHeaders() });
}

/**
 * Update a prompt template
 */
export async function updatePrompt(
  name: string,
  content: string,
  description?: string
): Promise<PromptResponse> {
  return put<PromptResponse>(`/admin/prompts/${name}`, {
    content,
    description,
  }, { headers: getAuthHeaders() });
}

/**
 * Get available placeholders for prompt templates
 */
export async function getPromptPlaceholders(): Promise<PromptPlaceholdersResponse> {
  return get<PromptPlaceholdersResponse>('/admin/prompt-placeholders', { headers: getAuthHeaders() });
}