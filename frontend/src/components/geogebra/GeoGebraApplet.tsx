import { useEffect, useRef, useState } from 'react'

export type GeoGebraAppletType = 'graphing' | 'geometry' | '3d' | 'classic'

interface GeoGebraAppletProps {
  appletType: GeoGebraAppletType
  commands?: string[]
  config?: Record<string, unknown>
  height?: number
  width?: number
  onCommandResults?: (results: { command: string; success: boolean }[]) => void
}

// ── Global script loading ──────────────────────────────────────────

let scriptLoadingPromise: Promise<void> | null = null

function loadGeoGebraScript(): Promise<void> {
  if (typeof window === 'undefined') return Promise.resolve()

  if (window.GGBApplet) return Promise.resolve()

  if (document.getElementById('geogebra-script')) {
    return new Promise((resolve) => {
      const check = setInterval(() => {
        if (window.GGBApplet) {
          clearInterval(check)
          resolve()
        }
      }, 100)
      setTimeout(() => { clearInterval(check); resolve() }, 10000)
    })
  }

  if (scriptLoadingPromise) return scriptLoadingPromise

  scriptLoadingPromise = new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.id = 'geogebra-script'
    script.src = 'https://www.geogebra.org/apps/deployggb.js'
    script.async = true
    script.onload = () => {
      const check = setInterval(() => {
        if (window.GGBApplet) { clearInterval(check); resolve() }
      }, 100)
      setTimeout(() => { clearInterval(check); resolve() }, 10000)
    }
    script.onerror = () => { scriptLoadingPromise = null; reject(new Error('Failed to load GeoGebra')) }
    document.head.appendChild(script)
  })

  return scriptLoadingPromise
}

// ── GeoGebra types ─────────────────────────────────────────────────

interface GGBAppletApi {
  evalCommand: (command: string) => boolean
  reset: () => void
}

interface GGBAppletInstance {
  inject: (containerId: string) => void
  getAppletObject: () => GGBAppletApi | null
}

declare global {
  interface Window {
    GGBApplet?: new (parameters: Record<string, unknown>, view5d?: boolean) => GGBAppletInstance
  }
}

// ── Per-type defaults ───────────────────────────────────────────────

const TYPE_DEFAULTS: Record<GeoGebraAppletType, Record<string, unknown>> = {
  graphing: {
    showAxes: true,
    showGrid: true,
    enableLabelDrags: false,
    enableShiftDragZoom: true,
    enableRightClick: false,
  },
  geometry: {
    showAxes: false,
    showGrid: true,
    enableLabelDrags: true,
    enableShiftDragZoom: true,
    enableRightClick: false,
  },
  classic: {
    showAxes: true,
    showGrid: true,
    enableLabelDrags: true,
    enableShiftDragZoom: true,
    enableRightClick: true,
    showToolBar: true,
    showAlgebraInput: true,
    showMenuBar: true,
    showResetIcon: true,
  },
  '3d': {
    enable3D: true,
    showPlane: true,
    showAxisX: true,
    showAxisY: true,
    showAxisZ: true,
    enableLabelDrags: false,
    enableShiftDragZoom: true,
    enableRightClick: false,
  },
}

// ── Component ──────────────────────────────────────────────────────

export function GeoGebraApplet({
  appletType,
  commands = [],
  config = {},
  height = 400,
  width = 600,
  onCommandResults,
}: GeoGebraAppletProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Stable ID so StrictMode doesn't create duplicate containers
  const stableIdRef = useRef(`ggb-${appletType}-${Math.random().toString(36).slice(2, 9)}`)
  const containerId = stableIdRef.current

  // Track which commands have been sent to the current applet instance
  const executedCommandsRef = useRef<Set<string>>(new Set())
  // Hold the applet instance so we can reuse it when only commands change
  const appletInstanceRef = useRef<GGBAppletInstance | null>(null)
  const apiRef = useRef<GGBAppletApi | null>(null)

  useEffect(() => {
    let isMounted = true
    let api: GGBAppletApi | null = null
    let checkReady: ReturnType<typeof setInterval> | null = null
    let timeoutId: ReturnType<typeof setTimeout> | null = null

    async function init() {
      executedCommandsRef.current.clear()
      setIsLoading(true)
      setError(null)

      try {
        await loadGeoGebraScript()
        if (!isMounted || !containerRef.current || !window.GGBApplet) {
          if (isMounted) setError('GeoGebra unavailable. Check your internet connection.')
          setIsLoading(false)
          return
        }

        const parameters: Record<string, unknown> = {
          id: containerId,
          appName: appletType,
          width,
          height,
          showToolBar: false,
          showAlgebraInput: false,
          showMenuBar: false,
          showResetIcon: false,
          ...TYPE_DEFAULTS[appletType],
          ...config,
        }

        const applet = new window.GGBApplet(parameters, true)
        appletInstanceRef.current = applet

        const el = document.getElementById(containerId)
        if (el) el.innerHTML = ''
        applet.inject(containerId)

        checkReady = setInterval(() => {
          if (!isMounted) { if (checkReady) clearInterval(checkReady); return }

          try {
            const a = applet.getAppletObject()
            if (a && typeof a.evalCommand === 'function') {
              if (checkReady) clearInterval(checkReady)
              api = a
              apiRef.current = a

              if (commands.length > 0) {
                const newCommands = commands.filter((c) => !executedCommandsRef.current.has(c))
                if (newCommands.length > 0) {
                  const results: { command: string; success: boolean }[] = []
                  newCommands.forEach((cmd) => {
                    try {
                      const ok = a.evalCommand(cmd)
                      results.push({ command: cmd, success: !!ok })
                      executedCommandsRef.current.add(cmd)
                    } catch (err) {
                      console.warn('GeoGebra command failed:', cmd, err)
                      results.push({ command: cmd, success: false })
                      executedCommandsRef.current.add(cmd)
                    }
                  })
                  if (onCommandResults && results.length > 0) onCommandResults(results)
                }
              }

              if (isMounted) setIsLoading(false)
            }
          } catch {
            // API not ready yet, keep polling
          }
        }, 100)

        timeoutId = setTimeout(() => {
          if (checkReady) clearInterval(checkReady)
          if (isMounted && !api) {
            setError(`GeoGebra ${appletType} applet failed to initialize. Please refresh.`)
            setIsLoading(false)
          }
        }, 15000)
      } catch (err) {
        if (isMounted) {
          setError('Failed to load GeoGebra applet.')
          setIsLoading(false)
        }
      }
    }

    init()

    return () => {
      isMounted = false
      if (checkReady) clearInterval(checkReady)
      if (timeoutId) clearTimeout(timeoutId)

      // Best-effort cleanup: remove injected DOM and attempt reset
      const el = document.getElementById(containerId)
      if (el) el.innerHTML = ''
      try {
        apiRef.current?.reset()
      } catch {
        // ignore
      }
      apiRef.current = null
      appletInstanceRef.current = null
    }
  }, [appletType, height, width, containerId, config, commands, onCommandResults])

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
            <p className="text-text-muted font-display text-sm">Loading {appletType === '3d' ? '3D calculator' : `${appletType} tool`}...</p>
          </div>
        </div>
      )}
      <div
        ref={containerRef}
        id={containerId}
        style={{ height, width: '100%', minWidth: width }}
        className="flex items-center justify-center"
      />
    </div>
  )
}
