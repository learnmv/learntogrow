/**
 * Types for prompt template API
 */

export interface PromptResponse {
  id: number;
  name: string;
  content: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface PromptPlaceholder {
  placeholder: string;
  description: string;
  example: string;
}

export interface PromptPlaceholdersResponse {
  placeholders: PromptPlaceholder[];
}