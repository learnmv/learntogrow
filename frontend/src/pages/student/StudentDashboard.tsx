import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowRight, BookOpen, ClipboardList, Play, Target, BarChart3, RotateCcw, Zap } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import { SubjectSelector } from '../../components/ui/SubjectSelector'
import { LoadingSpinner } from '../../components/ui/LoadingSpinner'
import {
  getOwnProgress,
  fetchMistakeStandards,
  getDailyGoal,
  getSkillMap,
  getAssignedQuizzes,
} from '../../services/student'
import type { DailyGoal, SkillMapDomain, StudentProgress } from '../../types/student'
import type { Standard } from '../../types/standards'
import type { QuizAssignmentSummary } from '../../types/quizAssignment'

export function StudentDashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [selectedSubject, setSelectedSubject] = useState<string>('')
  const [selectedGrade, setSelectedGrade] = useState<string>('')
  const [progress, setProgress] = useState<StudentProgress | null>(null)
  const [dailyGoal, setDailyGoal] = useState<DailyGoal | null>(null)
  const [mistakes, setMistakes] = useState<Standard[]>([])
  const [loadingProgress, setLoadingProgress] = useState(true)
  const [loadingDailyGoal, setLoadingDailyGoal] = useState(true)
  const [skillMap, setSkillMap] = useState<SkillMapDomain[]>([])
  const [loadingSkillMap, setLoadingSkillMap] = useState(false)
  const [assignments, setAssignments] = useState<QuizAssignmentSummary[]>([])
  const [loadingAssignments, setLoadingAssignments] = useState(true)

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

  useEffect(() => {
    async function loadDailyGoal() {
      try {
        const goal = await getDailyGoal()
        setDailyGoal(goal)
      } catch {
        setDailyGoal(null)
      } finally {
        setLoadingDailyGoal(false)
      }
    }
    loadDailyGoal()
  }, [])

  useEffect(() => {
    async function loadAssignments() {
      try {
        const data = await getAssignedQuizzes()
        setAssignments(data)
      } catch {
        setAssignments([])
      } finally {
        setLoadingAssignments(false)
      }
    }
    loadAssignments()
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

  // Fetch the student-friendly skill map when subject/grade selection changes
  useEffect(() => {
    if (!selectedSubject || !selectedGrade) {
      setSkillMap([])
      return
    }

    async function loadSkillMap() {
      setLoadingSkillMap(true)
      try {
        const domains = await getSkillMap({
          subject_id: parseInt(selectedSubject),
          grade_id: parseInt(selectedGrade),
        })
        setSkillMap(domains)
      } catch {
        setSkillMap([])
      } finally {
        setLoadingSkillMap(false)
      }
    }
    loadSkillMap()
  }, [selectedSubject, selectedGrade])

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
  const recommendedSkill = skillMap.find((domain) => domain.recommended)

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

      <DailyGoalCard goal={dailyGoal} loading={loadingDailyGoal} />

      <AssignedQuizzesSection
        assignments={assignments}
        loading={loadingAssignments}
        onOpen={(assignmentId) => navigate(`/student/assigned-quiz/${assignmentId}`)}
      />

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

      {/* Skill Map */}
      {canStartQuiz && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="mb-8"
        >
          <h2 className="text-lg font-display font-semibold text-text mb-4 flex items-center gap-2">
            <Zap className="w-5 h-5 text-sage-600" />
            Skill Map
          </h2>
          {loadingSkillMap ? (
            <LoadingSpinner text="Loading skill map..." />
          ) : skillMap.length === 0 ? (
            <p className="text-text-muted font-body">No skill map found for this subject and grade.</p>
          ) : (
            <>
              {recommendedSkill && (
                <RecommendedSkillCard
                  domain={recommendedSkill}
                  onPractice={() => handleAdaptivePractice(recommendedSkill.domain_id, recommendedSkill.domain_name)}
                />
              )}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {skillMap.map((domain) => (
                  <SkillDomainCard
                    key={domain.domain_id}
                    domain={domain}
                    onPractice={() => handleAdaptivePractice(domain.domain_id, domain.domain_name)}
                  />
                ))}
              </div>
            </>
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

interface AssignedQuizzesSectionProps {
  assignments: QuizAssignmentSummary[]
  loading: boolean
  onOpen: (assignmentId: number) => void
}

function AssignedQuizzesSection({ assignments, loading, onOpen }: AssignedQuizzesSectionProps) {
  const visibleAssignments = assignments.slice(0, 4)

  if (loading) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.08 }}
        className="bg-surface-elevated rounded-2xl p-6 shadow-sm border border-border mb-8"
      >
        <div className="flex items-center gap-3 text-text-muted">
          <div className="w-5 h-5 border-2 border-sage-200 border-t-sage-600 rounded-full animate-spin" />
          <span className="font-display">Checking assigned quizzes...</span>
        </div>
      </motion.div>
    )
  }

  if (visibleAssignments.length === 0) {
    return null
  }

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.08 }}
      className="mb-8"
    >
      <div className="flex items-center gap-2 mb-4">
        <ClipboardList className="w-5 h-5 text-sage-600" />
        <h2 className="text-lg font-display font-semibold text-text">Assigned Quizzes</h2>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {visibleAssignments.map((assignment) => {
          const progress = assignment.question_count > 0
            ? Math.min(assignment.answered_count / assignment.question_count, 1)
            : 0
          const statusLabel = assignment.status.replace('_', ' ')
          const buttonLabel = assignment.status === 'completed'
            ? 'Review'
            : assignment.status === 'in_progress'
              ? 'Continue'
              : 'Start'

          return (
            <button
              key={assignment.id}
              onClick={() => onOpen(assignment.id)}
              className="bg-surface-elevated rounded-2xl border border-border p-5 text-left shadow-sm hover:border-sage-300 hover:shadow-md transition-all"
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="font-display font-semibold text-text">{assignment.title}</p>
                  <p className="mt-1 text-sm text-text-muted font-body">
                    {assignment.subject_name || 'Any subject'} - {assignment.question_count} questions
                  </p>
                </div>
                <span className="shrink-0 px-2.5 py-1 rounded-lg bg-sage-100 text-sage-700 text-xs font-display font-medium capitalize">
                  {statusLabel}
                </span>
              </div>

              <div className="mt-4">
                <div className="flex justify-between text-xs text-text-muted font-body mb-1">
                  <span>{assignment.answered_count} answered</span>
                  <span>{assignment.correct_count} correct</span>
                </div>
                <div className="h-2 bg-sage-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-sage-600 rounded-full transition-all duration-500"
                    style={{ width: `${Math.round(progress * 100)}%` }}
                  />
                </div>
              </div>

              <div className="mt-4 flex items-center justify-between gap-3">
                <span className="text-xs text-text-muted font-body capitalize">
                  {assignment.difficulty} difficulty
                </span>
                <span className="inline-flex items-center gap-1 text-sm font-display font-semibold text-sage-700">
                  {buttonLabel}
                  <ArrowRight className="w-4 h-4" />
                </span>
              </div>
            </button>
          )
        })}
      </div>
    </motion.section>
  )
}

interface DailyGoalCardProps {
  goal: DailyGoal | null
  loading: boolean
}

function DailyGoalCard({ goal, loading }: DailyGoalCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.05 }}
      className="bg-surface-elevated rounded-2xl p-6 shadow-sm border border-border mb-8"
    >
      <div className="flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
        <div className="flex items-start gap-4">
          <div className="p-3 rounded-xl bg-sage-100">
            <Target className="w-6 h-6 text-sage-600" />
          </div>
          <div>
            <p className="text-sm font-display font-medium text-text-muted">Today's Goal</p>
            <h2 className="text-2xl font-display font-semibold text-text">
              {loading ? 'Loading...' : goal?.completed ? 'Goal Complete' : `Answer ${goal?.target ?? 10} Questions`}
            </h2>
            <p className="mt-1 text-sm text-text-muted font-body">
              {loading ? 'Checking your practice today.' : goal?.message ?? 'Start a quiz to begin.'}
            </p>
          </div>
        </div>

        <div className="min-w-52">
          <div className="flex items-end justify-between mb-2">
            <span className="text-3xl font-display font-bold text-text">
              {goal?.answered_today ?? 0}
            </span>
            <span className="text-sm text-text-muted font-body">
              / {goal?.target ?? 10}
            </span>
          </div>
          <div className="h-3 bg-sage-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-sage-600 rounded-full transition-all duration-500"
              style={{ width: `${Math.round((goal?.progress ?? 0) * 100)}%` }}
            />
          </div>
          <p className="mt-2 text-xs text-text-muted font-body">
            {goal ? `${goal.correct_today} correct today` : 'Progress appears here'}
          </p>
        </div>
      </div>
    </motion.div>
  )
}

interface RecommendedSkillCardProps {
  domain: SkillMapDomain
  onPractice: () => void
}

function RecommendedSkillCard({ domain, onPractice }: RecommendedSkillCardProps) {
  return (
    <div className="bg-sage-700 text-white rounded-2xl p-5 shadow-sm mb-4 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
      <div>
        <p className="text-sm font-display font-medium text-sage-100">Recommended Next</p>
        <h3 className="mt-1 text-2xl font-display font-semibold">{domain.domain_name}</h3>
        <p className="mt-1 text-sm text-sage-100 font-body">{domain.recommendation_reason}</p>
      </div>
      <button
        onClick={onPractice}
        disabled={domain.active_questions === 0}
        className="flex items-center justify-center gap-2 px-5 py-3 bg-white text-sage-700 rounded-xl font-display font-semibold hover:bg-sage-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <Zap className="w-4 h-4" />
        Practice
      </button>
    </div>
  )
}

interface SkillDomainCardProps {
  domain: SkillMapDomain
  onPractice: () => void
}

function SkillDomainCard({ domain, onPractice }: SkillDomainCardProps) {
  const progressPct = Math.round(domain.progress * 100)
  const accuracyLabel = domain.accuracy == null ? 'New' : `${Math.round(domain.accuracy * 100)}%`
  const styles = getLevelStyles(domain.level)

  return (
    <div className="bg-surface-elevated rounded-2xl p-5 shadow-sm border border-border flex flex-col gap-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-display font-semibold text-text">{domain.domain_name}</p>
          <p className="text-sm text-text-muted font-body">{domain.domain_code}</p>
        </div>
        <div className={`px-2.5 py-1 rounded-lg text-xs font-display font-medium ${styles.badge}`}>
          {domain.level}
        </div>
      </div>

      <div className="space-y-1">
        <div className="flex justify-between text-xs text-text-muted font-body">
          <span>Progress</span>
          <span>{progressPct}%</span>
        </div>
        <div className="h-2 bg-sage-100 rounded-full overflow-hidden">
          <div
            className={`h-full ${styles.bar} rounded-full transition-all duration-500`}
            style={{ width: `${progressPct}%` }}
          />
        </div>
      </div>

      <p className="text-sm text-text-muted font-body min-h-10">{domain.level_description}</p>

      <div className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <p className="text-text-muted font-body">Attempted</p>
          <p className="font-display font-semibold text-text">{domain.questions_attempted}</p>
        </div>
        <div>
          <p className="text-text-muted font-body">Accuracy</p>
          <p className="font-display font-semibold text-text">{accuracyLabel}</p>
        </div>
      </div>

      <div className="mt-auto flex items-center justify-between gap-3">
        <span className="text-xs text-text-muted font-body">
          {domain.active_questions > 0 ? `${domain.active_questions} questions ready` : 'No questions yet'}
        </span>
        <button
          onClick={onPractice}
          disabled={domain.active_questions === 0}
          className="flex items-center gap-1.5 px-4 py-2 bg-sage-600 text-white rounded-lg font-display font-medium text-sm hover:bg-sage-700 transition-colors shadow-sm hover:shadow-md disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <Zap className="w-3.5 h-3.5" />
          Practice
        </button>
      </div>
    </div>
  )
}

function getLevelStyles(level: string): { badge: string; bar: string } {
  if (level === 'Mastered') {
    return { badge: 'bg-sage-100 text-sage-800', bar: 'bg-sage-700' }
  }
  if (level === 'Strong') {
    return { badge: 'bg-sage-100 text-sage-700', bar: 'bg-sage-600' }
  }
  if (level === 'Improving') {
    return { badge: 'bg-coral-100 text-coral-700', bar: 'bg-coral-500' }
  }
  if (level === 'Building') {
    return { badge: 'bg-sage-100 text-sage-700', bar: 'bg-sage-400' }
  }
  return { badge: 'bg-coral-100 text-coral-700', bar: 'bg-coral-400' }
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
