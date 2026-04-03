import { useCallback, useEffect, useRef } from 'react'

/**
 * Hook to track timeouts and automatically clean them up
 * Prevents memory leaks by clearing timeouts on unmount
 */
export function useTrackedTimeouts() {
  const timeoutsRef = useRef<ReturnType<typeof setTimeout>[]>([])

  const addTimeout = useCallback((callback: () => void, ms: number): void => {
    const id = setTimeout(() => {
      // Remove from tracking array after execution
      const index = timeoutsRef.current.indexOf(id)
      if (index > -1) {
        timeoutsRef.current.splice(index, 1)
      }
      callback()
    }, ms)
    timeoutsRef.current.push(id)
  }, [])

  const clearAllTimeouts = useCallback(() => {
    timeoutsRef.current.forEach(id => clearTimeout(id))
    timeoutsRef.current = []
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => clearAllTimeouts()
  }, [clearAllTimeouts])

  return { addTimeout, clearAllTimeouts }
}
