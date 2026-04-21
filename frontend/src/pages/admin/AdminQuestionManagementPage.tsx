import { useState, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import {
  BookOpen, Trash2, ToggleLeft, ToggleRight, Search, Filter,
  Loader2, AlertCircle, Inbox, X,
} from 'lucide-react'
import { getAdminQuestions, toggleQuestionStatus, deleteQuestion } from '../../services/admin'
import type { QuestionFromDB } from '../../types/questions'

type ActiveFilter = 'all' | 'active' | 'inactive'

export function AdminQuestionManagementPage() {
  const [questions, setQuestions] = useState<QuestionFromDB[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [standardIdFilter, setStandardIdFilter] = useState('')
  const [activeFilter, setActiveFilter] = useState<ActiveFilter>('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [togglingId, setTogglingId] = useState<number | null>(null)

  const loadQuestions = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const standardId = standardIdFilter ? Number(standardIdFilter) : undefined
      const isActive = activeFilter === 'all' ? undefined : activeFilter === 'active' ? true : false
      const data = await getAdminQuestions(standardId, undefined, undefined, isActive)
      setQuestions(data)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to load questions'
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [standardIdFilter, activeFilter])

  useEffect(() => {
    loadQuestions()
  }, [loadQuestions])

  async function handleToggleStatus(questionId: number) {
    try {
      setTogglingId(questionId)
      await toggleQuestionStatus(questionId)
      await loadQuestions()
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to toggle status'
      setError(message)
    } finally {
      setTogglingId(null)
    }
  }

  async function handleDelete(questionId: number) {
    if (!confirm('Are you sure you want to delete this question? This action cannot be undone.')) {
      return
    }
    try {
      setDeletingId(questionId)
      await deleteQuestion(questionId)
      await loadQuestions()
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to delete question'
      setError(message)
    } finally {
      setDeletingId(null)
    }
  }

  function truncateText(text: string, maxLength: number): string {
    if (text.length <= maxLength) return text
    return text.substring(0, maxLength) + '...'
  }

  function formatDifficulty(difficulty: number | null): string {
    if (difficulty === null || difficulty === undefined) return 'N/A'
    return (difficulty * 100).toFixed(0) + '%'
  }

  const filteredQuestions = questions.filter((q) => {
    if (!searchTerm) return true
    return q.question_text.toLowerCase().includes(searchTerm.toLowerCase())
  })

  function clearFilters() {
    setStandardIdFilter('')
    setActiveFilter('all')
    setSearchTerm('')
  }

  const hasActiveFilters = standardIdFilter !== '' || activeFilter !== 'all' || searchTerm !== ''

  if (loading && questions.length === 0) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 text-sage-600 animate-spin mx-auto" />
          <p className="mt-4 text-text-muted font-display">Loading questions...</p>
        </div>
      </div>
    )
  }

  if (error && questions.length === 0) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center max-w-md mx-auto">
          <div className="w-16 h-16 bg-coral-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-8 h-8 text-coral-600" />
          </div>
          <p className="text-coral-600 font-display text-lg mb-2">Error Loading Questions</p>
          <p className="text-text-muted mb-4">{error}</p>
          <button onClick={loadQuestions} className="px-6 py-2 bg-sage-600 text-white rounded-xl font-display font-medium hover:bg-sage-700 transition-colors">
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <BookOpen className="w-6 h-6 text-sage-600" />
        <h1 className="text-xl font-display font-semibold text-text">Question Management</h1>
      </div>

      {/* Inline error */}
      {error && (
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="flex items-center gap-3 p-4 bg-coral-50 border border-coral-200 rounded-xl">
          <AlertCircle className="w-5 h-5 text-coral-600 shrink-0" />
          <p className="text-coral-700 text-sm flex-1">{error}</p>
          <button onClick={() => setError(null)} className="text-coral-400 hover:text-coral-600 transition-colors" aria-label="Dismiss error">
            <X className="w-4 h-4" />
          </button>
        </motion.div>
      )}

      {/* Filters */}
      <div className="bg-surface-elevated rounded-2xl p-4 shadow-sm border border-border">
        <div className="flex items-center gap-2 mb-4">
          <Filter className="w-4 h-4 text-text-muted" />
          <span className="text-sm font-display font-medium text-text">Filters</span>
          {hasActiveFilters && (
            <button onClick={clearFilters} className="ml-auto text-xs text-sage-600 hover:text-sage-700 font-display font-medium transition-colors">
              Clear all
            </button>
          )}
        </div>
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
            <input
              type="text"
              placeholder="Search questions..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-border rounded-xl bg-surface focus:ring-2 focus:ring-sage-500 focus:border-transparent text-sm"
            />
          </div>
          <div className="w-full sm:w-40">
            <input
              type="number"
              placeholder="Standard ID"
              value={standardIdFilter}
              onChange={(e) => setStandardIdFilter(e.target.value)}
              min={1}
              className="w-full px-4 py-2 border border-border rounded-xl bg-surface focus:ring-2 focus:ring-sage-500 focus:border-transparent text-sm"
            />
          </div>
          <div className="w-full sm:w-auto">
            <select
              value={activeFilter}
              onChange={(e) => setActiveFilter(e.target.value as ActiveFilter)}
              className="w-full px-4 py-2 border border-border rounded-xl bg-surface focus:ring-2 focus:ring-sage-500 focus:border-transparent text-sm"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>
        </div>
      </div>

      {/* Results count */}
      <p className="text-sm text-text-muted font-display">
        {loading ? 'Updating...' : `${filteredQuestions.length} question${filteredQuestions.length !== 1 ? 's' : ''} found`}
      </p>

      {/* Questions Table */}
      <div className="bg-surface-elevated rounded-2xl border border-border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-sage-50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-display font-medium text-text">Question</th>
                <th className="px-4 py-3 text-left text-sm font-display font-medium text-text">Standard</th>
                <th className="px-4 py-3 text-left text-sm font-display font-medium text-text">Type</th>
                <th className="px-4 py-3 text-left text-sm font-display font-medium text-text">Difficulty</th>
                <th className="px-4 py-3 text-left text-sm font-display font-medium text-text">Status</th>
                <th className="px-4 py-3 text-right text-sm font-display font-medium text-text">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filteredQuestions.map((question) => (
                <tr key={question.id} className="hover:bg-sage-50/50">
                  <td className="px-4 py-3">
                    <p className="text-sm text-text font-body">{truncateText(question.question_text, 100)}</p>
                  </td>
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center px-2.5 py-1 rounded-lg bg-sage-100 text-sage-700 text-xs font-display font-medium">
                      #{question.standard_id}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-sm text-text-muted capitalize">{question.question_type.replace('_', ' ')}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-sm text-text-muted">{formatDifficulty(question.difficulty)}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-display font-medium ${
                      question.is_active ? 'bg-green-100 text-green-700' : 'bg-surface-muted text-text-muted'
                    }`}>
                      {question.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => handleToggleStatus(question.id)}
                        disabled={togglingId === question.id}
                        className={`p-2 rounded-lg transition-colors disabled:opacity-50 ${
                          question.is_active ? 'text-sage-600 hover:bg-sage-50' : 'text-text-muted hover:bg-sage-50'
                        }`}
                        title={question.is_active ? 'Deactivate' : 'Activate'}
                        aria-label={question.is_active ? 'Deactivate question' : 'Activate question'}
                      >
                        {togglingId === question.id ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : question.is_active ? (
                          <ToggleRight className="w-4 h-4" />
                        ) : (
                          <ToggleLeft className="w-4 h-4" />
                        )}
                      </button>
                      <button
                        onClick={() => handleDelete(question.id)}
                        disabled={deletingId === question.id}
                        className="p-2 rounded-lg text-coral-500 hover:bg-coral-50 transition-colors disabled:opacity-50"
                        title="Delete"
                        aria-label="Delete question"
                      >
                        {deletingId === question.id ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <Trash2 className="w-4 h-4" />
                        )}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Empty State */}
        {filteredQuestions.length === 0 && (
          <div className="text-center py-16 px-4">
            <Inbox className="w-12 h-12 text-text-muted mx-auto mb-4" />
            <p className="font-display font-semibold text-text mb-1">No questions found</p>
            <p className="text-sm text-text-muted">
              {hasActiveFilters ? 'Try adjusting your filters to see more results.' : 'Generate questions from the dashboard to get started.'}
            </p>
            {hasActiveFilters && (
              <button onClick={clearFilters} className="mt-4 px-4 py-2 text-sm bg-sage-600 text-white rounded-xl font-display font-medium hover:bg-sage-700 transition-colors">
                Clear filters
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}