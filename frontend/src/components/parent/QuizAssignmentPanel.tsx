import { useEffect, useState } from 'react'
import { ClipboardList, Loader2, Plus, RefreshCw, Sparkles } from 'lucide-react'
import { fetchGrades, fetchSubjects } from '../../services/standards'
import { createQuizAssignment, getParentQuizAssignments } from '../../services/parent'
import type { Grade, Subject } from '../../types/standards'
import type { ParentStudentLink } from '../../types/parent'
import type {
  QuizAssignmentDifficulty,
  QuizAssignmentSummary,
} from '../../types/quizAssignment'

interface QuizAssignmentPanelProps {
  childrenList: ParentStudentLink[]
  refreshKey?: number
}

export function QuizAssignmentPanel({ childrenList, refreshKey = 0 }: QuizAssignmentPanelProps) {
  const [assignments, setAssignments] = useState<QuizAssignmentSummary[]>([])
  const [subjects, setSubjects] = useState<Subject[]>([])
  const [grades, setGrades] = useState<Grade[]>([])
  const [studentId, setStudentId] = useState('')
  const [subjectId, setSubjectId] = useState('')
  const [gradeId, setGradeId] = useState('')
  const [title, setTitle] = useState('Practice Quiz')
  const [description, setDescription] = useState('')
  const [difficulty, setDifficulty] = useState<QuizAssignmentDifficulty>('medium')
  const [questionCount, setQuestionCount] = useState(5)
  const [generateMissing, setGenerateMissing] = useState(false)
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [message, setMessage] = useState<string | null>(null)

  useEffect(() => {
    if (!studentId && childrenList.length === 1) {
      setStudentId(String(childrenList[0].student_id))
    }
  }, [childrenList, studentId])

  useEffect(() => {
    async function loadInitialData() {
      setLoading(true)
      try {
        const [subjectData, assignmentData] = await Promise.all([
          fetchSubjects(),
          getParentQuizAssignments(),
        ])
        setSubjects(subjectData)
        setAssignments(assignmentData)
      } catch (error: unknown) {
        setMessage(error instanceof Error ? error.message : 'Failed to load quiz assignments.')
      } finally {
        setLoading(false)
      }
    }

    loadInitialData()
  }, [])

  useEffect(() => {
    if (!subjectId) {
      setGrades([])
      setGradeId('')
      return
    }

    async function loadGrades() {
      try {
        const data = await fetchGrades(Number(subjectId))
        setGrades(data)
      } catch {
        setGrades([])
      }
    }

    loadGrades()
  }, [subjectId])

  useEffect(() => {
    if (refreshKey > 0) {
      getParentQuizAssignments()
        .then(setAssignments)
        .catch((error: unknown) => {
          setMessage(error instanceof Error ? error.message : 'Failed to refresh assignments.')
        })
    }
  }, [refreshKey])

  async function refreshAssignments() {
    try {
      const data = await getParentQuizAssignments()
      setAssignments(data)
    } catch (error: unknown) {
      setMessage(error instanceof Error ? error.message : 'Failed to refresh assignments.')
    }
  }

  async function handleCreateAssignment() {
    if (!studentId || !title.trim()) return

    setCreating(true)
    setMessage(null)
    try {
      await createQuizAssignment({
        student_id: Number(studentId),
        title: title.trim(),
        description: description.trim() || undefined,
        subject_id: subjectId ? Number(subjectId) : undefined,
        grade_id: gradeId ? Number(gradeId) : undefined,
        difficulty,
        question_count: questionCount,
        generate_missing: generateMissing,
      })
      await refreshAssignments()
      setMessage('Quiz assigned successfully.')
    } catch (error: unknown) {
      setMessage(error instanceof Error ? error.message : 'Failed to assign quiz.')
    } finally {
      setCreating(false)
    }
  }

  return (
    <section className="bg-surface-elevated border border-border rounded-2xl p-6 mb-8 shadow-sm">
      <div className="flex items-start justify-between gap-4 mb-5">
        <div>
          <div className="flex items-center gap-2">
            <ClipboardList className="w-5 h-5 text-sage-600" />
            <h2 className="text-lg font-display font-semibold text-text">Assign a Quiz</h2>
          </div>
          <p className="mt-1 text-sm text-text-muted">
            Create a short quiz from existing questions and post it to your child&apos;s dashboard.
          </p>
        </div>
        <button
          onClick={refreshAssignments}
          className="p-2 rounded-lg text-text-muted hover:text-text hover:bg-sage-50 transition-colors"
          aria-label="Refresh assignments"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
        <select
          value={studentId}
          onChange={(event) => setStudentId(event.target.value)}
          className="h-11 px-3 bg-surface border border-border rounded-xl text-sm text-text focus:outline-none focus:ring-2 focus:ring-sage-500"
        >
          <option value="">Select child</option>
          {childrenList.map((child) => (
            <option key={child.student_id} value={child.student_id}>
              {child.student_name}
            </option>
          ))}
        </select>

        <select
          value={subjectId}
          onChange={(event) => {
            setSubjectId(event.target.value)
            setGradeId('')
          }}
          className="h-11 px-3 bg-surface border border-border rounded-xl text-sm text-text focus:outline-none focus:ring-2 focus:ring-sage-500"
        >
          <option value="">Any subject</option>
          {subjects.map((subject) => (
            <option key={subject.id} value={subject.id}>
              {subject.name}
            </option>
          ))}
        </select>

        <select
          value={gradeId}
          onChange={(event) => setGradeId(event.target.value)}
          disabled={!subjectId}
          className="h-11 px-3 bg-surface border border-border rounded-xl text-sm text-text focus:outline-none focus:ring-2 focus:ring-sage-500 disabled:opacity-60"
        >
          <option value="">Any grade</option>
          {grades.map((grade) => (
            <option key={grade.id} value={grade.id}>
              {grade.display_name}
            </option>
          ))}
        </select>

        <select
          value={difficulty}
          onChange={(event) => setDifficulty(event.target.value as QuizAssignmentDifficulty)}
          className="h-11 px-3 bg-surface border border-border rounded-xl text-sm text-text focus:outline-none focus:ring-2 focus:ring-sage-500"
        >
          <option value="easy">Easy</option>
          <option value="medium">Medium</option>
          <option value="hard">Hard</option>
          <option value="mixed">Mixed</option>
        </select>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-[1fr_1fr_auto] gap-3 mt-3">
        <input
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          className="h-11 px-3 bg-surface border border-border rounded-xl text-sm text-text focus:outline-none focus:ring-2 focus:ring-sage-500"
          placeholder="Quiz title"
        />
        <input
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          className="h-11 px-3 bg-surface border border-border rounded-xl text-sm text-text focus:outline-none focus:ring-2 focus:ring-sage-500"
          placeholder="Optional note"
        />
        <div className="flex gap-3">
          <input
            type="number"
            min={1}
            max={25}
            value={questionCount}
            onChange={(event) => {
              const nextCount = Number(event.target.value)
              setQuestionCount(Number.isFinite(nextCount) ? Math.max(1, Math.min(25, nextCount)) : 1)
            }}
            className="h-11 w-24 px-3 bg-surface border border-border rounded-xl text-sm text-text focus:outline-none focus:ring-2 focus:ring-sage-500"
            aria-label="Question count"
          />
          <button
            onClick={handleCreateAssignment}
            disabled={!studentId || !title.trim() || creating}
            className="h-11 px-4 bg-sage-600 text-white rounded-xl font-display font-semibold hover:bg-sage-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
            Assign
          </button>
        </div>
      </div>

      <label className="mt-3 flex items-center gap-2 text-sm text-text-muted">
        <input
          type="checkbox"
          checked={generateMissing}
          onChange={(event) => setGenerateMissing(event.target.checked)}
          className="h-4 w-4 rounded border-border text-sage-600 focus:ring-sage-500"
        />
        <Sparkles className="w-4 h-4 text-sage-600" />
        AI-fill missing questions when the question bank is short
      </label>

      {message && (
        <p className="mt-3 text-sm text-text-muted">{message}</p>
      )}

      <div className="mt-6">
        <h3 className="text-sm font-display font-semibold text-text mb-3">Recent Assignments</h3>
        {loading ? (
          <div className="flex items-center gap-2 text-sm text-text-muted">
            <Loader2 className="w-4 h-4 animate-spin" />
            Loading assignments...
          </div>
        ) : assignments.length === 0 ? (
          <p className="text-sm text-text-muted">No assigned quizzes yet.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {assignments.slice(0, 4).map((assignment) => (
              <div key={assignment.id} className="border border-border rounded-xl p-4 bg-surface">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-display font-semibold text-text">{assignment.title}</p>
                    <p className="text-xs text-text-muted">
                      {assignment.student_name} - {assignment.question_count} questions - {assignment.difficulty}
                    </p>
                  </div>
                  <span className="text-xs px-2 py-1 rounded-lg bg-sage-100 text-sage-700 font-display">
                    {assignment.status.replace('_', ' ')}
                  </span>
                </div>
                <p className="mt-2 text-xs text-text-muted">
                  {assignment.answered_count}/{assignment.question_count} answered
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  )
}
