import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Eye, EyeOff, Loader2 } from 'lucide-react'
import { AuthFormLayout } from '../../components/auth/AuthFormLayout'
import { useAuth } from '../../contexts/AuthContext'

export function LoginPage() {
  const navigate = useNavigate()
  const { user, isAuthenticated, isLoading, login } = useAuth()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Redirect authenticated users to their role-appropriate page
  useEffect(() => {
    if (!isLoading && isAuthenticated && user) {
      const routes: Record<string, string> = { admin: '/admin', parent: '/parent', student: '/student' }
      navigate(routes[user.role], { replace: true })
    }
  }, [isLoading, isAuthenticated, user, navigate])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setIsSubmitting(true)
    setError(null)

    try {
      await login({ username, password })
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Invalid username or password'
      setError(message)
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-sage-600 animate-spin" />
      </div>
    )
  }

  return (
    <AuthFormLayout
      title="Welcome Back"
      subtitle="Sign in to continue learning"
      footer={
        <>
          Don't have an account?{' '}
          <Link to="/register/student" className="text-sage-600 hover:text-sage-700 font-medium">
            Register as Student
          </Link>
          {' | '}
          <Link to="/register/parent" className="text-sage-600 hover:text-sage-700 font-medium">
            Register as Parent
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="p-3 bg-coral-50 text-coral-700 rounded-lg text-sm">
            {error}
          </div>
        )}

        <div>
          <label htmlFor="username" className="block text-sm font-display font-medium text-text mb-1">
            Username
          </label>
          <input
            id="username"
            type="text"
            required
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Enter your username"
            className="w-full px-4 py-3 rounded-xl border border-border bg-surface focus:border-sage-500 focus:ring-2 focus:ring-sage-200 outline-none transition-colors font-body"
          />
        </div>

        <div>
          <label htmlFor="password" className="block text-sm font-display font-medium text-text mb-1">
            Password
          </label>
          <div className="relative">
            <input
              id="password"
              type={showPassword ? 'text' : 'password'}
              required
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              className="w-full px-4 py-3 rounded-xl border border-border bg-surface focus:border-sage-500 focus:ring-2 focus:ring-sage-200 outline-none transition-colors font-body pr-12"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text transition-colors"
              aria-label={showPassword ? 'Hide password' : 'Show password'}
            >
              {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
            </button>
          </div>
          <div className="mt-2 text-right">
            <Link
              to="/forgot-password"
              className="text-sm text-sage-600 hover:text-sage-700 font-medium"
            >
              Forgot Password?
            </Link>
          </div>
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full py-3 rounded-xl font-display font-semibold transition-colors bg-coral-500 text-white hover:bg-coral-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Signing In...
            </>
          ) : (
            'Sign In'
          )}
        </button>
      </form>
    </AuthFormLayout>
  )
}