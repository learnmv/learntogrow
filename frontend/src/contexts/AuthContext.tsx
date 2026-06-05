import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import type { ReactNode } from 'react'
import type { User, LoginCredentials, RegisterStudentData, RegisterParentData } from '../types/auth'
import * as authService from '../services/auth'

interface AuthContextValue {
  user: User | null
  token: string | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (credentials: LoginCredentials) => Promise<void>
  logout: () => void
  registerStudent: (data: RegisterStudentData) => Promise<void>
  registerParent: (data: RegisterParentData) => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setTokenState] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let cancelled = false

    async function initialize() {
      const storedToken = authService.getToken()

      if (!storedToken) {
        setIsLoading(false)
        return
      }

      try {
        setTokenState(storedToken)
        const currentUser = await authService.getCurrentUser()
        if (!cancelled) {
          setUser(currentUser)
        }
      } catch {
        authService.removeToken()
        setTokenState(null)
        setUser(null)
      } finally {
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    }

    initialize()

    return () => {
      cancelled = true
    }
  }, [])

  const login = useCallback(async (credentials: LoginCredentials) => {
    const response = await authService.login(credentials)
    setTokenState(response.access_token)
    const currentUser = await authService.getCurrentUser()
    setUser(currentUser)
  }, [])

  const logout = useCallback(() => {
    authService.logout()
    setTokenState(null)
    setUser(null)
  }, [])

  const registerStudent = useCallback(async (data: RegisterStudentData) => {
    await authService.registerStudent(data)
  }, [])

  const registerParent = useCallback(async (data: RegisterParentData) => {
    await authService.registerParent(data)
  }, [])

  const refreshUser = useCallback(async () => {
    const currentUser = await authService.getCurrentUser()
    setUser(currentUser)
  }, [])

  const value: AuthContextValue = {
    user,
    token,
    isLoading,
    isAuthenticated: !!user && !!token,
    login,
    logout,
    registerStudent,
    registerParent,
    refreshUser,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
