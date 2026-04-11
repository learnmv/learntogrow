import { useEffect, useRef, useState, useCallback } from 'react'
import { APPLET_TYPE_NAMES, type AppletType } from '../lib/geogebra-commands'
import { delay } from '../lib/utils'
import { useTrackedTimeouts } from '../hooks/useTrackedTimeouts'
import type { AppletConfig } from '../types/questions'

// Constants for timeouts and delays
const POLL_INTERVAL_MS = 500
const INITIAL_POLL_DELAY_MS = 1000
const INJECTION_TIMEOUT_MS = 45000
const MAX_RETRIES = 20
const PERSPECTIVE_DELAY_MS = 1000
const COMMAND_EXECUTION_DELAY_MS = 500

interface GeoGebraAppletProps {
  /** GeoGebra applet type */
  appletType: AppletType
  /** Array of GeoGebra commands to execute */
  commands?: string[]
  /** Applet configuration options */
  config?: AppletConfig
  /** CSS class name for the container */
  className?: string
  /** Callback when applet fails to load */
  onError?: (error: Error) => void
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
      // Check if script already loaded successfully
      if ((existingScript as HTMLScriptElement).dataset.loaded === 'true') {
        resolve()
        return
      }
      // Wait for load event
      existingScript.addEventListener('load', () => resolve())
      existingScript.addEventListener('error', () => {
        scriptLoadPromise = null
        reject(new Error('Failed to load GeoGebra script'))
      })
      return
    }

    const script = document.createElement('script')
    script.id = 'geogebra-deployggb'
    script.src = 'https://www.geogebra.org/apps/deployggb.js'
    script.async = true
    script.onload = () => {
      script.dataset.loaded = 'true'
      resolve()
    }
    script.onerror = () => {
      scriptLoadPromise = null
      reject(new Error('Failed to load GeoGebra script'))
    }
    document.head.appendChild(script)
  })

  return scriptLoadPromise
}

/** Parse command string to extract method name and arguments */
function parseCommandArgs(command: string): { methodName: string; args: unknown[] } | null {
  const trimmed = command.trim()

  // Handle API methods (camelCase or PascalCase with parentheses)
  if (trimmed.startsWith('set') || trimmed.startsWith('Set')) {
    const match = trimmed.match(/^([^(]+)\((.*)\)$/)
    if (match) {
      let methodName = match[1]
      const argsStr = match[2]

      // Normalize to camelCase (GeoGebra API uses camelCase)
      // Convert SetCoordSystem -> setCoordSystem
      if (methodName.startsWith('Set') && methodName.length > 3) {
        methodName = methodName[0].toLowerCase() + methodName.slice(1)
      }

      // Parse arguments
      const args = argsStr.split(',').map(arg => {
        const argTrimmed = arg.trim()
        // Try to parse as number
        if (!isNaN(Number(argTrimmed)) && argTrimmed !== '') {
          return Number(argTrimmed)
        }
        // Parse as boolean
        if (argTrimmed === 'true') return true
        if (argTrimmed === 'false') return false
        // Return as string (remove quotes if present)
        return argTrimmed.replace(/^["']|["']$/g, '')
      })

      return { methodName, args }
    }
  }

  return null
}

export function GeoGebraApplet({
  appletType,
  commands = [],
  config = {},
  className = '',
  onError,
}: GeoGebraAppletProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const appletRef = useRef<any>(null)
  const { addTimeout, clearAllTimeouts } = useTrackedTimeouts()
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  // Memoize config values to avoid unnecessary re-renders
  const {
    width = 800,
    height = 400,
    showToolBar = false,
    showAlgebraInput = false,
    showMenuBar = false,
    showAlgebraView = true,
  } = config

  const handleError = useCallback((err: Error) => {
    setStatus('error')
    setErrorMessage(err.message)
    onError?.(err)
  }, [onError])

  // Load GeoGebra script and initialize applet
  useEffect(() => {
    let isMounted = true

    async function initApplet() {
      try {
        setStatus('loading')
        setErrorMessage(null)

        // Load the GeoGebra script
        await loadGeoGebraScript()

        if (!isMounted || !containerRef.current) return

        const appName = APPLET_TYPE_NAMES[appletType] || 'graphing'

        // Create applet parameters
        const parameters = {
          appName,
          width,
          height,
          showToolBar,
          showAlgebraInput,
          showMenuBar,
          showAlgebraView,
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
          const checkApplet = async () => {
            if (resolved) return
            // Check if applet is available on window
            const appletApi = (window as unknown as { ggbApplet?: { evalCommand?: () => void } }).ggbApplet
            if (appletApi?.evalCommand) {
              resolved = true
              resolve()
            } else {
              await delay(POLL_INTERVAL_MS)
              if (!resolved) checkApplet()
            }
          }

          // Start polling after a short delay
          addTimeout(() => checkApplet(), INITIAL_POLL_DELAY_MS)

          // Timeout after specified duration
          addTimeout(() => {
            if (!resolved) {
              resolved = true
              reject(new Error('Applet injection timeout'))
            }
          }, INJECTION_TIMEOUT_MS)
        })

        if (!isMounted) return

        // Wait for the applet to be fully available using polling
        let retryCount = 0
        while (retryCount < MAX_RETRIES && !appletRef.current) {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const api = (window as any).ggbApplet
          if (api && typeof api.evalCommand === 'function') {
            appletRef.current = api
          } else {
            retryCount++
            await delay(POLL_INTERVAL_MS)
          }
        }

        if (!appletRef.current) {
          throw new Error('GeoGebra applet API not available after injection')
        }

        // Hide algebra view if configured (with delay to ensure applet is stable)
        if (showAlgebraView === false) {
          const api = appletRef.current
          addTimeout(() => {
            if (typeof api.setPerspective === 'function') {
              try {
                api.setPerspective('D') // D = Drawing view only
              } catch (e) {
                console.warn('Failed to set perspective:', e)
              }
            }
          }, PERSPECTIVE_DELAY_MS)
        }

        if (isMounted) {
          setStatus('ready')
        }
      } catch (err) {
        if (isMounted) {
          handleError(err instanceof Error ? err : new Error('Failed to load GeoGebra applet'))
        }
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
  }, [appletType, width, height, showToolBar, showAlgebraInput, showMenuBar, showAlgebraView, addTimeout, clearAllTimeouts, handleError])

  // Execute commands when applet is ready or commands change
  useEffect(() => {
    if (status !== 'ready' || !appletRef.current || commands.length === 0) return

    const api = appletRef.current
    const shouldClearConstruction = showAlgebraView !== false

    // Execute commands with a delay to ensure applet is fully initialized
    addTimeout(() => {
      try {
        // Only clear construction if not showing clean view (setPerspective handles this)
        if (shouldClearConstruction && typeof api.newConstruction === 'function') {
          api.newConstruction()
        }

        // Execute each command
        for (const command of commands) {
          try {
            const parsed = parseCommandArgs(command)

            if (parsed && typeof api[parsed.methodName] === 'function') {
              api[parsed.methodName](...parsed.args)
            } else if (typeof api.evalCommand === 'function') {
              api.evalCommand(command.trim())
            }
          } catch (cmdError) {
            console.warn('Failed to execute GeoGebra command:', command, cmdError)
          }
        }
      } catch (err) {
        console.error('Error executing GeoGebra commands:', err)
      }
    }, COMMAND_EXECUTION_DELAY_MS)
  }, [status, commands, showAlgebraView, addTimeout])

  if (status === 'error') {
    return (
      <div className={`bg-red-50 border border-red-200 rounded-xl p-4 ${className}`}>
        <p className="text-red-600 text-sm">
          <span className="font-semibold">Diagram Error:</span> {errorMessage}
        </p>
        <p className="text-red-500 text-xs mt-2">
          Please check your internet connection and try again.
        </p>
      </div>
    )
  }

  return (
    <div className={`relative ${className}`}>
      {status === 'loading' && (
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
          minHeight: height,
          maxWidth: '100%',
        }}
      />
    </div>
  )
}

export default GeoGebraApplet
