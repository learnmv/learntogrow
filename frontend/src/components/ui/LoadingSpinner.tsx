interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  text?: string
}

const sizeMap: Record<NonNullable<LoadingSpinnerProps['size']>, number> = {
  sm: 20,
  md: 32,
  lg: 48,
}

const borderWidthMap: Record<NonNullable<LoadingSpinnerProps['size']>, number> = {
  sm: 2,
  md: 4,
  lg: 4,
}

export function LoadingSpinner({ size = 'md', text }: LoadingSpinnerProps) {
  const dimension = sizeMap[size]
  const borderWidth = borderWidthMap[size]

  return (
    <div className="flex flex-col items-center justify-center py-8">
      <div
        className="animate-spin rounded-full border-sage-200 border-t-sage-600"
        style={{
          width: dimension,
          height: dimension,
          borderWidth,
        }}
        role="status"
        aria-label="Loading"
      />
      {text && (
        <p className="mt-3 text-sm text-text-muted font-display">
          {text}
        </p>
      )}
    </div>
  )
}