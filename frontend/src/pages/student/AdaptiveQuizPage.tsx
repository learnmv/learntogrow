import { useSearchParams, useNavigate } from 'react-router-dom'
import { AdaptiveQuiz } from '../../components/AdaptiveQuiz'

export function AdaptiveQuizPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  const domainId = searchParams.get('domainId')
  const domainName = searchParams.get('domainName') || undefined

  if (!domainId) {
    return (
      <div className="max-w-7xl mx-auto text-center py-16">
        <p className="text-text-muted font-display">No domain selected.</p>
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
    <AdaptiveQuiz
      domainId={domainId}
      domainName={domainName}
      onExit={() => navigate('/student')}
    />
  )
}
