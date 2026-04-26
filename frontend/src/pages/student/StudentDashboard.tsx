import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { BookOpen, Play, Target, BarChart3, RotateCcw, Zap } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import { SubjectSelector } from '../../components/ui/SubjectSelector'
import { LoadingSpinner } from '../../components/ui/LoadingSpinner'
import { getOwnProgress, fetchMistakeStandards } from '../../services/student'
import { fetchDomainsBySubject } from '../../services/standards'
import { fetchDomainTheta } from '../../services/adaptive'
import type { StudentProgress } from '../../types/student'
import type { Standard, Domain } from '../../types/standards'

interface DomainProgress {
  domain: Domain
  theta: number
  questions_attempted: number
  correct_streak: number
}

export function StudentDashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [selectedSubject, setSelectedSubject] = useState<string>('')
  const [selectedGrade, setSelectedGrade] = useState<string>('')
  const [progress, setProgress] = useState<StudentProgress | null>(null)
  const [mistakes, setMistakes] = useState<Standard[]>([])
  const [loadingProgress, setLoadingProgress] = useState(true)
  const [domains, setDomains] = useState<DomainProgress[]>([])
  const [loadingDomains, setLoadingDomains] = useState(false)

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

  // Fetch mistake standards when subject/grade selection changes
  useEffect(() => {
    if (!selectedSubject || !selectedGrade) {
      setMistakes([])
      return
    }

    async function loadMistakes() {
      try {
        const standards = await fetchMistakeStandards({
          subject_id: parseInt(selectedSubject),
          grade_id: parseInt(selectedGrade),
        })
        setMistakes(standards)
      } catch {
        setMistakes([])
      }
    }
    loadMistakes()
  }, [selectedSubject, selectedGrade])

  // Fetch domains + adaptive progress when subject is selected
  useEffect(() => {
    if (!selectedSubject) {
      setDomains([])
      return
    }

    async function loadDomains() {
      setLoadingDomains(true)
      try {
        const domainList = await fetchDomainsBySubject(parseInt(selectedSubject))
        const progressData = await Promise.all(
          domainList.map(async (domain) => {
            try {
              const thetaData = await fetchDomainTheta(domain.id)
              return {
                domain,
                theta: thetaData.theta,
                questions_attempted: thetaData.questions_attempted,
                correct_streak: thetaData.correct_streak,
              }
            } catch {
              return {
                domain,
                theta: 0.35,
                questions_attempted: 0,
                correct_streak: 0,
              }
            }
          })
        )
        setDomains(progressData)
      } catch {
        setDomains([])
      } finally {
        setLoadingDomains(false)
      }
    }
    loadDomains()
  }, [selectedSubject])

  function handleStartQuiz() {
    if (selectedSubject && selectedGrade) {
      navigate(`/quiz?subjectId=${selectedSubject}&gradeId=${selectedGrade}`)
    }
  }

  function handlePracticeMistakes() {
    if (selectedSubject && selectedGrade && mistakes.length > 0) {
      navigate(`/quiz?subjectId=${selectedSubject}&gradeId=${selectedGrade}&mode=mistakes`)
    }
  }

  function handleAdaptivePractice(domainId: number, domainName: string) {
    navigate(`/adaptive-quiz?domainId=${domainId}&domainName=${encodeURIComponent(domainName)}`)
  }

  const displayName = user?.full_name || user?.username || 'Student'
  const canStartQuiz = selectedSubject !== '' && selectedGrade !== ''
  const hasMistakes = mistakes.length > 0

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
          <div className="flex flex-col gap-3">
            <button
              onClick={handleStartQuiz}
              disabled={!canStartQuiz}
              className="flex items-center gap-2 px-6 py-3 bg-sage-600 text-white rounded-xl font-display font-semibold hover:bg-sage-700 transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed shadow-lg shadow-sage-200 hover:shadow-xl"
            >
              <Play className="w-5 h-5" />
              Start Quiz
            </button>
            {hasMistakes && (
              <button
                onClick={handlePracticeMistakes}
                className="flex items-center gap-2 px-6 py-3 bg-coral-500 text-white rounded-xl font-display font-semibold hover:bg-coral-600 transition-all duration-200 shadow-lg shadow-coral-200 hover:shadow-xl"
              >
                <RotateCcw className="w-5 h-5" />
                Practice Mistakes ({mistakes.length})
              </button>
            )}
          </div>
        </div>
        {!canStartQuiz && (
          <p className="mt-3 text-sm text-text-muted font-body">
            Select a subject and grade above to begin.
          </p>
        )}
      </motion.div>

      {/* Adaptive Practice by Domain */}
      {selectedSubject && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="mb-8"
        >
          <h2 className="text-lg font-display font-semibold text-text mb-4 flex items-center gap-2">
            <Zap className="w-5 h-5 text-sand-600" />
            Adaptive Practice
          </h2>
          {loadingDomains ? (
            <LoadingSpinner text="Loading domains..." />
          ) : domains.length === 0 ? (
            <p className="text-text-muted font-body">No domains found for this subject.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {domains.map(({ domain, theta, questions_attempted }) => (
                <DomainCard
                  key={domain.id}
                  domain={domain}
                  theta={theta}
                  questions_attempted={questions_attempted}
                  onPractice={() => handleAdaptivePractice(domain.id, domain.name)}
                />
              ))}
            </div>
          )}
        </motion.div>
      )}

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
    </div>
  )
}

interface DomainCardProps {
  domain: Domain
  theta: number
  questions_attempted: number
  onPractice: () => void
}

function DomainCard({ domain, theta, questions_attempted, onPractice }: DomainCardProps) {
  const thetaPct = Math.round(theta * 100)
  const level = thetaPct < 40 ? 'Getting Started' : thetaPct < 70 ? 'Developing' : 'Proficient'
  const colorClass = thetaPct < 40 ? 'bg-coral-500' : thetaPct < 70 ? 'bg-sand-500' : 'bg-sage-500'

  return (
    <div className="bg-surface-elevated rounded-2xl p-5 shadow-sm border border-border flex flex-col gap-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="font-display font-semibold text-text">{domain.name}</p>
          <p className="text-sm text-text-muted font-body">{domain.code}</p>
        </div>
        <div className="px-2.5 py-1 rounded-lg bg-sage-100 text-sage-700 text-xs font-display font-medium">
          {level}
        </div>
      </div>

      <div className="space-y-1">
        <div className="flex justify-between text-xs text-text-muted font-body">
          <span>Skill Level</span>
          <span>{thetaPct}%</span>
        </div>
        <div className="h-2 bg-sage-100 rounded-full overflow-hidden">
          <div
            className={`h-full ${colorClass} rounded-full transition-all duration-500`}
            style={{ width: `${thetaPct}%` }}
          />
        </div>
      </div>

      <div className="flex items-center justify-between mt-auto">
        <span className="text-xs text-text-muted font-body">
          {questions_attempted > 0 ? `${questions_attempted} attempted` : 'Not started'}
        </span>
        <button
          onClick={onPractice}
          className="flex items-center gap-1.5 px-4 py-2 bg-sage-600 text-white rounded-lg font-display font-medium text-sm hover:bg-sage-700 transition-colors shadow-sm hover:shadow-md"
        >
          <Zap className="w-3.5 h-3.5" />
          Practice
        </button>
      </div>
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
