import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ArrowLeft, ArrowRight, BookOpen, RotateCcw, CheckCircle, XCircle } from 'lucide-react'
import { fetchStandards } from '../services/standards'
import { generateQuestion } from '../services/questions'
import { cn } from '../lib/utils'
import type { Standard } from '../types/standards'
import type { GeneratedQuestion, QuestionGenerationRequest } from '../types/questions'

interface QuizProps {
  subjectId: string
  gradeId: string
  onExit: () => void
}

export function Quiz({ subjectId, gradeId, onExit }: QuizProps) {
  const [standards, setStandards] = useState<Standard[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [currentQuestion, setCurrentQuestion] = useState<GeneratedQuestion | null>(null)
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null)
  const [showResult, setShowResult] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [generatingQuestion, setGeneratingQuestion] = useState(false)

  // Fetch standards on mount
  useEffect(() => {
    async function loadStandards() {
      try {
        const standardsList = await fetchStandards({
          subject_id: parseInt(subjectId),
          grade_id: parseInt(gradeId),
        })
        setStandards(standardsList)
        setLoading(false)
      } catch (err) {
        setError('Failed to load standards')
        setLoading(false)
      }
    }

    loadStandards()
  }, [subjectId, gradeId])

  // Generate question when currentIndex changes
  useEffect(() => {
    if (standards.length === 0) return

    async function loadQuestion() {
      setGeneratingQuestion(true)
      setSelectedAnswer(null)
      setShowResult(false)

      try {
        const request: QuestionGenerationRequest = {
          standard_id: standards[currentIndex].id,
          question_type: 'multiple_choice',
        }
        const question = await generateQuestion(request)
        setCurrentQuestion(question)
      } catch (err) {
        setError('Failed to generate question')
      } finally {
        setGeneratingQuestion(false)
      }
    }

    loadQuestion()
  }, [standards, currentIndex])

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

  const handleAnswerSelect = (value: string) => {
    setSelectedAnswer(value)
    setShowResult(true)
  }

  const isCorrect = selectedAnswer === currentQuestion?.answer

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
          <p className="text-coral-600 font-display text-lg mb-6">{error}</p>
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

  // Handle case where no standards were found
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
            onClick={onExit}
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

        {/* Question Card */}
        <AnimatePresence mode="wait">
          {generatingQuestion ? (
            <motion.div
              key="loading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="bg-surface-elevated rounded-3xl p-8 shadow-lg shadow-sage-100/50 border border-border min-h-[400px] flex items-center justify-center"
            >
              <div className="text-center">
                <div className="w-12 h-12 border-4 border-sage-200 border-t-sage-600 rounded-full animate-spin mx-auto mb-4" />
                <p className="text-text-muted font-display">Generating question...</p>
              </div>
            </motion.div>
          ) : currentQuestion ? (
            <motion.div
              key="question"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
              className="bg-surface-elevated rounded-3xl p-8 shadow-lg shadow-sage-100/50 border border-border"
            >
              {/* Standard Info */}
              <div className="flex items-center gap-3 mb-6">
                <span className="px-3 py-1 bg-sage-100 text-sage-700 font-display font-medium text-sm rounded-full">
                  {currentStandard?.code}
                </span>
                <span className="text-text-muted text-sm">
                  Difficulty: {Math.round((currentStandard?.difficulty_base || 0) * 100)}%
                </span>
              </div>

              {/* Question Text */}
              <h2 className="font-display text-2xl font-semibold text-text mb-8 leading-relaxed">
                {currentQuestion.question}
              </h2>

              {/* Options */}
              <div className="space-y-3">
                {currentQuestion.options.map((option, index) => {
                  const isSelected = selectedAnswer === option
                  const isCorrectAnswer = option === currentQuestion.answer
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
                        <span className="font-body text-text text-lg">{option}</span>
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
                {showResult && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="mt-6 p-4 bg-sage-50 rounded-2xl border border-sage-200"
                  >
                    <p className="font-display font-medium text-sage-700 mb-2">Explanation</p>
                    <p className="text-text-muted font-body">{currentQuestion.explanation}</p>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ) : null}
        </AnimatePresence>

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
