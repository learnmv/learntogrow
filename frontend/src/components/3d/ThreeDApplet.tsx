import { useEffect, useRef, useState } from 'react'

interface ThreeDAppletProps {
  /** GeoGebra commands to execute after applet loads */
  commands?: string[]
  /** Custom applet configuration */
  config?: Record<string, unknown>
  /** Height of the applet container */
  height?: number
  /** Width of the applet container */
  width?: number
}

// Global script loading state
let scriptLoadingPromise: Promise<void> | null = null

/**
 * Load the GeoGebra deployggb.js script dynamically.
 * Returns a promise that resolves when the script is loaded.
 */
function loadGeoGebraScript(): Promise<void> {
  if (typeof window === 'undefined') {
    return Promise.resolve()
  }

  // If script already exists, resolve immediately
  if (document.getElementById('geogebra-script')) {
    // Check if GGBApplet is available
    if (window.GGBApplet) {
      return Promise.resolve()
    }
    // Script tag exists but may not have loaded yet, wait a bit
    return new Promise((resolve) => {
      const checkInterval = setInterval(() => {
        if (window.GGBApplet) {
          clearInterval(checkInterval)
          resolve()
        }
      }, 100)
      // Timeout after 10 seconds
      setTimeout(() => {
        clearInterval(checkInterval)
        resolve()
      }, 10000)
    })
  }

  // If already loading, return the same promise
  if (scriptLoadingPromise) {
    return scriptLoadingPromise
  }

  // Create new script loading promise
  scriptLoadingPromise = new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.id = 'geogebra-script'
    script.src = 'https://www.geogebra.org/apps/deployggb.js'
    script.async = true
    script.onload = () => {
      // Wait for GGBApplet to be available
      const checkInterval = setInterval(() => {
        if (window.GGBApplet) {
          clearInterval(checkInterval)
          resolve()
        }
      }, 100)
      // Timeout after 10 seconds
      setTimeout(() => {
        clearInterval(checkInterval)
        resolve()
      }, 10000)
    }
    script.onerror = () => {
      scriptLoadingPromise = null
      reject(new Error('Failed to load GeoGebra script'))
    }
    document.head.appendChild(script)
  })

  return scriptLoadingPromise
}

// GeoGebra API interface (available after applet is ready)
interface GGBAppletApi {
  evalCommand: (command: string) => boolean
  evalCommandGetLabels: (command: string) => string | null
  setValue: (objName: string, value: number) => void
  getValue: (objName: string) => number
  getObjectType: (objName: string) => string
  reset: () => void
}

// GeoGebra applet instance returned by new GGBApplet()
interface GGBAppletInstance {
  inject: (containerId: string, type?: string) => void
  getAppletObject: () => GGBAppletApi | null
}

// Extend Window interface to include GeoGebra types
declare global {
  interface Window {
    GGBApplet?: new (
      parameters: Record<string, unknown>,
      view5d?: boolean
    ) => GGBAppletInstance
  }
}

export function ThreeDApplet({
  commands = [],
  config = {},
  height = 400,
  width = 600,
}: ThreeDAppletProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const containerIdRef = useRef<string>(`ggb-3d-${Math.random().toString(36).substring(2, 9)}`)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let isMounted = true
    let appletApi: GGBAppletApi | null = null
    let checkReadyInterval: ReturnType<typeof setInterval> | null = null
    let timeoutId: ReturnType<typeof setTimeout> | null = null

    async function initApplet() {
      try {
        // Load GeoGebra script
        await loadGeoGebraScript()

        if (!isMounted || !containerRef.current || !window.GGBApplet) {
          if (isMounted) {
            setError('GeoGebra is not available. Please check your internet connection.')
            setIsLoading(false)
          }
          return
        }

        const containerId = containerIdRef.current
        containerRef.current.id = containerId

        // Default parameters for 3D applet
        const parameters: Record<string, unknown> = {
          id: containerId,
          appName: '3d',
          width,
          height,
          showToolBar: false,
          showAlgebraInput: false,
          showMenuBar: false,
          showResetIcon: false,
          enableLabelDrags: false,
          enableShiftDragZoom: true,
          enableRightClick: false,
          capturingThreshold: null,
          // 3D-specific settings
          enable3D: true,
          showPlane: true,
          showAxisX: true,
          showAxisY: true,
          showAxisZ: true,
          ...config,
        }

        // Create applet instance
        const applet = new window.GGBApplet(parameters, true)

        // Inject applet into container
        applet.inject(containerId)

        // Poll for the API to become available (it's available after injection)
        checkReadyInterval = setInterval(() => {
          if (!isMounted) {
            if (checkReadyInterval) clearInterval(checkReadyInterval)
            return
          }

          try {
            const api = applet.getAppletObject()
            if (api && typeof api.evalCommand === 'function') {
              if (checkReadyInterval) clearInterval(checkReadyInterval)
              appletApi = api

              // Execute commands now that API is ready
              if (commands.length > 0) {
                commands.forEach((command) => {
                  try {
                    api.evalCommand(command)
                  } catch (err) {
                    console.warn('Failed to execute GeoGebra 3D command:', command, err)
                  }
                })
              }

              if (isMounted) {
                setIsLoading(false)
              }
            }
          } catch (e) {
            // API not ready yet, continue polling
          }
        }, 100)

        // Timeout after 15 seconds
        timeoutId = setTimeout(() => {
          if (checkReadyInterval) clearInterval(checkReadyInterval)
          if (isMounted && !appletApi) {
            setError('3D applet failed to initialize. Please refresh the page.')
            setIsLoading(false)
          }
        }, 15000)
      } catch (err) {
        console.error('Failed to initialize GeoGebra 3D applet:', err)
        if (isMounted) {
          setError('Failed to load 3D calculator. Please check your internet connection.')
          setIsLoading(false)
        }
      }
    }

    initApplet()

    // Cleanup function
    return () => {
      isMounted = false
      if (checkReadyInterval) clearInterval(checkReadyInterval)
      if (timeoutId) clearTimeout(timeoutId)
      // Clean up the applet container
      const container = document.getElementById(containerIdRef.current)
      if (container) {
        container.innerHTML = ''
      }
    }
  }, [commands, config, height, width])

  if (error) {
    return (
      <div
        className="rounded-xl border border-coral-200 bg-coral-50 p-4 text-center"
        style={{ height, width: '100%' }}
      >
        <p className="text-coral-700 font-body text-sm">{error}</p>
      </div>
    )
  }

  return (
    <div className="relative rounded-xl border border-sage-200 overflow-hidden bg-white">
      {isLoading && (
        <div
          className="absolute inset-0 flex items-center justify-center bg-sage-50/80 z-10"
          style={{ height }}
        >
          <div className="text-center">
            <div className="w-8 h-8 border-3 border-sage-200 border-t-sage-600 rounded-full animate-spin mx-auto mb-2" />
            <p className="text-text-muted font-display text-sm">Loading 3D calculator...</p>
          </div>
        </div>
      )}
      <div
        ref={containerRef}
        style={{ height, width: '100%', minWidth: width }}
        className="flex items-center justify-center"
      />
    </div>
  )
}
