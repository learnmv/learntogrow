import { useState } from 'react'
import { useSearchParams, useNavigate, Link } from 'react-router-dom'
import { Eye, EyeOff, Loader2, AlertCircle } from 'lucide-react'
import { AuthFormLayout } from '../../components/auth/AuthFormLayout'
import { confirmPasswordReset } from '../../services/auth'

export function ResetPasswordPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')

  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showNewPassword, setShowNewPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isSuccess, setIsSuccess] = useState(false)

  function validateForm(): string | null {
    if (!newPassword) return 'Password is required'
    if (newPassword.length < 8) return 'Password must be at least 8 characters'
    if (newPassword !== confirmPassword) return 'Passwords do not match'
    return null
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()

    if (!token) {
      setError('Invalid or missing reset token. Please request a new password reset link.')
      return
    }

    const validationError = validateForm()
    if (validationError) {
      setError(validationError)
      return
    }

    setIsSubmitting(true)
    setError(null)

    try {
      await confirmPasswordReset({ token, new_password: newPassword })
      setIsSuccess(true)
      setTimeout(() => {
        navigate('/login', { replace: true })
      }, 2000)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to reset password. The link may have expired.'
      setError(message)
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!token) {
    return (
      <AuthFormLayout
        title="Set New Password"
        footer={
          <>
            <Link to="/forgot-password" className="text-sage-600 hover:text-sage-700 font-medium">
              Request a new reset link
            </Link>
            {' | '}
            <Link to="/login" className="text-sage-600 hover:text-sage-700 font-medium">
              Back to Sign In
            </Link>
          </>
        }
      >
        <div className="p-4 bg-coral-50 border border-coral-200 rounded-xl text-center">
          <AlertCircle className="w-8 h-8 text-coral-600 mx-auto mb-3" />
          <p className="text-coral-700 font-display font-medium">
            Invalid Reset Link
          </p>
          <p className="text-text-muted text-sm mt-2">
            This password reset link is missing a valid token. Please request a new one.
          </p>
        </div>
      </AuthFormLayout>
    )
  }

  return (
    <AuthFormLayout
      title="Set New Password"
      footer={
        <Link to="/login" className="text-sage-600 hover:text-sage-700 font-medium">
          Back to Sign In
        </Link>
      }
    >
      {isSuccess ? (
        <div className="p-4 bg-sage-50 border border-sage-200 rounded-xl text-center">
          <p className="text-sage-700 font-display font-medium">
            Password Reset Successfully
          </p>
          <p className="text-text-muted text-sm mt-2">
            Redirecting to sign in...
          </p>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="p-3 bg-coral-50 text-coral-700 rounded-lg text-sm">
              {error}
            </div>
          )}

          <div>
            <label htmlFor="newPassword" className="block text-sm font-display font-medium text-text mb-1">
              New Password <span className="text-coral-500">*</span>
            </label>
            <div className="relative">
              <input
                id="newPassword"
                type={showNewPassword ? 'text' : 'password'}
                required
                autoComplete="new-password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="At least 8 characters"
                className="w-full px-4 py-3 rounded-xl border border-border bg-surface focus:border-sage-500 focus:ring-2 focus:ring-sage-200 outline-none transition-colors font-body pr-12"
              />
              <button
                type="button"
                onClick={() => setShowNewPassword(!showNewPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text transition-colors"
                aria-label={showNewPassword ? 'Hide password' : 'Show password'}
              >
                {showNewPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
          </div>

          <div>
            <label htmlFor="confirmPassword" className="block text-sm font-display font-medium text-text mb-1">
              Confirm New Password <span className="text-coral-500">*</span>
            </label>
            <div className="relative">
              <input
                id="confirmPassword"
                type={showConfirmPassword ? 'text' : 'password'}
                required
                autoComplete="new-password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Re-enter your new password"
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

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-3 rounded-xl font-display font-semibold transition-colors bg-coral-500 text-white hover:bg-coral-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Resetting Password...
              </>
            ) : (
              'Reset Password'
            )}
          </button>
        </form>
      )}
    </AuthFormLayout>
  )
}