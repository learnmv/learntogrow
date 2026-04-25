import { useState, useEffect, useCallback, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ArrowLeft, ArrowRight, BookOpen, RotateCcw, CheckCircle, XCircle, RefreshCw } from 'lucide-react'
import { fetchStandards } from '../services/standards'
import { fetchQuestionsByStandard } from '../services/questions'
import { recordAnswer } from '../services/student'
import { useAuth } from '../contexts/AuthContext'
import { cn, renderMathToHtml } from '../lib/utils'
import { GeoGebraApplet } from './geogebra/GeoGebraApplet'
import type { Standard } from '../types/standards'
import type { QuestionFromDB } from '../types/questions'

interface QuizProps {
  subjectId: string
  gradeId: string
  onExit: () => void
  standards?: Standard[]  // Pre-loaded standards (for mistakes mode)
}

// Storage key for quiz progress
const PROGRESS_KEY = 'learntogrow_quiz_progress'
const PROGRESS_EXPIRY_MS = 24 * 60 * 60 * 1000 // 24 hours

interface SavedProgress {
  subjectId: string
  gradeId: string
  currentIndex: number
  answers: Record<number, { selected: string; correct: boolean }>
  timestamp: number
}

export function Quiz({ subjectId, gradeId, onExit, standards: standardsProp }: QuizProps) {
  const { isAuthenticated } = useAuth()
  const [standards, setStandards] = useState<Standard[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [currentQuestion, setCurrentQuestion] = useState<QuestionFromDB | null>(null)
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null)
  const [showResult, setShowResult] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [generatingQuestion, setGeneratingQuestion] = useState(false)
  const [retryCount, setRetryCount] = useState(0)
  const [answers, setAnswers] = useState<Record<number, { selected: string; correct: boolean }>>({})

  // Cache loaded questions by index so navigation back shows the same question
  const questionMap = useRef<Record<number, QuestionFromDB>>({})

  // Fetch standards on mount (only if not pre-loaded)
  useEffect(() => {
    if (standardsProp && standardsProp.length > 0) {
      setStandards(standardsProp)
      setLoading(false)
      return
    }

    async function loadStandards() {
      try {
        const standardsList = await fetchStandards({
          subject_id: parseInt(subjectId),
          grade_id: parseInt(gradeId),
        })
        setStandards(standardsList)
        setLoading(false)
      } catch {
        setError('Failed to load standards')
        setLoading(false)
      }
    }

    loadStandards()
  }, [subjectId, gradeId, standardsProp])

  // Load progress from localStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem(PROGRESS_KEY)
      if (saved) {
        const progress: SavedProgress = JSON.parse(saved)
        if (progress.subjectId === subjectId && progress.gradeId === gradeId) {
          const age = Date.now() - progress.timestamp
          if (age < PROGRESS_EXPIRY_MS) {
            setCurrentIndex(progress.currentIndex)
            setAnswers(progress.answers)
          }
        }
      }
    } catch (e) {
      console.warn('Failed to load saved progress:', e)
    }
  }, [subjectId, gradeId])

  // Debounced save progress to localStorage
  const pendingSaveRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  useEffect(() => {
    if (!loading && standards.length > 0) {
      if (pendingSaveRef.current) {
        clearTimeout(pendingSaveRef.current)
      }
      pendingSaveRef.current = setTimeout(() => {
        const progress: SavedProgress = {
          subjectId,
          gradeId,
          currentIndex,
          answers,
          timestamp: Date.now()
        }
        try {
          localStorage.setItem(PROGRESS_KEY, JSON.stringify(progress))
        } catch (e) {
          console.warn('Failed to save progress:', e)
        }
      }, 500)
    }
    return () => {
      if (pendingSaveRef.current) {
        clearTimeout(pendingSaveRef.current)
      }
    }
  }, [currentIndex, answers, subjectId, gradeId, loading, standards.length])

  // Load question when currentIndex or standards change.
  const loadQuestion = useCallback(async (isRetry = false) => {
    if (standards.length === 0) return

    const cached = questionMap.current[currentIndex]
    if (cached && !isRetry) {
      setCurrentQuestion(cached)
      return
    }

    setGeneratingQuestion(true)
    setError(null)
    if (!isRetry) {
      setRetryCount(0)
    }

    try {
      const questions = await fetchQuestionsByStandard(standards[currentIndex].id, 1)
      const question = questions[0] || null

      if (!question) {
        setError('No questions available for this standard.')
        setCurrentQuestion(null)
        return
      }

      questionMap.current[currentIndex] = question
      setCurrentQuestion(question)
    } catch (err) {
      console.error('Failed to load questions:', err)
      setError('Failed to load questions. Please try again.')
    } finally {
      setGeneratingQuestion(false)
    }
  }, [standards, currentIndex])

  useEffect(() => {
    loadQuestion()
  }, [loadQuestion])

  // Restore saved answer state on index change (separate from question fetch)
  useEffect(() => {
    const savedAnswer = answers[currentIndex]
    if (savedAnswer) {
      setSelectedAnswer(savedAnswer.selected)
      setShowResult(true)
    } else {
      setSelectedAnswer(null)
      setShowResult(false)
    }
  }, [currentIndex, answers])

  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1)
    }
  }

  const handleNext = () => {
    if (currentIndex < standards.length - 1) {
      setCurrentIndex(currentIndex + 1)
    }
  }

  const handleRetry = async () => {
    setRetryCount(prev => prev + 1)
    delete questionMap.current[currentIndex]
    await loadQuestion(true)
  }

  const handleAnswerSelect = async (value: string) => {
    if (!currentQuestion) return

    setSelectedAnswer(value)
    setShowResult(true)

    const isCorrect = value === currentQuestion.correct_answer
    setAnswers(prev => ({
      ...prev,
      [currentIndex]: { selected: value, correct: isCorrect }
    }))

    if (isAuthenticated) {
      try {
        await recordAnswer({
          question_id: currentQuestion.id,
          selected_answer: value,
          is_correct: isCorrect,
        })
      } catch (err) {
        console.error('Failed to record answer:', err)
      }
    }
  }

  const handleExit = () => {
    try {
      localStorage.removeItem(PROGRESS_KEY)
    } catch (e) {
      console.warn('Failed to clear progress:', e)
    }
    onExit()
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-sage-200 border-t-sage-600 rounded-full animate-spin mx-auto" />
          <p className="mt-6 font-display text-text-muted">Loading standards...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center px-6">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 bg-coral-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <XCircle className="w-8 h-8 text-coral-600" />
          </div>
          <p className="text-coral-600 font-display text-lg mb-2">{error}</p>
          {retryCount > 0 && (
            <p className="text-text-muted text-sm mb-4">
              Retry attempt {retryCount}/3
            </p>
          )}
          <div className="flex gap-3 justify-center">
            <button
              onClick={handleRetry}
              disabled={generatingQuestion}
              className="flex items-center gap-2 px-6 py-3 bg-sage-600 text-white rounded-xl font-display font-medium hover:bg-sage-700 transition-colors disabled:opacity-50"
            >
              {generatingQuestion ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Loading...
                </>
              ) : (
                <>
                  <RefreshCw className="w-4 h-4" />
                  Try Again
                </>
              )}
            </button>
            <button
              onClick={handleExit}
              className="px-6 py-3 border-2 border-sage-200 text-sage-700 rounded-xl font-display font-medium hover:bg-sage-50 transition-colors"
            >
              Exit Quiz
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (standards.length === 0) {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center px-6">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 bg-sage-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <BookOpen className="w-8 h-8 text-sage-600" />
          </div>
          <p className="text-text font-display text-lg mb-2">No Standards Found</p>
          <p className="text-text-muted mb-6">No standards were found for the selected subject and grade.</p>
          <button
            onClick={onExit}
            className="px-6 py-3 bg-sage-600 text-white rounded-xl font-display font-medium hover:bg-sage-700 transition-colors"
          >
            Go Back
          </button>
        </div>
      </div>
    )
  }

  const currentStandard = standards[currentIndex]
  const progress = ((currentIndex + 1) / standards.length) * 100

  return (
    <div className="min-h-screen bg-gradient-to-b from-sage-50 via-surface to-surface py-8 px-4">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between mb-8"
        >
          <button
            onClick={handleExit}
            className="flex items-center gap-2 text-text-muted hover:text-text transition-colors font-display"
          >
            <RotateCcw className="w-4 h-4" />
            Exit Quiz
          </button>

          <div className="flex items-center gap-3">
            <BookOpen className="w-5 h-5 text-sage-600" />
            <span className="font-display font-medium text-text">
              Question {currentIndex + 1} of {standards.length}
            </span>
          </div>
        </motion.div>

        {/* Progress Bar */}
        <motion.div
          initial={{ scaleX: 0 }}
          animate={{ scaleX: 1 }}
          className="h-2 bg-sage-100 rounded-full mb-8 overflow-hidden"
        >
          <motion.div
            className="h-full bg-gradient-to-r from-sage-500 to-sage-600 rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          />
        </motion.div>

        {/* Question Card — STATIC shell, animated inner content */}
        <div className="bg-surface-elevated rounded-3xl p-8 shadow-lg shadow-sage-100/50 border border-border">
          {/* Standard Info — static, updates without animation */}
          {currentStandard && (
            <div className="flex items-center gap-3 mb-6">
              <span className="px-3 py-1 bg-sage-100 text-sage-700 font-display font-medium text-sm rounded-full">
                {currentStandard?.code}
              </span>
              <span className="text-text-muted text-sm">
                Difficulty: {Math.round((currentStandard?.difficulty_base || 0) * 100)}%
              </span>
            </div>
          )}

          {/* Diagram — PERSISTENT, inside the static card shell.
              Never unmounts; only receives new commands when question changes.
              Fades out during loading so the old diagram doesn't linger
              while the next question is being fetched. */}
          {currentQuestion?.applet_type && (
            <div
              className={cn(
                'mb-6 flex justify-center transition-opacity duration-300',
                generatingQuestion && 'opacity-0 pointer-events-none'
              )}
            >
              <GeoGebraApplet
                appletType={currentQuestion.applet_type as 'graphing' | 'geometry' | '3d' | 'classic'}
                commands={currentQuestion.geogebra_commands || undefined}
                height={400}
                width={600}
              />
            </div>
          )}

          {/* Inner content — ANIMATED via AnimatePresence */}
          <AnimatePresence mode="wait">
            {generatingQuestion ? (
              <motion.div
                key="loading"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="min-h-[200px] flex items-center justify-center"
              >
                <div className="text-center">
                  <div className="w-12 h-12 border-4 border-sage-200 border-t-sage-600 rounded-full animate-spin mx-auto mb-4" />
                  <p className="text-text-muted font-display">Loading question...</p>
                </div>
              </motion.div>
            ) : currentQuestion ? (
              <motion.div
                key={`content-${currentQuestion.id}`}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
              >
                {/* Question Text */}
                <h2
                  className="font-display text-2xl font-semibold text-text mb-6 leading-relaxed"
                  dangerouslySetInnerHTML={{ __html: renderMathToHtml(currentQuestion.question_text) }}
                />

                {/* Options */}
                <div className="space-y-3">
                  {(currentQuestion.options || []).map((option, index) => {
                    const isSelected = selectedAnswer === option
                    const isCorrectAnswer = option === currentQuestion.correct_answer
                    const showCorrectness = showResult && (isSelected || isCorrectAnswer)

                    return (
                      <motion.button
                        key={index}
                        onClick={() => !showResult && handleAnswerSelect(option)}
                        disabled={showResult}
                        whileHover={!showResult ? { scale: 1.02 } : {}}
                        whileTap={!showResult ? { scale: 0.98 } : {}}
                        className={cn(
                          'w-full p-4 rounded-2xl border-2 text-left transition-all duration-200',
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
                              'w-8 h-8 rounded-xl flex items-center justify-center font-display font-semibold text-sm',
                              showCorrectness && isCorrectAnswer && 'bg-green-500 text-white',
                              showCorrectness && isSelected && !isCorrectAnswer && 'bg-coral-500 text-white',
                              showCorrectness && !isSelected && !isCorrectAnswer && 'bg-surface-muted text-text-muted',
                              !showCorrectness && isSelected && 'bg-sage-500 text-white',
                              !showCorrectness && !isSelected && 'bg-sage-100 text-sage-700'
                            )}
                          >
                            {String.fromCharCode(65 + index)}
                          </span>
                          <span className="font-body text-text text-lg" dangerouslySetInnerHTML={{ __html: renderMathToHtml(option) }} />
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

                {/* Explanation */}
                <AnimatePresence>
                  {showResult && currentQuestion.explanation && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="mt-6 p-4 bg-sage-50 rounded-2xl border border-sage-200"
                    >
                      <p className="font-display font-medium text-sage-700 mb-2">Explanation</p>
                      <p
                        className="text-text-muted font-body"
                        dangerouslySetInnerHTML={{ __html: renderMathToHtml(currentQuestion.explanation) }}
                      />
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            ) : null}
          </AnimatePresence>
        </div>

        {/* Navigation */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="flex items-center justify-between mt-8"
        >
          <button
            onClick={handlePrevious}
            disabled={currentIndex === 0}
            className="flex items-center gap-2 px-6 py-3 rounded-xl font-display font-medium transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed text-text-muted hover:text-text hover:bg-surface-elevated"
          >
            <ArrowLeft className="w-4 h-4" />
            Previous
          </button>

          <div className="flex gap-2">
            {standards.slice(0, Math.min(10, standards.length)).map((_, idx) => (
              <button
                key={idx}
                onClick={() => setCurrentIndex(idx)}
                className={cn(
                  'w-2 h-2 rounded-full transition-all duration-200',
                  idx === currentIndex && 'bg-sage-600 w-6',
                  idx < currentIndex && idx !== currentIndex && 'bg-sage-300',
                  idx > currentIndex && 'bg-sage-100'
                )}
              />
            ))}
            {standards.length > 10 && (
              <span className="text-text-muted text-sm ml-1">...</span>
            )}
          </div>

          <button
            onClick={handleNext}
            disabled={currentIndex === standards.length - 1}
            className="flex items-center gap-2 px-6 py-3 bg-sage-600 text-white rounded-xl font-display font-medium hover:bg-sage-700 transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed shadow-lg shadow-sage-200 hover:shadow-xl hover:-translate-y-0.5"
          >
            Next
            <ArrowRight className="w-4 h-4" />
          </button>
        </motion.div>
      </div>
    </div>
  )
}
