import { useState, useEffect } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  ArrowLeft, GraduationCap, BarChart3, BookOpen, Target, Loader2,
  AlertCircle, Clock, CheckCircle, XCircle,
} from 'lucide-react'
import { getChildProgress } from '../../services/parent'
import type { StudentDetailForParent, DetailedAttempt } from '../../types/parent'

function formatDate(dateString: string | null): string {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}

export function ChildProgressPage() {
  const { studentId } = useParams<{ studentId: string }>()
  const [data, setData] = useState<StudentDetailForParent | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (studentId) {
      loadProgress()
    }
  }, [studentId])

  async function loadProgress() {
    try {
      setLoading(true)
      setError(null)
      const result = await getChildProgress(Number(studentId))
      setData(result)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to load child progress'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto">
        <div className="text-center py-16">
          <Loader2 className="w-8 h-8 text-sage-600 animate-spin mx-auto" />
          <p className="mt-4 text-text-muted font-display">Loading progress...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-5xl mx-auto">
        <Link to="/parent" className="inline-flex items-center gap-1.5 text-sm text-text-muted hover:text-sage-600 font-display font-medium transition-colors mb-6">
          <ArrowLeft className="w-4 h-4" />
          Back to Dashboard
        </Link>
        <div className="bg-coral-50 border border-coral-200 rounded-2xl p-6 text-center">
          <AlertCircle className="w-10 h-10 text-coral-600 mx-auto mb-3" />
          <p className="text-coral-700 font-display font-semibold text-lg mb-1">Error Loading Progress</p>
          <p className="text-coral-600 text-sm mb-4">{error}</p>
          <button onClick={loadProgress} className="px-6 py-2 bg-sage-600 text-white rounded-xl font-display font-medium hover:bg-sage-700 transition-colors">
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (!data) return null

  const averageScore = data.average_score !== null ? Math.round(data.average_score) : null

  return (
    <div className="max-w-5xl mx-auto">
      <Link to="/parent" className="inline-flex items-center gap-1.5 text-sm text-text-muted hover:text-sage-600 font-display font-medium transition-colors mb-6">
        <ArrowLeft className="w-4 h-4" />
        Back to Dashboard
      </Link>

      {/* Child Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2.5 bg-sage-100 rounded-xl">
            <GraduationCap className="w-6 h-6 text-sage-600" />
          </div>
          <div>
            <h1 className="text-2xl font-display font-semibold text-text">{data.student_name}</h1>
            <p className="text-text-muted text-sm">@{data.student_username} · {data.email}</p>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <SummaryCard icon={BarChart3} label="Total Attempts" value={String(data.total_attempts)} color="sage" />
        <SummaryCard icon={Target} label="Average Score" value={averageScore !== null ? `${averageScore}%` : '-'} color={averageScore !== null && averageScore >= 70 ? 'sage' : 'coral'} />
        <SummaryCard icon={BookOpen} label="Standards Attempted" value={String(data.standards_attempted)} color="sage" />
        <SummaryCard icon={Clock} label="Recent Activity" value={data.recent_attempts.length > 0 ? formatDate(data.recent_attempts[0].answered_at) : 'No activity'} color="sage" />
      </div>

      {/* Recent Answers Table */}
      <div className="bg-surface-elevated rounded-2xl border border-border overflow-hidden">
        <div className="px-6 py-4 border-b border-border">
          <h2 className="text-lg font-display font-semibold text-text">Recent Answers</h2>
        </div>

        {data.recent_attempts.length === 0 ? (
          <div className="text-center py-12">
            <BookOpen className="w-10 h-10 text-text-muted mx-auto mb-3" />
            <p className="text-text-muted font-display">No answers yet</p>
            <p className="text-text-subtle text-sm mt-1">Progress will appear here once the student completes a quiz.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-sage-50">
                <tr>
                  <th className="px-6 py-3 text-left text-sm font-display font-medium text-text">Standard</th>
                  <th className="px-6 py-3 text-left text-sm font-display font-medium text-text">Result</th>
                  <th className="px-6 py-3 text-left text-sm font-display font-medium text-text">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {data.recent_attempts.map((attempt: DetailedAttempt) => (
                  <tr key={attempt.answer_id} className="hover:bg-sage-50/50">
                    <td className="px-6 py-4">
                      <div>
                        <p className="font-display font-medium text-text">{attempt.standard_code || 'Unknown'}</p>
                        {attempt.standard_description && (
                          <p className="text-sm text-text-muted line-clamp-1 max-w-xs">{attempt.standard_description}</p>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-display font-semibold ${
                        attempt.is_correct ? 'bg-sage-100 text-sage-700' : 'bg-coral-100 text-coral-700'
                      }`}>
                        {attempt.is_correct ? (
                          <>
                            <CheckCircle className="w-3.5 h-3.5" />
                            Correct
                          </>
                        ) : (
                          <>
                            <XCircle className="w-3.5 h-3.5" />
                            Incorrect
                          </>
                        )}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-text-muted">{formatDate(attempt.answered_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

interface SummaryCardProps {
  icon: React.ComponentType<{ className?: string }>
  label: string
  value: string
  color: 'sage' | 'coral'
}

function SummaryCard({ icon: Icon, label, value, color }: SummaryCardProps) {
  const bgClass = color === 'sage' ? 'bg-sage-100' : 'bg-coral-100'
  const iconClass = color === 'sage' ? 'text-sage-600' : 'text-coral-600'
  const valueClass = color === 'sage' ? 'text-text' : 'text-coral-700'

  return (
    <div className="bg-surface-elevated rounded-2xl border border-border p-5">
      <div className="flex items-start justify-between mb-3">
        <p className="text-sm font-display font-medium text-text-muted">{label}</p>
        <div className={`p-2 rounded-lg ${bgClass}`}>
          <Icon className={`w-4 h-4 ${iconClass}`} />
        </div>
      </div>
      <p className={`text-2xl font-display font-bold ${valueClass}`}>{value}</p>
    </div>
  )
}