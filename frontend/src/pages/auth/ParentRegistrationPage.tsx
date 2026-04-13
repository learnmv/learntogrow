import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Eye, EyeOff, Loader2 } from 'lucide-react'
import { AuthFormLayout } from '../../components/auth/AuthFormLayout'
import { useAuth } from '../../contexts/AuthContext'

export function ParentRegistrationPage() {
  const navigate = useNavigate()
  const { user, isAuthenticated, isLoading, registerParent, login } = useAuth()

  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [studentEmailOrUsername, setStudentEmailOrUsername] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!isLoading && isAuthenticated && user) {
      const routes: Record<string, string> = { admin: '/admin', parent: '/parent', student: '/student' }
      navigate(routes[user.role], { replace: true })
    }
  }, [isLoading, isAuthenticated, user, navigate])

  function validateForm(): string | null {
    if (!username.trim()) return 'Username is required'
    if (!email.trim()) return 'Email is required'
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return 'Please enter a valid email address'
    if (!password) return 'Password is required'
    if (password.length < 8) return 'Password must be at least 8 characters'
    if (password !== confirmPassword) return 'Passwords do not match'
    if (!studentEmailOrUsername.trim()) return 'Student username or email is required'
    return null
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()

    const validationError = validateForm()
    if (validationError) {
      setError(validationError)
      return
    }

    setIsSubmitting(true)
    setError(null)

    try {
      await registerParent({
        username: username.trim(),
        email: email.trim(),
        password,
        full_name: fullName.trim() || undefined,
        student_email_or_username: studentEmailOrUsername.trim(),
      })
      await login({ username: username.trim(), password })
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Registration failed. Please try again.'
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
      title="Create Parent Account"
      subtitle="Connect with your child's learning"
      footer={
        <>
          Already have an account?{' '}
          <Link to="/login" className="text-sage-600 hover:text-sage-700 font-medium">
            Sign In
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
            Username <span className="text-coral-500">*</span>
          </label>
          <input
            id="username"
            type="text"
            required
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Choose a username"
            className="w-full px-4 py-3 rounded-xl border border-border bg-surface focus:border-sage-500 focus:ring-2 focus:ring-sage-200 outline-none transition-colors font-body"
          />
        </div>

        <div>
          <label htmlFor="email" className="block text-sm font-display font-medium text-text mb-1">
            Email <span className="text-coral-500">*</span>
          </label>
          <input
            id="email"
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            className="w-full px-4 py-3 rounded-xl border border-border bg-surface focus:border-sage-500 focus:ring-2 focus:ring-sage-200 outline-none transition-colors font-body"
          />
        </div>

        <div>
          <label htmlFor="password" className="block text-sm font-display font-medium text-text mb-1">
            Password <span className="text-coral-500">*</span>
          </label>
          <div className="relative">
            <input
              id="password"
              type={showPassword ? 'text' : 'password'}
              required
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="At least 8 characters"
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
        </div>

        <div>
          <label htmlFor="confirmPassword" className="block text-sm font-display font-medium text-text mb-1">
            Confirm Password <span className="text-coral-500">*</span>
          </label>
          <div className="relative">
            <input
              id="confirmPassword"
              type={showConfirmPassword ? 'text' : 'password'}
              required
              autoComplete="new-password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Re-enter your password"
              className="w-full px-4 py-3 rounded-xl border border-border bg-surface focus:border-sage-500 focus:ring-2 focus:ring-sage-200 outline-none transition-colors font-body pr-12"
            />
            <button
              type="button"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text transition-colors"
              aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
            >
              {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
            </button>
          </div>
        </div>

        <div>
          <label htmlFor="fullName" className="block text-sm font-display font-medium text-text mb-1">
            Full Name
          </label>
          <input
            id="fullName"
            type="text"
            autoComplete="name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="Your full name (optional)"
            className="w-full px-4 py-3 rounded-xl border border-border bg-surface focus:border-sage-500 focus:ring-2 focus:ring-sage-200 outline-none transition-colors font-body"
          />
        </div>

        <div>
          <label htmlFor="studentEmailOrUsername" className="block text-sm font-display font-medium text-text mb-1">
            Child's Username or Email <span className="text-coral-500">*</span>
          </label>
          <input
            id="studentEmailOrUsername"
            type="text"
            required
            value={studentEmailOrUsername}
            onChange={(e) => setStudentEmailOrUsername(e.target.value)}
            placeholder="Enter your child's username or email"
            className="w-full px-4 py-3 rounded-xl border border-border bg-surface focus:border-sage-500 focus:ring-2 focus:ring-sage-200 outline-none transition-colors font-body"
          />
          <p className="mt-1.5 text-xs text-text-muted">
            Enter your child's username or email to request a link. An admin will review and approve the connection.
          </p>
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full py-3 rounded-xl font-display font-semibold transition-colors bg-coral-500 text-white hover:bg-coral-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Creating Account...
            </>
          ) : (
            'Create Account'
          )}
        </button>
      </form>
    </AuthFormLayout>
  )
}