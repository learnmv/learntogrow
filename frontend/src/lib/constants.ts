// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://10.0.0.131:30800/api/v1'

// App Configuration
export const APP_NAME = 'LearnToGrow'
export const APP_DESCRIPTION = 'AI-powered educational question generation'

// Default values
export const DEFAULT_QUESTION_TYPE = 'multiple_choice'
export const DEFAULT_DIFFICULTY = 0.5

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
