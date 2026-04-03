import { useEffect, useRef, useState } from 'react'
import type { AppletConfig, AppletType } from '../types/questions'

// Global type declaration for GeoGebra
declare global {
  interface Window {
    GGBApplet: new (
      parameters: GGBAppletParameters,
      appletWidth?: number,
      appletHeight?: number
    ) => GGBAppletInstance
    ggbApplet?: GGBAppletInstance
  }
}

interface GGBAppletParameters {
  id?: string
  width?: number
  height?: number
  showToolBar?: boolean
  showAlgebraInput?: boolean
  showMenuBar?: boolean
  showResetIcon?: boolean
  enableLabelDrags?: boolean
  enableShiftDragZoom?: boolean
  enableRightClick?: boolean
  capturingThreshold?: number
  showAuthorInfo?: boolean
  borderColor?: string
  ggbBase64?: string
  appletOnLoad?: () => void
}

interface GGBAppletInstance {
  inject: (containerId: string) => void
  evalCommand: (command: string) => void
  evalCommandGetLabels: (command: string) => string
  setValue: (objName: string, value: number) => void
  getValue: (objName: string) => number
  setColor: (objName: string, r: number, g: number, b: number) => void
  setPointSize: (objName: string, size: number) => void
  setFixed: (objName: string, fixed: boolean, selection?: boolean) => void
  setCoordSystem: (
    xmin: number,
    xmax: number,
    ymin: number,
    ymax: number
  ) => void
  setAxesVisible: (xVisible: boolean, yVisible: boolean) => void
  setGridVisible: (visible: boolean) => void
  setVisible: (objName: string, visible: boolean) => void
  setLabelVisible: (objName: string, visible: boolean) => void
  setLayer: (objName: string, layer: number) => void
  setLineThickness: (objName: string, thickness: number) => void
  setLineStyle: (objName: string, style: number) => void
  getXML: () => string
  setXML: (xml: string) => void
  getBase64: () => string
  setBase64: (base64: string) => void
  reset: () => void
  newConstruction: () => void
}

interface GeoGebraAppletProps {
  commands: string[]
  appletType?: AppletType
  config?: AppletConfig
  onError?: (error: string) => void
}

export function GeoGebraApplet({
  commands,
  config,
  onError,
}: GeoGebraAppletProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const appletRef = useRef<GGBAppletInstance | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isReady, setIsReady] = useState(false)
  const appletId = useRef(`ggb-applet-${Math.random().toString(36).slice(2, 9)}`)

  useEffect(() => {
    // Check if GeoGebra is loaded
    if (!window.GGBApplet) {
      onError?.('GeoGebra library not loaded. Please refresh the page.')
      setIsLoading(false)
      return
    }

    if (!containerRef.current) return

    const parameters: GGBAppletParameters = {
      id: appletId.current,
      width: config?.width ?? 800,
      height: config?.height ?? 400,
      showToolBar: config?.showToolBar ?? false,
      showAlgebraInput: config?.showAlgebraInput ?? false,
      showMenuBar: config?.showMenuBar ?? false,
      showResetIcon: false,
      enableLabelDrags: false,
      enableShiftDragZoom: true,
      enableRightClick: false,
      capturingThreshold: 3,
      showAuthorInfo: false,
      borderColor: '#e5e7eb',
      appletOnLoad: () => {
        setIsReady(true)
        setIsLoading(false)
      },
    }

    // Create and inject the applet
    const applet = new window.GGBApplet(parameters, parameters.width, parameters.height)
    appletRef.current = applet

    // Inject into container
    try {
      applet.inject(containerRef.current.id)
    } catch (err) {
      onError?.(`Failed to inject GeoGebra applet: ${err}`)
      setIsLoading(false)
    }

    return () => {
      // Cleanup if needed
      appletRef.current = null
    }
  }, [config, onError])

  // Execute commands when applet is ready
  useEffect(() => {
    if (!isReady || !appletRef.current || commands.length === 0) return

    const applet = appletRef.current

    try {
      // Reset construction before executing new commands
      applet.newConstruction()

      // Execute each command
      for (const command of commands) {
        try {
          // Handle API methods vs eval commands
          if (command.startsWith('SetCoordSystem')) {
            const match = command.match(/SetCoordSystem\(([^)]+)\)/)
            if (match) {
              const coords = match[1].split(',').map((n) => parseFloat(n.trim()))
              if (coords.length >= 4) {
                applet.setCoordSystem(coords[0], coords[1], coords[2], coords[3])
              }
            }
          } else if (command.startsWith('SetAxesVisible')) {
            const match = command.match(/SetAxesVisible\(([^)]+)\)/)
            if (match) {
              const vals = match[1].split(',').map((v) => v.trim().toLowerCase() === 'true')
              applet.setAxesVisible(vals[0] ?? true, vals[1] ?? true)
            }
          } else if (command.startsWith('SetGridVisible')) {
            const match = command.match(/SetGridVisible\(([^)]+)\)/)
            if (match) {
              const visible = match[1].trim().toLowerCase() === 'true'
              applet.setGridVisible(visible)
            }
          } else if (command.startsWith('SetColor')) {
            const match = command.match(/SetColor\(([^)]+)\)/)
            if (match) {
              const params = match[1].split(',').map((p) => p.trim())
              const objName = params[0]
              const r = parseInt(params[1])
              const g = parseInt(params[2])
              const b = parseInt(params[3])
              if (objName && !isNaN(r) && !isNaN(g) && !isNaN(b)) {
                applet.setColor(objName, r, g, b)
              }
            }
          } else if (command.startsWith('SetPointSize')) {
            const match = command.match(/SetPointSize\(([^)]+)\)/)
            if (match) {
              const params = match[1].split(',').map((p) => p.trim())
              const objName = params[0]
              const size = parseInt(params[1])
              if (objName && !isNaN(size)) {
                applet.setPointSize(objName, size)
              }
            }
          } else if (command.startsWith('SetFixed')) {
            const match = command.match(/SetFixed\(([^)]+)\)/)
            if (match) {
              const params = match[1].split(',').map((p) => p.trim())
              const objName = params[0]
              const fixed = params[1].toLowerCase() === 'true'
              const selection = params[2] ? params[2].toLowerCase() === 'true' : undefined
              if (objName) {
                applet.setFixed(objName, fixed, selection)
              }
            }
          } else if (command.startsWith('SetVisible')) {
            const match = command.match(/SetVisible\(([^)]+)\)/)
            if (match) {
              const params = match[1].split(',').map((p) => p.trim())
              const objName = params[0]
              const visible = params[1].toLowerCase() === 'true'
              if (objName) {
                applet.setVisible(objName, visible)
              }
            }
          } else {
            // Standard evalCommand
            applet.evalCommand(command)
          }
        } catch (cmdErr) {
          console.warn(`Failed to execute command: ${command}`, cmdErr)
        }
      }
    } catch (err) {
      onError?.(`Error executing GeoGebra commands: ${err}`)
    }
  }, [isReady, commands, onError])

  return (
    <div className="w-full rounded-xl overflow-hidden border border-border bg-white">
      {isLoading && (
        <div className="flex items-center justify-center bg-surface-muted" style={{ height: config?.height ?? 400 }}>
          <div className="text-center">
            <div className="w-10 h-10 border-4 border-sage-200 border-t-sage-600 rounded-full animate-spin mx-auto mb-3" />
            <p className="text-text-muted font-display text-sm">Loading diagram...</p>
          </div>
        </div>
      )}
      <div
        ref={containerRef}
        id={appletId.current}
        className={`w-full ${isLoading ? 'hidden' : 'block'}`}
        style={{ minHeight: config?.height ?? 400 }}
      />
    </div>
  )
}
