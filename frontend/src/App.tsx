import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Play, BookOpen } from 'lucide-react'
import './index.css'
import { SubjectSelector } from './components/ui/SubjectSelector'
import { Quiz } from './components/Quiz'
import { ANIMATION } from './lib/constants'

function App() {
  const [quizActive, setQuizActive] = useState(false)
  const [selectedSubject, setSelectedSubject] = useState<string>('')
  const [selectedGrade, setSelectedGrade] = useState<string>('')

  const handleGradeSelect = useCallback((subjectId: string, gradeId: string) => {
    setSelectedSubject(subjectId)
    setSelectedGrade(gradeId)
  }, [])

  const handleStartQuiz = () => {
    if (selectedSubject && selectedGrade) {
      setQuizActive(true)
    }
  }

  const handleExitQuiz = () => {
    setQuizActive(false)
  }

  return (
    <AnimatePresence mode="wait">
      {quizActive ? (
        <Quiz
          key="quiz"
          subjectId={selectedSubject}
          gradeId={selectedGrade}
          onExit={handleExitQuiz}
        />
      ) : (
        <motion.div
          key="home"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: ANIMATION.slow }}
          className="min-h-screen bg-surface flex flex-col items-center justify-center gap-8 px-4"
        >
          {/* Header */}
          <div className="text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-sage-100 rounded-full mb-6">
              <BookOpen className="w-4 h-4 text-sage-600" />
              <span className="text-sm font-display font-medium text-sage-700">
                AI-Powered Learning
              </span>
            </div>

            <h1 className="font-display text-6xl font-semibold text-text tracking-tight">
              Learn<span className="text-sage-600">To</span>Grow
            </h1>

            <p className="mt-4 text-lg text-text-muted max-w-md mx-auto">
              Select a subject and grade to begin your personalized quiz
            </p>
          </div>

          {/* Selector */}
          <SubjectSelector onGradeSelect={handleGradeSelect} />

          {/* Start Quiz Button */}
          <AnimatePresence>
            {selectedSubject && selectedGrade && (
              <motion.button
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                whileHover={{ scale: 1.05, y: -2 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleStartQuiz}
                className="flex items-center gap-3 px-8 py-4 bg-coral-500 text-white rounded-2xl font-display font-semibold text-lg shadow-lg shadow-coral-200 hover:shadow-xl transition-shadow"
              >
                <Play className="w-5 h-5" />
                Start Quiz
              </motion.button>
            )}
          </AnimatePresence>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export default App
