import { useSearchParams, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { Quiz } from '../../components/Quiz'
import { LoadingSpinner } from '../../components/ui/LoadingSpinner'
import { fetchMistakeStandards } from '../../services/student'
import type { Standard } from '../../types/standards'

export function QuizPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  const subjectId = searchParams.get('subjectId')
  const gradeId = searchParams.get('gradeId')
  const mode = searchParams.get('mode')
  const isMistakesMode = mode === 'mistakes'

  const [mistakeStandards, setMistakeStandards] = useState<Standard[]>([])
  const [loadingMistakes, setLoadingMistakes] = useState(isMistakesMode)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!isMistakesMode || !subjectId || !gradeId) {
      setLoadingMistakes(false)
      return
    }

    async function load() {
      try {
        const standards = await fetchMistakeStandards({
          subject_id: parseInt(subjectId!),
          grade_id: parseInt(gradeId!),
        })
        setMistakeStandards(standards)
      } catch {
        setError('Failed to load mistake standards.')
      } finally {
        setLoadingMistakes(false)
      }
    }
    load()
  }, [isMistakesMode, subjectId, gradeId])

  if (!subjectId || !gradeId) {
    return (
      <div className="max-w-7xl mx-auto text-center py-16">
        <p className="text-text-muted font-display">No subject or grade selected.</p>
        <button
          onClick={() => navigate('/student')}
          className="mt-4 px-6 py-2 bg-sage-600 text-white rounded-xl font-display font-medium hover:bg-sage-700 transition-colors"
        >
          Go to Dashboard
        </button>
      </div>
    )
  }

  if (loadingMistakes) {
    return <LoadingSpinner text="Loading mistake standards..." />
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto text-center py-16">
        <p className="text-coral-600 font-display">{error}</p>
        <button
          onClick={() => navigate('/student')}
          className="mt-4 px-6 py-2 bg-sage-600 text-white rounded-xl font-display font-medium hover:bg-sage-700 transition-colors"
        >
          Go to Dashboard
        </button>
      </div>
    )
  }

  return (
    <Quiz
      subjectId={subjectId}
      gradeId={gradeId}
      onExit={() => navigate('/student')}
      standards={isMistakesMode ? mistakeStandards : undefined}
    />
  )
}
