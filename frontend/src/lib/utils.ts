import katex from 'katex'
import 'katex/dist/katex.min.css'

/**
 * Combines class names using clsx and tailwind-merge
 */
export function cn(...inputs: (string | undefined | null | false)[]): string {
  return inputs.filter(Boolean).join(' ')
}

const MATH_WHITELIST = new Set([
  'sin', 'cos', 'tan', 'sec', 'csc', 'cot', 'log', 'ln', 'exp',
  'lim', 'max', 'min', 'sum', 'int', 'frac', 'sqrt', 'left', 'right',
  'over', 'cdot', 'times', 'pm', 'mp', 'neq', 'le', 'ge', 'lt', 'gt', 'leq', 'geq', 'cup', 'cap', 'vee', 'wedge',
  'in', 'not', 'and', 'pi', 'theta', 'alpha', 'beta', 'gamma', 'delta',
  'epsilon', 'lambda', 'mu', 'sigma', 'omega', 'phi', 'varphi', 'tau',
  'kappa', 'zeta', 'eta', 'xi', 'psi', 'rho', 'nu', 'chi', 'iota',
  'circ', 'deg', 'text', 'mbox', 'mathrm', 'mathbf', 'mathit', 'root',
  'tfrac', 'dfrac', 'binom', 'overline', 'underline', 'widetilde', 'widehat',
  'vec', 'bar', 'dot', 'ddot', 'hat', 'tilde', 'iint', 'iiint', 'oint',
  'prod', 'bigcup', 'bigcap', 'bigvee', 'bigwedge', 'infty', 'partial',
  'nabla', 'forall', 'exists', 'neg', 'lor', 'land', 'implies', 'iff',
  'to', 'mapsto', 'gets', 'mid', 'parallel', 'approx', 'sim',
  'cong', 'equiv', 'propto', 'perp', 'angle', 'triangle', 'square',
  'cdots', 'ldots', 'vdots', 'ddots', 'dots', 'quad', 'qquad', 'space',
  'operatorname', 'textrm', 'texttt', 'textsf', 'textbf', 'textit', 'emph',
  'mathop', 'bigl', 'bigr', 'Bigl', 'Bigr', 'biggl', 'biggr', 'Biggl',
  'Biggr', 'gcd', 'lcm', 'proj', 'det', 'dim', 'ker', 'hom', 'rank',
  'null', 'col', 'row', 'span', 'trace', 'bmod', 'pmod', 'pod', 'arg',
  'cosh', 'sinh', 'tanh', 'coth', 'sech', 'csch', 'arcsin', 'arccos',
  'arctan', 'arcsec', 'arccsc', 'arccot', 'arsinh', 'arcosh', 'artanh',
  'arcsch', 'arcoth', 'arsech', 'Re', 'Im', 'deg', 'det', 'div', 'mod',
])

function isValidMath(candidate: string): boolean {
  // Reject suspiciously long spans
  if (candidate.length > 300) return false

  // Reject anything that crosses a sentence boundary
  if (/[.!?]\s/.test(candidate)) return false

  // Reject prose words (3+ lowercase letters not in the math whitelist)
  const words = candidate.match(/[a-z]{3,}/g)
  if (words) {
    for (const w of words) {
      if (!MATH_WHITELIST.has(w)) return false
    }
  }

  return true
}

export function renderMathToHtml(text: string): string {
  // Protect escaped dollar signs
  const escapes: string[] = []
  text = text.replace(/\\\$/g, () => {
    escapes.push('$')
    return `[[ESCAPED_${escapes.length - 1}]]`
  })

  let result = ''
  let i = 0

  while (i < text.length) {
    if (text[i] !== '$') {
      result += text[i]
      i++
      continue
    }

    const j = text.indexOf('$', i + 1)
    if (j === -1) {
      // No closing delimiter — treat as literal
      result += '$'
      i++
      continue
    }

    const candidate = text.slice(i + 1, j)

    if (isValidMath(candidate)) {
      try {
        result += katex.renderToString(candidate, { throwOnError: false })
      } catch {
        result += text.slice(i, j + 1)
      }
      i = j + 1
    } else {
      // Not math — emit the opening $ literally and move forward
      // so the closing $ can still start a real math block later
      result += '$'
      i++
    }
  }

  // Restore escaped dollars
  result = result.replace(/\[\[ESCAPED_(\d+)\]\]/g, (_, idx) => escapes[parseInt(idx)])

  return result
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

/**
 * Returns a promise that resolves after the specified milliseconds
 */
export function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

/**
 * Returns a random element from an array
 */
export function getRandomElement<T>(array: T[]): T | undefined {
  if (array.length === 0) return undefined
  return array[Math.floor(Math.random() * array.length)]
}
