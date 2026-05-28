import { renderMathToHtml } from '../lib/utils'
import type { QuestionStimulus as QuestionStimulusType, TableStimulus } from '../types/questions'

interface ParsedQuestion {
  questionText: string
  stimulus: QuestionStimulusType | null
}

interface QuestionStimulusProps {
  questionText: string
  stimulus?: QuestionStimulusType | null
  questionClassName?: string
  className?: string
}

function splitTableCells(line: string): string[] {
  return line.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map(cell => cell.trim())
}

function isSeparatorLine(line: string): boolean {
  return /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(line)
}

function parseMarkdownTable(questionText: string): ParsedQuestion {
  const lines = questionText.split(/\r?\n/)
  for (let index = 0; index < lines.length - 1; index += 1) {
    if (!lines[index].includes('|') || !isSeparatorLine(lines[index + 1])) continue

    const columns = splitTableCells(lines[index])
    if (columns.length < 2 || columns.some(column => !column)) continue

    const rows: string[][] = []
    let end = index + 2
    while (end < lines.length && lines[end].includes('|')) {
      const row = splitTableCells(lines[end])
      if (row.length !== columns.length) break
      rows.push(row)
      end += 1
    }

    if (rows.length === 0) continue

    const cleaned = [...lines.slice(0, index), ...lines.slice(end)]
      .join('\n')
      .replace(/\n{3,}/g, '\n\n')
      .trim()

    return {
      questionText: cleaned,
      stimulus: {
        type: 'table',
        columns,
        rows,
      },
    }
  }

  return { questionText, stimulus: null }
}

function isTableStimulus(stimulus: QuestionStimulusType | null | undefined): stimulus is TableStimulus {
  return (
    Boolean(stimulus) &&
    stimulus?.type === 'table' &&
    Array.isArray((stimulus as TableStimulus).columns) &&
    Array.isArray((stimulus as TableStimulus).rows)
  )
}

function StimulusTable({ stimulus }: { stimulus: TableStimulus }) {
  return (
    <div className="my-5 overflow-x-auto">
      {stimulus.title && (
        <p className="mb-2 text-sm font-display font-medium text-text-muted">{stimulus.title}</p>
      )}
      <table className="w-full min-w-[320px] border-collapse overflow-hidden rounded-lg border border-border bg-surface">
        <thead>
          <tr className="bg-sage-50">
            {stimulus.columns.map((column, index) => (
              <th
                key={`${column}-${index}`}
                className="border border-border px-4 py-3 text-left font-display text-sm font-semibold text-sage-800"
                dangerouslySetInnerHTML={{ __html: renderMathToHtml(column) }}
              />
            ))}
          </tr>
        </thead>
        <tbody>
          {stimulus.rows.map((row, rowIndex) => (
            <tr key={rowIndex} className="odd:bg-white even:bg-surface-muted/40">
              {row.map((cell, cellIndex) => (
                <td
                  key={`${rowIndex}-${cellIndex}`}
                  className="border border-border px-4 py-3 font-body text-base text-text"
                  dangerouslySetInnerHTML={{ __html: renderMathToHtml(cell) }}
                />
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function QuestionStimulus({
  questionText,
  stimulus,
  questionClassName,
  className,
}: QuestionStimulusProps) {
  const parsed = stimulus ? { questionText, stimulus } : parseMarkdownTable(questionText)

  return (
    <div className={className}>
      <div
        className={questionClassName}
        dangerouslySetInnerHTML={{ __html: renderMathToHtml(parsed.questionText) }}
      />
      {isTableStimulus(parsed.stimulus) && <StimulusTable stimulus={parsed.stimulus} />}
    </div>
  )
}
