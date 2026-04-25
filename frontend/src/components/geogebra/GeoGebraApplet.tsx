import { useEffect, useRef, useState, useMemo } from 'react'

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
  setSize: (width: number, height: number) => void
  /** Switches to a single- or multi-view layout, e.g. \"G\" = Graphics only. */
  setPerspective?: (perspective: string) => void
  /** Hides/shows the left sidebar (algebra, CAS, spreadsheet). */
  setVisible?: (view: string, visible: boolean) => void
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
  const [apiReady, setApiReady] = useState(false)

  // Stable container ID for the life of this component instance
  const containerIdRef = useRef(`ggb-${Math.random().toString(36).slice(2, 9)}`)
  const containerId = containerIdRef.current

  // Refs to the live applet and its API — survive re-renders
  const apiRef = useRef<GGBAppletApi | null>(null)
  const appletRef = useRef<GGBAppletInstance | null>(null)

  // Serialised config key to detect REAL config changes vs object-ref churn
  const configKey = useMemo(() => JSON.stringify(config), [config])

  // ── Effect 1: create / destroy the applet (structural props only) ──
  useEffect(() => {
    let isMounted = true
    let checkReady: ReturnType<typeof setInterval> | null = null
    let timeoutId: ReturnType<typeof setTimeout> | null = null

    async function init() {
      setIsLoading(true)
      setApiReady(false)
      setError(null)
      apiRef.current = null
      appletRef.current = null

      try {
        await loadGeoGebraScript()
        if (!isMounted || !containerRef.current || !window.GGBApplet) {
          if (isMounted) setError('GeoGebra unavailable. Check your internet connection.')
          setIsLoading(false)
          return
        }

        const parameters: Record<string, unknown> = {
          // Base type defaults first
          ...TYPE_DEFAULTS[appletType],
          // User config can tweak type defaults (e.g. showAxes, showGrid)
          ...config,
          // Structural props — CANNOT be overridden by LLM-generated config
          id: containerId,
          appName: appletType,
          width,
          height,
          // Quiz mode: force-disable all UI chrome so students can't
          // accidentally open toolbars, algebra panels, or menus.
          // These are set LAST so the LLM can never override them.
          showToolBar: false,
          showAlgebraInput: false,
          showAlgebraView: false,
          allowStyleBar: false,
          allowStyleChanges: false,
          showMenuBar: false,
          showResetIcon: false,
          enableRightClick: false,
          enableLabelDrags: false,
          enableShiftDragZoom: true,
        }

        const applet = new window.GGBApplet(parameters, true)
        appletRef.current = applet

        // Use the ref DOM node directly — safer than getElementById
        const el = containerRef.current
        if (el) el.innerHTML = ''
        applet.inject(containerId)

        // Poll until the API becomes available
        checkReady = setInterval(() => {
          if (!isMounted) { if (checkReady) clearInterval(checkReady); return }

          try {
            const a = applet.getAppletObject()
            if (a && typeof a.evalCommand === 'function') {
              if (checkReady) clearInterval(checkReady)
              apiRef.current = a
              if (isMounted) {
                setApiReady(true)
                setIsLoading(false)
              }
            }
          } catch {
            // still loading
          }
        }, 100)

        timeoutId = setTimeout(() => {
          if (checkReady) clearInterval(checkReady)
          if (isMounted && !apiRef.current) {
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

      // Use the ref for cleanup — always points to the exact DOM node we own
      const el = containerRef.current
      if (el) el.innerHTML = ''
      try { apiRef.current?.reset() } catch { /* ignore */ }
      apiRef.current = null
      appletRef.current = null
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [appletType, height, width, containerId, configKey])

  // ── Effect 2: execute commands whenever they change or API becomes ready ──
  useEffect(() => {
    if (!apiReady || !apiRef.current) return

    const api = apiRef.current

    // Clear canvas before every command batch
    api.reset()

    // Hide algebra / CAS / spreadsheet panels via setPerspective.
    // setVisible('algebra', ...) targets *objects* named 'algebra', not the view.
    // The correct JS API for switching views is setPerspective:
    //   'G' = 2D Graphics only    (hides algebra in graphing/geometry)
    //   'T' = 3D Graphics only      (hides algebra in 3D calculator)
    try {
      if (appletType === '3d') {
        api.setPerspective?.('T')
      } else {
        api.setPerspective?.('G')
      }
    } catch {
      // setPerspective may not exist in all applet versions
    }

    if (commands.length === 0) return

    const results: { command: string; success: boolean }[] = []
    const failedCommands: string[] = []

    commands.forEach((cmd) => {
      try {
        const ok = api.evalCommand(cmd)
        results.push({ command: cmd, success: !!ok })
        if (!ok) {
          failedCommands.push(cmd)
        }
      } catch (err) {
        console.warn('GeoGebra command failed:', cmd, err)
        results.push({ command: cmd, success: false })
        failedCommands.push(cmd)
      }
    })

    if (onCommandResults && results.length > 0) {
      onCommandResults(results)
    }

    // Surface silent command failures so students aren't staring at a blank grid
    if (failedCommands.length > 0 && failedCommands.length === commands.length) {
      setError(
        `All ${failedCommands.length} diagram command(s) failed to render. The question may still be solvable without the diagram.`
      )
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [apiReady, commands, onCommandResults])

  if (error) {
    return (
      <div className="relative rounded-xl border border-sage-200 overflow-hidden bg-white" style={{ width, height }}>
        <div
          className="h-full w-full rounded-xl border border-coral-200 bg-coral-50 p-4 text-center flex flex-col items-center justify-center gap-2"
        >
          <p className="text-coral-700 font-body text-sm font-medium">{error}</p>
          <p className="text-coral-600 font-body text-xs">
            If the problem persists, try refreshing the page.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="relative rounded-xl border border-sage-200 overflow-hidden bg-white" style={{ width, height }}>
      {isLoading && (
        <div
          className="absolute inset-0 flex items-center justify-center bg-sage-50/80 z-10"
        >
          <div className="text-center">
            <div className="w-8 h-8 border-3 border-sage-200 border-t-sage-600 rounded-full animate-spin mx-auto mb-2" />
            <p className="text-text-muted font-display text-sm">
              Loading {appletType === '3d' ? '3D calculator' : `${appletType} tool`}...
            </p>
          </div>
        </div>
      )}
      <div
        ref={containerRef}
        id={containerId}
        style={{ width: '100%', height: '100%' }}
      />
    </div>
  )
}
