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

let runtimeConfig: RuntimeConfig | null = null
let configError: Error | null = null
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
  // Return prior error without retrying indefinitely
  if (configError) {
    throw configError
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
    const config = await response.json()
    runtimeConfig = config
    return config
  } catch (error) {
    console.error('Failed to load runtime config:', error)
    configError = error instanceof Error ? error : new Error(String(error))
    throw configError
  }
}

/**
 * Get the current configuration.
 * Throws if config has not loaded successfully.
 */
export function getConfig(): RuntimeConfig {
  if (!runtimeConfig) {
    throw new Error('Runtime configuration not loaded. Ensure loadConfig() completed successfully.')
  }
  return runtimeConfig
}

// Convenience getters
export const getApiUrl = () => getConfig().apiUrl
export const getAppName = () => getConfig().appName
export const isDebugEnabled = () => getConfig().features.enableDebug
