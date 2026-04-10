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

export {}
