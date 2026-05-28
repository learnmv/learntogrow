import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowLeft, ArrowRight, CheckCircle, ClipboardList, RotateCcw, XCircle } from 'lucide-react'
import { DiagramRenderer } from '../../components/DiagramRenderer'
import { GeoGebraApplet } from '../../components/geogebra/GeoGebraApplet'
import { QuestionStimulus } from '../../components/QuestionStimulus'
import { LoadingSpinner } from '../../components/ui/LoadingSpinner'
import { cn, renderMathToHtml } from '../../lib/utils'
import {
  completeAssignedQuiz,
  getAssignedQuiz,
  recordAnswer,
  startAssignedQuiz,
} from '../../services/student'
import type { QuizAssignmentDetail } from '../../types/quizAssignment'
import type { QuestionFromDB } from '../../types/questions'

interface LocalAnswer {
  selected: string
  correct: boolean
}

function getLocalAnswers(assignment: QuizAssignmentDetail): Record<number, LocalAnswer> {
  return assignment.answers.reduce<Record<number, LocalAnswer>>((result, answer) => {
    if (answer.selected_answer !== null) {
      result[answer.question_id] = {
        selected: answer.selected_answer,
        correct: answer.is_correct,
      }
    }
    return result
  }, {})
}

export function AssignedQuizPage() {
  const { assignmentId } = useParams()
  const navigate = useNavigate()
  const [assignment, setAssignment] = useState<QuizAssignmentDetail | null>(null)
  const [currentIndex, setCurrentIndex] = useState(0)
  const [answers, setAnswers] = useState<Record<number, LocalAnswer>>({})
  const [loading, setLoading] = useState(true)
  const [completing, setCompleting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [complete, setComplete] = useState(false)

  const numericAssignmentId = Number(assignmentId)
  const currentQuestion = assignment?.questions[currentIndex] ?? null
  const savedAnswer = answers[currentQuestion?.id ?? -1]
  const selectedAnswer = savedAnswer?.selected ?? null
  const showResult = Boolean(savedAnswer)

  useEffect(() => {
    async function loadAssignment() {
      if (!assignmentId || Number.isNaN(numericAssignmentId)) {
        setError('Assigned quiz not found.')
        setLoading(false)
        return
      }

      try {
        let data = await getAssignedQuiz(numericAssignmentId)
        if (data.status === 'assigned') {
          data = await startAssignedQuiz(numericAssignmentId)
        }
        setAssignment(data)
        setAnswers(getLocalAnswers(data))
        setComplete(data.status === 'completed')
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Failed to load assigned quiz.')
      } finally {
        setLoading(false)
      }
    }

    loadAssignment()
  }, [assignmentId, numericAssignmentId])

  const score = useMemo(() => {
    return Object.values(answers).filter((answer) => answer.correct).length
  }, [answers])

  async function handleAnswerSelect(question: QuestionFromDB, value: string) {
    if (answers[question.id]) return

    const isCorrect = value === question.correct_answer
    setAnswers((previous) => ({
      ...previous,
      [question.id]: { selected: value, correct: isCorrect },
    }))

    try {
      await recordAnswer({
        question_id: question.id,
        selected_answer: value,
        is_correct: isCorrect,
      })
    } catch (err) {
      console.error('Failed to record assigned quiz answer:', err)
    }
  }

  async function handleFinish() {
    if (!assignment) return

    setCompleting(true)
    try {
      const data = await completeAssignedQuiz(assignment.id)
      setAssignment(data)
      setAnswers(getLocalAnswers(data))
      setComplete(true)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to finish quiz.')
    } finally {
      setCompleting(false)
    }
  }

  if (loading) {
    return <LoadingSpinner text="Loading assigned quiz..." />
  }

  if (error || !assignment) {
    return (
      <div className="max-w-3xl mx-auto text-center py-16">
        <XCircle className="w-12 h-12 text-coral-600 mx-auto mb-3" />
        <p className="text-coral-600 font-display text-lg">{error || 'Assigned quiz not found.'}</p>
        <button
          onClick={() => navigate('/student')}
          className="mt-4 px-6 py-2 bg-sage-600 text-white rounded-xl font-display font-medium hover:bg-sage-700 transition-colors"
        >
          Go to Dashboard
        </button>
      </div>
    )
  }

  if (assignment.questions.length === 0) {
    return (
      <div className="max-w-3xl mx-auto text-center py-16">
        <ClipboardList className="w-12 h-12 text-sage-600 mx-auto mb-3" />
        <p className="text-text font-display text-lg">No questions are attached to this quiz.</p>
        <button
          onClick={() => navigate('/student')}
          className="mt-4 px-6 py-2 bg-sage-600 text-white rounded-xl font-display font-medium hover:bg-sage-700 transition-colors"
        >
          Go to Dashboard
        </button>
      </div>
    )
  }

  if (complete) {
    const total = assignment.questions.length
    const finalScore = assignment.correct_count || score

    return (
      <div className="max-w-3xl mx-auto py-12">
        <div className="bg-surface-elevated rounded-2xl border border-border p-8 text-center shadow-sm">
          <CheckCircle className="w-14 h-14 text-sage-600 mx-auto mb-4" />
          <p className="text-sm font-display font-medium text-text-muted">Quiz Complete</p>
          <h1 className="mt-2 text-3xl font-display font-semibold text-text">{assignment.title}</h1>
          <p className="mt-4 text-5xl font-display font-bold text-sage-700">
            {finalScore}/{total}
          </p>
          <p className="mt-2 text-text-muted font-body">
            Nice work. Your parent can now see this assignment progress.
          </p>
          <button
            onClick={() => navigate('/student')}
            className="mt-6 px-6 py-3 bg-sage-600 text-white rounded-xl font-display font-semibold hover:bg-sage-700 transition-colors"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    )
  }

  const progress = ((currentIndex + 1) / assignment.questions.length) * 100
  const allAnswered = assignment.questions.every((question) => answers[question.id])

  return (
    <div className="max-w-3xl mx-auto py-8">
      <div className="flex items-center justify-between gap-4 mb-6">
        <button
          onClick={() => navigate('/student')}
          className="flex items-center gap-2 text-text-muted hover:text-text transition-colors font-display"
        >
          <RotateCcw className="w-4 h-4" />
          Exit
        </button>
        <div className="flex items-center gap-2 text-text">
          <ClipboardList className="w-5 h-5 text-sage-600" />
          <span className="font-display font-medium">
            Question {currentIndex + 1} of {assignment.questions.length}
          </span>
        </div>
      </div>

      <div className="h-2 bg-sage-100 rounded-full mb-6 overflow-hidden">
        <div
          className="h-full bg-sage-600 rounded-full transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>

      <div className="bg-surface-elevated rounded-2xl p-6 md:p-8 shadow-sm border border-border">
        <div className="mb-6">
          <p className="text-sm font-display font-medium text-sage-700">{assignment.title}</p>
          <QuestionStimulus
            questionText={currentQuestion?.question_text ?? ''}
            stimulus={currentQuestion?.stimulus}
            questionClassName="mt-2 font-display text-2xl font-semibold text-text leading-relaxed"
          />
        </div>

        {currentQuestion?.diagram_spec ? (
          <DiagramRenderer diagram={currentQuestion.diagram_spec} className="mb-6" />
        ) : currentQuestion?.applet_type ? (
          <div className="mb-6 flex justify-center">
            <GeoGebraApplet
              appletType={currentQuestion.applet_type as 'graphing' | 'geometry' | '3d' | 'classic'}
              commands={currentQuestion.geogebra_commands || undefined}
              height={400}
              width={600}
            />
          </div>
        ) : null}

        <div className="space-y-3">
          {(currentQuestion?.options || []).map((option, index) => {
            const isSelected = selectedAnswer === option
            const isCorrectAnswer = option === currentQuestion?.correct_answer
            const showCorrectness = showResult && (isSelected || isCorrectAnswer)

            return (
              <motion.button
                key={option}
                onClick={() => currentQuestion && handleAnswerSelect(currentQuestion, option)}
                disabled={showResult}
                whileHover={!showResult ? { scale: 1.01 } : {}}
                whileTap={!showResult ? { scale: 0.99 } : {}}
                className={cn(
                  'w-full p-4 rounded-xl border-2 text-left transition-all duration-200',
                  showCorrectness && isCorrectAnswer && 'border-green-500 bg-green-50',
                  showCorrectness && isSelected && !isCorrectAnswer && 'border-coral-500 bg-coral-50',
                  showCorrectness && !isSelected && !isCorrectAnswer && 'border-border bg-surface-muted',
                  !showCorrectness && isSelected && 'border-sage-500 bg-sage-50',
                  !showCorrectness && !isSelected && 'border-border hover:border-sage-300 hover:bg-sage-50/50'
                )}
              >
                <div className="flex items-center gap-4">
                  <span
                    className={cn(
                      'w-8 h-8 rounded-lg flex items-center justify-center font-display font-semibold text-sm',
                      showCorrectness && isCorrectAnswer && 'bg-green-500 text-white',
                      showCorrectness && isSelected && !isCorrectAnswer && 'bg-coral-500 text-white',
                      showCorrectness && !isSelected && !isCorrectAnswer && 'bg-surface-muted text-text-muted',
                      !showCorrectness && isSelected && 'bg-sage-500 text-white',
                      !showCorrectness && !isSelected && 'bg-sage-100 text-sage-700'
                    )}
                  >
                    {String.fromCharCode(65 + index)}
                  </span>
                  <span
                    className="font-body text-text text-lg"
                    dangerouslySetInnerHTML={{ __html: renderMathToHtml(option) }}
                  />
                  {showCorrectness && isCorrectAnswer && (
                    <CheckCircle className="w-5 h-5 text-green-500 ml-auto" />
                  )}
                  {showCorrectness && isSelected && !isCorrectAnswer && (
                    <XCircle className="w-5 h-5 text-coral-500 ml-auto" />
                  )}
                </div>
              </motion.button>
            )
          })}
        </div>

        {showResult && currentQuestion?.explanation && (
          <div className="mt-6 p-4 bg-sage-50 rounded-xl border border-sage-200">
            <p className="font-display font-medium text-sage-700 mb-2">Explanation</p>
            <p
              className="text-text-muted font-body"
              dangerouslySetInnerHTML={{ __html: renderMathToHtml(currentQuestion.explanation) }}
            />
          </div>
        )}
      </div>

      <div className="flex items-center justify-between mt-8">
        <button
          onClick={() => setCurrentIndex((index) => Math.max(index - 1, 0))}
          disabled={currentIndex === 0}
          className="flex items-center gap-2 px-6 py-3 rounded-xl font-display font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed text-text-muted hover:text-text hover:bg-surface-elevated"
        >
          <ArrowLeft className="w-4 h-4" />
          Previous
        </button>

        {currentIndex === assignment.questions.length - 1 ? (
          <button
            onClick={handleFinish}
            disabled={!allAnswered || completing}
            className="flex items-center gap-2 px-6 py-3 bg-sage-600 text-white rounded-xl font-display font-semibold hover:bg-sage-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {completing ? 'Finishing...' : 'Finish Quiz'}
          </button>
        ) : (
          <button
            onClick={() => setCurrentIndex((index) => Math.min(index + 1, assignment.questions.length - 1))}
            className="flex items-center gap-2 px-6 py-3 bg-sage-600 text-white rounded-xl font-display font-semibold hover:bg-sage-700 transition-colors"
          >
            Next
            <ArrowRight className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  )
}
