import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Mail, Loader2 } from 'lucide-react'
import { AuthFormLayout } from '../../components/auth/AuthFormLayout'
import { requestPasswordReset } from '../../services/auth'

export function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isSuccess, setIsSuccess] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setIsSubmitting(true)
    setError(null)

    try {
      await requestPasswordReset({ email: email.trim() })
      setIsSuccess(true)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to send reset email. Please try again.'
      setError(message)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <AuthFormLayout
      title="Reset Password"
      subtitle="Enter your email to receive a reset link"
      footer={
        <>
          Remember your password?{' '}
          <Link to="/login" className="text-sage-600 hover:text-sage-700 font-medium">
            Sign In
          </Link>
        </>
      }
    >
      {isSuccess ? (
        <div className="p-4 bg-sage-50 border border-sage-200 rounded-xl text-center">
          <Mail className="w-8 h-8 text-sage-600 mx-auto mb-3" />
          <p className="text-sage-700 font-display font-medium">
            Check Your Email
          </p>
          <p className="text-text-muted text-sm mt-2">
            If an account exists with that email, a reset link has been sent.
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
            <label htmlFor="email" className="block text-sm font-display font-medium text-text mb-1">
              Email Address
            </label>
            <input
              id="email"
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email address"
              className="w-full px-4 py-3 rounded-xl border border-border bg-surface focus:border-sage-500 focus:ring-2 focus:ring-sage-200 outline-none transition-colors font-body"
            />
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-3 rounded-xl font-display font-semibold transition-colors bg-coral-500 text-white hover:bg-coral-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Sending Reset Link...
              </>
            ) : (
              'Send Reset Link'
            )}
          </button>
        </form>
      )}
    </AuthFormLayout>
  )
}