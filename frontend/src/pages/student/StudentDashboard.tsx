import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { BookOpen, Play, Target, BarChart3 } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import { SubjectSelector } from '../../components/ui/SubjectSelector'
import { LoadingSpinner } from '../../components/ui/LoadingSpinner'
import { getOwnProgress } from '../../services/student'
import type { StudentProgress } from '../../types/student'

export function StudentDashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [selectedSubject, setSelectedSubject] = useState<string>('')
  const [selectedGrade, setSelectedGrade] = useState<string>('')
  const [progress, setProgress] = useState<StudentProgress | null>(null)
  const [loadingProgress, setLoadingProgress] = useState(true)

  useEffect(() => {
    async function loadData() {
      try {
        const p = await getOwnProgress()
        setProgress(p)
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

  const displayName = user?.full_name || user?.username || 'Student'
  const canStartQuiz = selectedSubject !== '' && selectedGrade !== ''

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
          <button
            onClick={handleStartQuiz}
            disabled={!canStartQuiz}
            className="flex items-center gap-2 px-6 py-3 bg-sage-600 text-white rounded-xl font-display font-semibold hover:bg-sage-700 transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed shadow-lg shadow-sage-200 hover:shadow-xl"
          >
            <Play className="w-5 h-5" />
            Start Quiz
          </button>
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

      {/* Recent Answers section removed per user request */}
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
