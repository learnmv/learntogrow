import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ArrowRight, RotateCcw, CheckCircle, XCircle, RefreshCw, Target } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { cn, getFriendlySkillLevel, renderMathToHtml } from '../lib/utils'
import { GeoGebraApplet } from './geogebra/GeoGebraApplet'
import { fetchAdaptiveQuestion, recordAdaptiveAnswer } from '../services/adaptive'
import type { QuestionFromDB } from '../types/questions'

interface AdaptiveQuizProps {
  domainId: string
  domainName?: string
  onExit: () => void
}

export function AdaptiveQuiz({ domainId, domainName, onExit }: AdaptiveQuizProps) {
  const { isAuthenticated } = useAuth()

  const [currentQuestion, setCurrentQuestion] = useState<QuestionFromDB | null>(null)
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null)
  const [showResult, setShowResult] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [retryCount, setRetryCount] = useState(0)

  const [questionCount, setQuestionCount] = useState(0)
  const [correctCount, setCorrectCount] = useState(0)
  const [answeredCount, setAnsweredCount] = useState(0)
  const [theta, setTheta] = useState<number | null>(null)

  const loadNextQuestion = useCallback(async (isRetry = false) => {
    setLoading(true)
    setError(null)
    setSelectedAnswer(null)
    setShowResult(false)
    if (!isRetry) setRetryCount(0)

    try {
      const question = await fetchAdaptiveQuestion(parseInt(domainId))
      setCurrentQuestion(question)
      setQuestionCount(prev => prev + 1)
    } catch (err: unknown) {
      console.error('Failed to load adaptive question:', err)
      const msg = err instanceof Error ? err.message : String(err)
      if (msg.includes('404') || msg.includes('No active questions')) {
        setError('No more questions available in this domain right now.')
      } else {
        setError('Failed to load question. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }, [domainId])

  useEffect(() => {
    loadNextQuestion()
  }, [loadNextQuestion])

  const handleRetry = async () => {
    if (!currentQuestion || error) {
      await loadNextQuestion(true)
    } else {
      setRetryCount(prev => prev + 1)
      await loadNextQuestion(true)
    }
  }

  const handleAnswerSelect = async (value: string) => {
    if (!currentQuestion || showResult) return

    setSelectedAnswer(value)
    setShowResult(true)
    setAnsweredCount(prev => prev + 1)

    const isCorrect = value === currentQuestion.correct_answer

    if (isAuthenticated) {
      try {
        const result = await recordAdaptiveAnswer({
          question_id: currentQuestion.id,
          selected_answer: value,
          is_correct: isCorrect,
        })
        if (result.adaptive?.theta != null) {
          setTheta(result.adaptive.theta)
        }
      } catch (err) {
        console.error('Failed to record answer:', err)
      }
    }

    if (isCorrect) {
      setCorrectCount(prev => prev + 1)
    }
  }

  const handleNext = async () => {
    await loadNextQuestion()
  }

  const accuracy = answeredCount > 0 ? Math.round((correctCount / answeredCount) * 100) : 0

  if (loading && !currentQuestion) {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-sage-200 border-t-sage-600 rounded-full animate-spin mx-auto" />
          <p className="mt-6 font-display text-text-muted">Preparing your next question...</p>
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
            <p className="text-text-muted text-sm mb-4">Retry attempt {retryCount}/3</p>
          )}
          <div className="flex gap-3 justify-center">
            <button
              onClick={handleRetry}
              disabled={loading}
              className="flex items-center gap-2 px-6 py-3 bg-sage-600 text-white rounded-xl font-display font-medium hover:bg-sage-700 transition-colors disabled:opacity-50"
            >
              {loading ? (
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
              onClick={onExit}
              className="px-6 py-3 border-2 border-sage-200 text-sage-700 rounded-xl font-display font-medium hover:bg-sage-50 transition-colors"
            >
              Exit Quiz
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-sage-50 via-surface to-surface py-8 px-4">
      <div className="max-w-3xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between mb-6"
        >
          <button
            onClick={onExit}
            className="flex items-center gap-2 text-text-muted hover:text-text transition-colors font-display"
          >
            <RotateCcw className="w-4 h-4" />
            Exit Quiz
          </button>

          <div className="flex items-center gap-4">
            {theta !== null && (
              <div className="flex items-center gap-1.5 px-3 py-1.5 bg-sage-100 rounded-lg">
                <Target className="w-4 h-4 text-sage-600" />
                <span className="text-sm font-display text-sage-700">
                  Skill: {getFriendlySkillLevel(theta)}
                </span>
              </div>
            )}
            <div className="text-sm font-display text-text-muted">
              Question {questionCount}
            </div>
            <div className="text-sm font-display text-text-muted">
              Accuracy: {accuracy}%
            </div>
          </div>
        </motion.div>

        {domainName && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center mb-6">
            <span className="px-4 py-1.5 bg-sand-100 text-sand-700 font-display text-sm rounded-full">
              {domainName}
            </span>
          </motion.div>
        )}

        <div className="bg-surface-elevated rounded-3xl p-8 shadow-lg shadow-sage-100/50 border border-border">
          {currentQuestion?.standard_id && (
            <div className="flex items-center gap-3 mb-6">
              <span className="px-3 py-1 bg-sage-100 text-sage-700 font-display font-medium text-sm rounded-full">
                Q.{currentQuestion.id}
              </span>
              <span className="text-text-muted text-sm">
                Difficulty: {Math.round((currentQuestion.difficulty || 0.5) * 100)}%
              </span>
            </div>
          )}

          {currentQuestion?.applet_type && (
            <div className="mb-6 flex justify-center">
              <GeoGebraApplet
                appletType={currentQuestion.applet_type as 'graphing' | 'geometry' | '3d' | 'classic'}
                commands={currentQuestion.geogebra_commands || undefined}
                height={400}
                width={600}
              />
            </div>
          )}

          <AnimatePresence mode="wait">
            {loading ? (
              <motion.div
                key="loading"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="min-h-[200px] flex items-center justify-center"
              >
                <div className="text-center">
                  <div className="w-12 h-12 border-4 border-sage-200 border-t-sage-600 rounded-full animate-spin mx-auto mb-4" />
                  <p className="text-text-muted font-display">Loading next question...</p>
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
                <h2
                  className="font-display text-2xl font-semibold text-text mb-6 leading-relaxed"
                  dangerouslySetInnerHTML={{ __html: renderMathToHtml(currentQuestion.question_text) }}
                />

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

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="flex items-center justify-center mt-8"
        >
          <button
            onClick={handleNext}
            disabled={!showResult || loading}
            className="flex items-center gap-2 px-8 py-3 bg-sage-600 text-white rounded-xl font-display font-medium hover:bg-sage-700 transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed shadow-lg shadow-sage-200 hover:shadow-xl hover:-translate-y-0.5"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Loading...
              </>
            ) : (
              <>
                Next Question
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </motion.div>
      </div>
    </div>
  )
}
