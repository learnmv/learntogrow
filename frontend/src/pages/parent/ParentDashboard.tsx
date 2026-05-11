import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Users, Link2, GraduationCap, Loader2, UserPlus, AlertCircle } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import { ParentAssistant } from '../../components/parent/ParentAssistant'
import { getLinkedChildren } from '../../services/parent'
import type { ParentStudentLink } from '../../types/parent'

const statusStyles: Record<string, string> = {
  approved: 'bg-sage-100 text-sage-700',
  pending: 'bg-yellow-100 text-yellow-700',
  rejected: 'bg-coral-100 text-coral-700',
}

const statusLabels: Record<string, string> = {
  approved: 'Approved',
  pending: 'Pending',
  rejected: 'Rejected',
}

export function ParentDashboard() {
  const { user } = useAuth()
  const [children, setChildren] = useState<ParentStudentLink[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadChildren()
  }, [])

  async function loadChildren() {
    try {
      setLoading(true)
      setError(null)
      const data = await getLinkedChildren()
      setChildren(data)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to load linked children'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <Users className="w-8 h-8 text-sage-600" />
          <h1 className="text-2xl font-display font-semibold text-text">
            Welcome, {user?.full_name || user?.username}
          </h1>
        </div>
        <p className="text-text-muted">
          View your linked children and monitor their learning progress.
        </p>
      </div>

      <ParentAssistant childrenList={children} />

      {/* Action Bar */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-display font-semibold text-text">Linked Children</h2>
        <Link
          to="/parent/link-request"
          className="flex items-center gap-2 px-4 py-2 bg-sage-600 text-white rounded-xl font-display font-medium hover:bg-sage-700 transition-colors"
        >
          <UserPlus className="w-4 h-4" />
          Request New Link
        </Link>
      </div>

      {/* Loading */}
      {loading && (
        <div className="text-center py-16">
          <Loader2 className="w-8 h-8 text-sage-600 animate-spin mx-auto" />
          <p className="mt-4 text-text-muted font-display">Loading children...</p>
        </div>
      )}

      {/* Error */}
      {!loading && error && (
        <div className="bg-coral-50 border border-coral-200 rounded-2xl p-6 text-center">
          <AlertCircle className="w-10 h-10 text-coral-600 mx-auto mb-3" />
          <p className="text-coral-700 font-display font-semibold text-lg mb-1">Error Loading Children</p>
          <p className="text-coral-600 text-sm mb-4">{error}</p>
          <button
            onClick={loadChildren}
            className="px-6 py-2 bg-sage-600 text-white rounded-xl font-display font-medium hover:bg-sage-700 transition-colors"
          >
            Retry
          </button>
        </div>
      )}

      {/* Children List */}
      {!loading && !error && children.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {children.map((child) => (
            <Link
              key={child.id}
              to={`/parent/child/${child.student_id}`}
              className="bg-surface-elevated rounded-2xl border border-border p-6 hover:border-sage-300 hover:shadow-sm transition-all group"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 bg-sage-100 rounded-xl">
                    <GraduationCap className="w-5 h-5 text-sage-600" />
                  </div>
                  <div>
                    <p className="font-display font-semibold text-text group-hover:text-sage-700 transition-colors">
                      {child.student_name}
                    </p>
                    <p className="text-sm text-text-muted">@{child.student_username}</p>
                  </div>
                </div>
                <span
                  className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-display font-medium ${statusStyles[child.status] || statusStyles.approved}`}
                >
                  {statusLabels[child.status] || 'Approved'}
                </span>
              </div>
              <p className="text-sm text-text-muted">{child.student_email}</p>
              {child.approved_at && (
                <p className="text-xs text-text-subtle mt-2">
                  Approved {new Date(child.approved_at).toLocaleDateString()}
                </p>
              )}
            </Link>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && children.length === 0 && (
        <div className="bg-surface-elevated rounded-2xl border border-border p-12 text-center">
          <div className="w-16 h-16 bg-sage-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Link2 className="w-8 h-8 text-sage-400" />
          </div>
          <h3 className="text-lg font-display font-semibold text-text mb-2">No Children Linked Yet</h3>
          <p className="text-text-muted max-w-sm mx-auto mb-6">
            Link your account to your child to view their quiz progress and learning statistics.
          </p>
          <Link
            to="/parent/link-request"
            className="inline-flex items-center gap-2 px-6 py-3 bg-coral-500 text-white rounded-xl font-display font-semibold hover:bg-coral-600 transition-colors"
          >
            <UserPlus className="w-5 h-5" />
            Request a Link
          </Link>
        </div>
      )}
    </div>
  )
}
