import { AlertCircle } from 'lucide-react'

interface ErrorDisplayProps {
  message: string
  onRetry?: () => void
}

export function ErrorDisplay({ message, onRetry }: ErrorDisplayProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <div className="w-14 h-14 bg-coral-50 rounded-2xl flex items-center justify-center mb-4">
        <AlertCircle className="w-7 h-7 text-coral-500" />
      </div>
      <p className="text-text-muted font-body max-w-md mb-6">
        {message}
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-6 py-2.5 bg-coral-500 text-white rounded-xl font-display font-medium hover:bg-coral-600 transition-colors"
        >
          Try Again
        </button>
      )}
    </div>
  )
}