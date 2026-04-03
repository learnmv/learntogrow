import { useEffect, useRef, useState } from 'react'
import type { AppletType } from '../lib/geogebra-commands'
import type { AppletConfig } from '../types/questions'

interface GeoGebraAppletProps {
  /** GeoGebra applet type */
  appletType: AppletType
  /** Array of GeoGebra commands to execute */
  commands?: string[]
  /** Applet configuration options */
  config?: AppletConfig
  /** CSS class name for the container */
  className?: string
}

/** Script loading promise for deduplication */
let scriptLoadPromise: Promise<void> | null = null

/** Load GeoGebra deploy script with deduplication */
function loadGeoGebraScript(): Promise<void> {
  // Return existing promise if loading is in progress
  if (scriptLoadPromise) {
    return scriptLoadPromise
  }

  scriptLoadPromise = new Promise((resolve, reject) => {
    // Check if already loaded
    if (window.ggbApplet) {
      resolve()
      return
    }

    // Check if script element exists
    const existingScript = document.getElementById('geogebra-deployggb')
    if (existingScript) {
      existingScript.addEventListener('load', () => resolve())
      return
    }

    const script = document.createElement('script')
    script.id = 'geogebra-deployggb'
    script.src = 'https://www.geogebra.org/apps/deployggb.js'
    script.async = true
    script.onload = () => resolve()
    script.onerror = () => {
      scriptLoadPromise = null
      reject(new Error('Failed to load GeoGebra script'))
    }
    document.head.appendChild(script)
  })

  return scriptLoadPromise
}

/** Get GeoGebra app name based on applet type */
function getAppName(appletType: AppletType): string {
  const appNames: Record<AppletType, string> = {
    graphing: 'graphing',
    geometry: 'geometry',
    '3d': '3d',
    classic: 'classic',
    cas: 'cas',
    scientific: 'scientific',
  }
  return appNames[appletType] || 'graphing'
}

/** Create stable config key from config object */
function getConfigKey(config: AppletConfig): string {
  return `${config.width}-${config.height}-${config.showToolBar}-${config.showAlgebraInput}-${config.showMenuBar}-${config.showAlgebraView}`
}

export function GeoGebraApplet({
  appletType,
  commands = [],
  config = {},
  className = '',
}: GeoGebraAppletProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const appletRef = useRef<any>(null)
  const timeoutsRef = useRef<number[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isReady, setIsReady] = useState(false)

  // Stable config key for effect dependencies
  const configKey = getConfigKey(config)

  // Helper to track timeouts for cleanup
  const addTimeout = (id: number) => {
    timeoutsRef.current.push(id)
    return id
  }

  const clearAllTimeouts = () => {
    timeoutsRef.current.forEach(id => clearTimeout(id))
    timeoutsRef.current = []
  }

  // Load GeoGebra script and initialize applet
  useEffect(() => {
    let isMounted = true

    async function initApplet() {
      try {
        setIsLoading(true)
        setError(null)

        // Load the GeoGebra script
        await loadGeoGebraScript()

        if (!isMounted || !containerRef.current) return

        const appName = getAppName(appletType)
        const width = config.width || 800
        const height = config.height || 400

        // Create applet parameters
        const parameters = {
          appName,
          width,
          height,
          showToolBar: config.showToolBar ?? false,
          showAlgebraInput: config.showAlgebraInput ?? false,
          showMenuBar: config.showMenuBar ?? false,
          showAlgebraView: config.showAlgebraView ?? true, // Default to true for backward compatibility
          enableRightClick: false,
          enableShiftDragZoom: true,
          showResetIcon: false,
          language: 'en',
          borderColor: '#e2e8f0',
        }

        // Create the applet
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const ggb = (window as any).GGBApplet
        if (!ggb) {
          throw new Error('GeoGebra API not available')
        }

        const applet = new ggb(parameters, true)

        // Inject the applet into the container
        await new Promise<void>((resolve, reject) => {
          let resolved = false

          // Inject the applet
          applet.inject(containerRef.current, 'preferHTML5', () => {
            if (!resolved) {
              resolved = true
              resolve()
            }
          })

          // Poll for applet readiness as backup
          const checkApplet = () => {
            if (resolved) return
            // Check if applet is available on window
            const appletApi = (window as unknown as { ggbApplet?: { evalCommand?: () => void } }).ggbApplet
            if (appletApi?.evalCommand) {
              resolved = true
              resolve()
            } else {
              setTimeout(checkApplet, 500)
            }
          }

          // Start polling after a short delay
          setTimeout(checkApplet, 1000)

          // Timeout after 45 seconds
          setTimeout(() => {
            if (!resolved) {
              resolved = true
              reject(new Error('Applet injection timeout'))
            }
          }, 45000)
        })

        if (!isMounted) return

        // Wait for the applet to be fully available
        let retryCount = 0
        const maxRetries = 20
        const checkAppletReady = () => {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const api = (window as any).ggbApplet
          if (api && typeof api.evalCommand === 'function') {
            return api
          }
          return null
        }

        while (retryCount < maxRetries && !appletRef.current) {
          appletRef.current = checkAppletReady()
          if (!appletRef.current) {
            retryCount++
            // eslint-disable-next-line no-await-in-loop
            await new Promise(r => setTimeout(r, 500))
          }
        }

        if (!appletRef.current) {
          throw new Error('GeoGebra applet API not available after injection')
        }

        // Hide algebra view if configured (with delay to ensure applet is stable)
        if (config.showAlgebraView === false) {
          const api = appletRef.current
          // Use setPerspective to show only drawing view (no algebra view)
          addTimeout(window.setTimeout(() => {
            if (typeof api.setPerspective === 'function') {
              try {
                api.setPerspective('D')  // D = Drawing view only
              } catch (e) {
                console.warn('Failed to set perspective:', e)
              }
            }
          }, 1000))
        }

        setIsReady(true)
        setIsLoading(false)
      } catch (err) {
        if (!isMounted) return
        const errorMsg = err instanceof Error ? err.message : 'Failed to load GeoGebra applet'
        setError(errorMsg)
        setIsLoading(false)
      }
    }

    initApplet()

    return () => {
      isMounted = false
      clearAllTimeouts()
      // Cleanup applet on unmount
      if (appletRef.current && typeof appletRef.current.remove === 'function') {
        appletRef.current.remove()
      }
    }
  }, [appletType, configKey])

  // Execute commands when applet is ready or commands change
  useEffect(() => {
    if (!isReady || !appletRef.current || commands.length === 0) return

    const api = appletRef.current
    const shouldClearConstruction = config.showAlgebraView !== false

    // Execute commands with a delay to ensure applet is fully initialized
    // Especially after setPerspective which may reset the view
    const timer = window.setTimeout(() => {
      try {
        // Only clear construction if not showing clean view (setPerspective handles this)
        if (shouldClearConstruction && typeof api.newConstruction === 'function') {
          api.newConstruction()
        }

        // Execute each command
        for (const command of commands) {
          try {
            const cmd = command.trim()

            // Handle API methods (camelCase with parentheses)
            if (cmd.startsWith('set') || cmd.startsWith('Set')) {
              const match = cmd.match(/^([^(]+)\((.*)\)$/)
              if (match) {
                const methodName = match[1]
                const argsStr = match[2]

                // Parse arguments
                const args = argsStr.split(',').map(arg => {
                  const trimmed = arg.trim()
                  // Try to parse as number
                  if (!isNaN(Number(trimmed)) && trimmed !== '') {
                    return Number(trimmed)
                  }
                  // Parse as boolean
                  if (trimmed === 'true') return true
                  if (trimmed === 'false') return false
                  // Return as string (remove quotes if present)
                  return trimmed.replace(/^["']|["']$/g, '')
                })

                // Call the API method if it exists
                if (typeof api[methodName] === 'function') {
                  api[methodName](...args)
                  continue
                }
              }
            }

            // Otherwise use evalCommand for standard GeoGebra commands
            if (typeof api.evalCommand === 'function') {
              api.evalCommand(cmd)
            }
          } catch (cmdError) {
            console.warn('Failed to execute GeoGebra command:', command, cmdError)
          }
        }
      } catch (err) {
        console.error('Error executing GeoGebra commands:', err)
      }
    }, 500)

    return () => clearTimeout(timer)
  }, [isReady, commands, config.showAlgebraView])

  if (error) {
    return (
      <div className={`bg-red-50 border border-red-200 rounded-xl p-4 ${className}`}>
        <p className="text-red-600 text-sm">
          <span className="font-semibold">Diagram Error:</span> {error}
        </p>
        <p className="text-red-500 text-xs mt-2">
          Please check your internet connection and try again.
        </p>
      </div>
    )
  }

  return (
    <div className={`relative ${className}`}>
      {isLoading && (
        <div className="absolute inset-0 bg-slate-50 rounded-xl flex items-center justify-center">
          <div className="text-center">
            <div className="w-8 h-8 border-3 border-sage-200 border-t-sage-600 rounded-full animate-spin mx-auto mb-2" />
            <p className="text-text-muted text-sm">Loading diagram...</p>
          </div>
        </div>
      )}
      <div
        ref={containerRef}
        className="rounded-xl overflow-hidden border border-border"
        style={{
          minHeight: config.height || 400,
          maxWidth: '100%',
        }}
      />
    </div>
  )
}

// TypeScript declarations for GeoGebra global objects
declare global {
  interface Window {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    ggbApplet?: any
    GGBApplet?: new (
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      parameters: any,
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      javaCodebase?: any
    ) => {
      inject: (container: HTMLElement | null, type: string, callback?: () => void) => unknown
      getAppletNumber?: () => number
      remove?: () => void
    }
  }
}

export default GeoGebraApplet
