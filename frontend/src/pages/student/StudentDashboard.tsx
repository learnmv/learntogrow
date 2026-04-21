import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { BookOpen, Play, BarChart3, Target, Clock, CheckCircle, XCircle, Zap, TrendingUp, TrendingDown, Lightbulb } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import { SubjectSelector } from '../../components/ui/SubjectSelector'
import { LoadingSpinner } from '../../components/ui/LoadingSpinner'
import { getOwnProgress } from '../../services/student'
import { getDomainProgress, getStrengthsWeaknesses } from '../../services/adaptive'
import type { StudentProgress, RecentAnswer } from '../../types/student'
import type { DomainProgress, StrengthsWeaknesses } from '../../services/adaptive'

export function StudentDashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [selectedSubject, setSelectedSubject] = useState<string>('')
  const [selectedGrade, setSelectedGrade] = useState<string>('')
  const [progress, setProgress] = useState<StudentProgress | null>(null)
  const [domainProgress, setDomainProgress] = useState<DomainProgress[]>([])
  const [swData, setSwData] = useState<StrengthsWeaknesses | null>(null)
  const [loadingProgress, setLoadingProgress] = useState(true)

  useEffect(() => {
    async function loadData() {
      try {
        const [p, dp, sw] = await Promise.all([
          getOwnProgress(),
          getDomainProgress().catch(() => [] as DomainProgress[]),
          getStrengthsWeaknesses().catch(() => null),
        ])
        setProgress(p)
        setDomainProgress(dp)
        setSwData(sw)
      } catch {
        // Backend endpoint may not exist yet
      } finally {
        setLoadingProgress(false)
              }
    }
    loadData()
  }, [])

  const handleGradeSelect = useCallback((subjectId: string, gradeId: string) => {
    setSelectedSubject(subjectId)
    setSelectedGrade(gradeId)
  }, [])

  function handleStartQuiz() {
    if (selectedSubject && selectedGrade) {
      navigate(`/quiz?subjectId=${selectedSubject}&gradeId=${selectedGrade}`)
    }
  }

  function handleStartAdaptiveQuiz() {
    if (selectedGrade) {
      navigate(`/quiz?subjectId=${selectedSubject || '1'}&gradeId=${selectedGrade}&adaptive=1`)
    }
  }

  const displayName = user?.full_name || user?.username || 'Student'
  const canStartQuiz = selectedSubject !== '' && selectedGrade !== ''
  const canStartAdaptive = selectedGrade !== ''

  return (
    <div className="max-w-7xl mx-auto">
      {/* Welcome */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
        <h1 className="text-3xl font-display font-semibold text-text">
          Welcome back, {displayName}!
        </h1>
        <p className="mt-1 text-text-muted font-body">
          Ready to keep learning? Pick a subject and grade to start a quiz.
        </p>
      </motion.div>

      {/* Quick Start */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-surface-elevated rounded-2xl p-6 shadow-sm border border-border mb-8"
      >
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2.5 rounded-xl bg-sage-100">
            <BookOpen className="w-5 h-5 text-sage-600" />
          </div>
          <h2 className="text-lg font-display font-semibold text-text">Start a Quiz</h2>
        </div>

        <div className="flex flex-wrap items-end gap-6">
          <SubjectSelector onGradeSelect={handleGradeSelect} />
          <div className="flex gap-3">
            <button
              onClick={handleStartQuiz}
              disabled={!canStartQuiz}
              className="flex items-center gap-2 px-6 py-3 bg-sage-600 text-white rounded-xl font-display font-semibold hover:bg-sage-700 transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed shadow-lg shadow-sage-200 hover:shadow-xl"
            >
              <Play className="w-5 h-5" />
              Start Quiz
            </button>
            <button
              onClick={handleStartAdaptiveQuiz}
              disabled={!canStartAdaptive}
              title={!canStartAdaptive ? 'Select a grade to start an adaptive quiz' : 'Questions matched to your learning needs'}
              className="flex items-center gap-2 px-6 py-3 bg-coral-500 text-white rounded-xl font-display font-semibold hover:bg-coral-600 transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed shadow-lg shadow-coral-200 hover:shadow-xl"
            >
              <Zap className="w-5 h-5" />
              Adaptive Quiz
            </button>
          </div>
        </div>
        {!canStartQuiz && (
          <p className="mt-3 text-sm text-text-muted font-body">
            Select a subject and grade above to begin.
          </p>
        )}
      </motion.div>

      {/* Progress Stats */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="mb-8"
      >
        <h2 className="text-lg font-display font-semibold text-text mb-4">Your Progress</h2>
        {loadingProgress ? (
          <LoadingSpinner text="Loading progress..." />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <ProgressStatCard
              icon={Target}
              label="Questions Answered"
              value={progress?.total_answered ?? 0}
              sublabel={progress ? `${progress.correct_count} correct` : 'Start a quiz to track progress'}
            />
            <ProgressStatCard
              icon={BarChart3}
              label="Accuracy"
              value={progress?.accuracy != null ? `${Math.round(progress.accuracy * 100)}%` : '--'}
              sublabel={progress ? `Across ${progress.total_answered} questions` : 'Answer questions to see your accuracy'}
            />
            <ProgressStatCard
              icon={BookOpen}
              label="Standards Attempted"
              value={progress?.standards_attempted ?? 0}
              sublabel={progress ? 'Unique standards covered' : 'Explore different standards'}
            />
          </div>
        )}
      </motion.div>

      {/* Domain Progress */}
      {domainProgress.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
          className="mb-8"
        >
          <h2 className="text-lg font-display font-semibold text-text mb-4">Domain Progress</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {domainProgress.map((dp) => (
              <div key={dp.domain_id} className="bg-surface-elevated rounded-2xl p-5 shadow-sm border border-border"
              >
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <p className="font-display font-medium text-text">{dp.domain_name}</p>
                    <p className="text-xs text-text-muted">{dp.correct_count}/{dp.total_answered} correct · Difficulty: {dp.current_difficulty.toFixed(1)}</p>
                  </div>
                  <div className={`text-lg font-display font-bold ${dp.accuracy >= 0.8 ? 'text-sage-600' : dp.accuracy >= 0.5 ? 'text-amber-600' : 'text-coral-600'}`}>
                    {Math.round(dp.accuracy * 100)}%
                  </div>
                </div>
                <div className="w-full h-2 bg-sage-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${dp.accuracy >= 0.8 ? 'bg-sage-500' : dp.accuracy >= 0.5 ? 'bg-amber-400' : 'bg-coral-400'}`}
                    style={{ width: `${Math.round(dp.accuracy * 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Strengths & Weaknesses */}
      {swData && (swData.strengths.length > 0 || swData.weaknesses.length > 0) && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="mb-8"
        >
          <h2 className="text-lg font-display font-semibold text-text mb-4">Insights</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {swData.strengths.length > 0 && (
              <div className="bg-sage-50 border border-sage-200 rounded-2xl p-5">
                <div className="flex items-center gap-2 mb-3">
                  <TrendingUp className="w-5 h-5 text-sage-600" />
                  <p className="font-display font-semibold text-sage-700">Strengths</p>
                </div>
                <ul className="space-y-2">
                  {swData.strengths.map((s) => (
                    <li key={s.domain_id} className="text-sm text-text">
                      <span className="font-medium">{s.domain_name}</span> — {Math.round(s.accuracy * 100)}% accuracy
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {swData.weaknesses.length > 0 && (
              <div className="bg-coral-50 border border-coral-200 rounded-2xl p-5">
                <div className="flex items-center gap-2 mb-3">
                  <TrendingDown className="w-5 h-5 text-coral-600" />
                  <p className="font-display font-semibold text-coral-700">Focus Areas</p>
                </div>
                <ul className="space-y-2">
                  {swData.weaknesses.map((w) => (
                    <li key={w.domain_id} className="text-sm text-text">
                      <span className="font-medium">{w.domain_name}</span> — {Math.round(w.accuracy * 100)}% accuracy
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
          {swData.recommendations.length > 0 && (
            <div className="mt-4 bg-surface-elevated rounded-2xl p-5 border border-border">
              <div className="flex items-center gap-2 mb-2">
                <Lightbulb className="w-5 h-5 text-amber-500" />
                <p className="font-display font-semibold text-text">Recommendations</p>
              </div>
              <ul className="space-y-1">
                {swData.recommendations.map((r, i) => (
                  <li key={i} className="text-sm text-text-muted">• {r}</li>
                ))}
              </ul>
            </div>
          )}
        </motion.div>
      )}

      {/* Recent Answers */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.35 }}
      >
        <h2 className="text-lg font-display font-semibold text-text mb-4">Recent Answers</h2>
        {!progress || progress.recent_answers.length === 0 ? (
          <div className="bg-surface-elevated rounded-2xl p-8 shadow-sm border border-border text-center">
            <div className="w-14 h-14 bg-sage-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Clock className="w-7 h-7 text-sage-600" />
            </div>
            <p className="text-text-muted font-body">No answers yet. Start a quiz to see your recent activity here.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {progress.recent_answers.map((answer: RecentAnswer) => (
              <div key={answer.question_id} className="bg-surface-elevated rounded-2xl p-4 shadow-sm border border-border flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className={`p-2 rounded-xl ${answer.is_correct ? 'bg-sage-100' : 'bg-coral-100'}`}>
                    {answer.is_correct ? (
                      <CheckCircle className="w-5 h-5 text-sage-600" />
                    ) : (
                      <XCircle className="w-5 h-5 text-coral-600" />
                    )}
                  </div>
                  <div>
                    <p className="font-display font-medium text-text">{answer.standard_code}</p>
                    <p className="text-sm text-text-muted">{answer.is_correct ? 'Correct' : 'Incorrect'}</p>
                  </div>
                </div>
                <span className="text-sm text-text-muted font-body">
                  {new Date(answer.answered_at).toLocaleDateString()}
                </span>
              </div>
            ))}
          </div>
        )}
      </motion.div>
    </div>
  )
}

interface ProgressStatCardProps {
  icon: React.ComponentType<{ className?: string }>
  label: string
  value: number | string
  sublabel: string
}

function ProgressStatCard({ icon: Icon, label, value, sublabel }: ProgressStatCardProps) {
  return (
    <div className="bg-surface-elevated rounded-2xl p-6 shadow-sm border border-border">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-text-muted">{label}</p>
          <p className="text-3xl font-display font-bold text-text mt-2">{value}</p>
        </div>
        <div className="p-3 rounded-xl bg-sage-100">
          <Icon className="w-6 h-6 text-sage-600" />
        </div>
      </div>
      <p className="text-sm text-text-muted mt-4">{sublabel}</p>
    </div>
  )
}
