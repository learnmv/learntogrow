import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Link2, ArrowLeft, Loader2, CheckCircle } from 'lucide-react'
import { requestStudentLink } from '../../services/parent'
import type { LinkRequestData } from '../../types/parent'

export function ParentLinkRequestPage() {
  const [emailOrUsername, setEmailOrUsername] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setIsSubmitting(true)
    setError(null)
    setSuccess(false)

    const data: LinkRequestData = { student_email_or_username: emailOrUsername.trim() }

    try {
      await requestStudentLink(data)
      setSuccess(true)
      setEmailOrUsername('')
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to submit link request'
      setError(message)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="max-w-lg mx-auto">
      <Link
        to="/parent"
        className="inline-flex items-center gap-1.5 text-sm text-text-muted hover:text-sage-600 font-display font-medium transition-colors mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Dashboard
      </Link>

      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2.5 bg-sage-100 rounded-xl">
            <Link2 className="w-6 h-6 text-sage-600" />
          </div>
          <h1 className="text-2xl font-display font-semibold text-text">Request Student Link</h1>
        </div>
        <p className="text-text-muted">
          Enter your child's email or username to request access to their progress data.
          An admin will review and approve the link.
        </p>
      </div>

      {success && (
        <div className="bg-sage-50 border border-sage-200 rounded-xl p-4 mb-6 flex items-start gap-3">
          <CheckCircle className="w-5 h-5 text-sage-600 mt-0.5 shrink-0" />
          <div>
            <p className="font-display font-semibold text-sage-700">Link Request Submitted</p>
            <p className="text-sage-600 text-sm mt-1">
              Your request has been submitted. Waiting for admin approval.
            </p>
          </div>
        </div>
      )}

      {error && (
        <div className="bg-coral-50 border border-coral-200 rounded-xl p-4 mb-6 flex items-start gap-3">
          <Link2 className="w-5 h-5 text-coral-600 mt-0.5 shrink-0" />
          <div>
            <p className="font-display font-semibold text-coral-700">Request Failed</p>
            <p className="text-coral-600 text-sm mt-1">{error}</p>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-surface-elevated rounded-2xl border border-border p-6">
        <div className="mb-6">
          <label htmlFor="student-email" className="block text-sm font-display font-medium text-text mb-1.5">
            Student Email or Username
          </label>
          <input
            id="student-email"
            type="text"
            required
            value={emailOrUsername}
            onChange={(e) => setEmailOrUsername(e.target.value)}
            placeholder="e.g. student@email.com or john_doe"
            className="w-full px-4 py-3 rounded-xl border border-border bg-surface focus:border-sage-500 focus:ring-2 focus:ring-sage-200 outline-none transition-colors font-body"
          />
          <p className="text-xs text-text-subtle mt-2">
            This must match the email or username registered for the student account.
          </p>
        </div>

        <button
          type="submit"
          disabled={isSubmitting || !emailOrUsername.trim()}
          className="w-full py-3 rounded-xl font-display font-semibold transition-colors bg-coral-500 text-white hover:bg-coral-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Submitting Request...
            </>
          ) : (
            'Submit Link Request'
          )}
        </button>
      </form>
    </div>
  )
}