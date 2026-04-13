import { useSearchParams, useNavigate } from 'react-router-dom'
import { Quiz } from '../../components/Quiz'

export function QuizPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  const subjectId = searchParams.get('subjectId')
  const gradeId = searchParams.get('gradeId')

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

  return (
    <Quiz
      subjectId={subjectId}
      gradeId={gradeId}
      onExit={() => navigate('/student')}
    />
  )
}