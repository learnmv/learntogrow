import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Clock, CheckCircle, XCircle } from 'lucide-react'
import { getOwnAttempts } from '../../services/student'
import { LoadingSpinner } from '../../components/ui/LoadingSpinner'
import type { RecentAnswer } from '../../types/student'

export function QuizHistoryPage() {
  const [recentAnswers, setRecentAnswers] = useState<RecentAnswer[]>([])
  const [loading, setLoading] = useState(true)
  const [notAvailable, setNotAvailable] = useState(false)

  useEffect(() => {
    async function loadAttempts() {
      try {
        const data = await getOwnAttempts()
        setRecentAnswers(data.recent_answers ?? [])
      } catch {
        setNotAvailable(true)
      } finally {
        setLoading(false)
      }
    }
    loadAttempts()
  }, [])

  if (loading) {
    return <LoadingSpinner text="Loading quiz history..." />
  }

  const isEmpty = notAvailable || recentAnswers.length === 0

  return (
    <div className="max-w-4xl mx-auto">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-6">
        <h1 className="text-2xl font-display font-semibold text-text">Quiz History</h1>
        <p className="mt-1 text-text-muted font-body">Review your past answers and track improvement.</p>
      </motion.div>

      {isEmpty ? (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-surface-elevated rounded-2xl p-10 shadow-sm border border-border text-center"
        >
          <div className="w-16 h-16 bg-sage-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Clock className="w-8 h-8 text-sage-600" />
          </div>
          <p className="text-text font-display font-semibold text-lg mb-2">No History Yet</p>
          <p className="text-text-muted font-body max-w-sm mx-auto">
            Your quiz history will appear here as you answer questions. Head to your dashboard to start a quiz.
          </p>
        </motion.div>
      ) : (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="space-y-3"
        >
          {recentAnswers.map((answer) => (
            <div
              key={`${answer.question_id}-${answer.answered_at}`}
              className="bg-surface-elevated rounded-2xl p-4 shadow-sm border border-border flex items-center justify-between hover:shadow-md transition-shadow"
            >
              <div className="flex items-center gap-4">
                <div className={`p-2.5 rounded-xl ${answer.is_correct ? 'bg-sage-100' : 'bg-coral-100'}`}>
                  {answer.is_correct ? (
                    <CheckCircle className="w-5 h-5 text-sage-600" />
                  ) : (
                    <XCircle className="w-5 h-5 text-coral-600" />
                  )}
                </div>
                <div>
                  <p className="font-display font-semibold text-text">{answer.standard_code}</p>
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-display font-medium mt-1 ${
                      answer.is_correct ? 'bg-sage-100 text-sage-700' : 'bg-coral-100 text-coral-700'
                    }`}
                  >
                    {answer.is_correct ? 'Correct' : 'Incorrect'}
                  </span>
                </div>
              </div>
              <span className="text-sm text-text-muted font-body">
                {new Date(answer.answered_at).toLocaleDateString()}
              </span>
            </div>
          ))}
        </motion.div>
      )}
    </div>
  )
}