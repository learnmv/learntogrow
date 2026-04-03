// Re-export config functions for backward compatibility
export { getApiUrl, getAppName, getConfig, isDebugEnabled } from './config'
export type { RuntimeConfig } from './config'

// App Configuration
export const APP_DESCRIPTION = 'AI-powered educational question generation'

// Question types
export const QUESTION_TYPES = [
  { value: 'multiple_choice', label: 'Multiple Choice' },
  { value: 'open_ended', label: 'Open Ended' },
] as const

// Animation durations
export const ANIMATION = {
  fast: 0.2,
  normal: 0.3,
  slow: 0.5,
} as const
