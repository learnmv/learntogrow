/**
 * Combines class names using clsx and tailwind-merge
 */
export function cn(...inputs: (string | undefined | null | false)[]): string {
  return inputs.filter(Boolean).join(' ')
}

export function renderMathToHtml(text: string): string {
  return text.replace(/\$([^$]+)\$/g, '<span class="math-inline">$1</span>')
}

/**
 * Formats a number as a percentage
 */
export function formatPercentage(value: number): string {
  return `${Math.round(value * 100)}%`
}

/**
 * Truncates text with ellipsis
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return `${text.slice(0, maxLength)}...`
}

/**
 * Debounces a function
 */
export function debounce<T extends (...args: unknown[]) => void>(
  fn: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout>
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => fn(...args), delay)
  }
}
