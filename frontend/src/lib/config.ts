// Runtime configuration loaded from server
export interface RuntimeConfig {
  apiUrl: string
  appName: string
  environment: string
  features: {
    enableDebug: boolean
    showDebugInfo: boolean
  }
  defaults: {
    questionType: string
    difficulty: number
  }
}

// Fallback config used when fetch fails or before load
const FALLBACK_CONFIG: RuntimeConfig = {
  apiUrl: 'http://10.0.0.131:30800/api/v1',
  appName: 'LearnToGrow',
  environment: 'production',
  features: {
    enableDebug: false,
    showDebugInfo: false
  },
  defaults: {
    questionType: 'multiple_choice',
    difficulty: 0.5
  }
}

let runtimeConfig: RuntimeConfig | null = null
let configPromise: Promise<RuntimeConfig> | null = null

/**
 * Load configuration from server.
 * Deduplicates concurrent calls to prevent duplicate requests.
 */
export async function loadConfig(): Promise<RuntimeConfig> {
  // Return cached config if already loaded
  if (runtimeConfig) {
    return runtimeConfig
  }

  // Deduplicate concurrent calls
  if (!configPromise) {
    configPromise = fetchConfig()
  }

  return configPromise
}

async function fetchConfig(): Promise<RuntimeConfig> {
  try {
    const response = await fetch('/config.json')
    if (!response.ok) {
      throw new Error(`Failed to load config: ${response.status}`)
    }
    runtimeConfig = await response.json()
    return runtimeConfig
  } catch (error) {
    console.error('Failed to load runtime config:', error)
    // Use fallback on error
    runtimeConfig = FALLBACK_CONFIG
    return runtimeConfig
  }
}

/**
 * Get the current configuration.
 * Returns fallback config if loadConfig() hasn't been called yet.
 */
export function getConfig(): RuntimeConfig {
  return runtimeConfig ?? FALLBACK_CONFIG
}

// Convenience getters
export const getApiUrl = () => getConfig().apiUrl
export const getAppName = () => getConfig().appName
export const isDebugEnabled = () => getConfig().features.enableDebug
