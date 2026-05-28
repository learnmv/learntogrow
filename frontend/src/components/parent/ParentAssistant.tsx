import { useEffect, useMemo, useState } from 'react'
import {
  AlertCircle,
  BookOpen,
  Bot,
  CheckCircle2,
  ClipboardList,
  Loader2,
  Send,
  Sparkles,
  Target,
  User,
} from 'lucide-react'
import { fetchGrades, fetchSubjects } from '../../services/standards'
import { sendParentAssistantMessage } from '../../services/parent'
import type { Grade, Subject } from '../../types/standards'
import type { ParentStudentLink } from '../../types/parent'

interface ParentAssistantProps {
  childrenList: ParentStudentLink[]
  onAssignmentCreated?: () => void
}

interface ChatMessage {
  role: 'assistant' | 'parent'
  content: string
  intent?: string
  data?: Record<string, unknown>
}

const starterPrompts = [
  "What are my child's weak topics?",
  "What are my child's strong topics?",
  'Assign a 5 question medium quiz',
  'Show syllabus',
]

export function ParentAssistant({ childrenList, onAssignmentCreated }: ParentAssistantProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content: "Ask me about your child's weak topics, strong topics, progress, or a subject syllabus.",
    },
  ])
  const [input, setInput] = useState('')
  const [selectedStudentId, setSelectedStudentId] = useState('')
  const [subjects, setSubjects] = useState<Subject[]>([])
  const [grades, setGrades] = useState<Grade[]>([])
  const [selectedSubjectId, setSelectedSubjectId] = useState('')
  const [selectedGradeId, setSelectedGradeId] = useState('')
  const [loadingSubjects, setLoadingSubjects] = useState(true)
  const [loadingGrades, setLoadingGrades] = useState(false)
  const [sending, setSending] = useState(false)
  const [suggestions, setSuggestions] = useState(starterPrompts)
  const [threadId, setThreadId] = useState<number | null>(null)

  useEffect(() => {
    if (!selectedStudentId && childrenList.length === 1) {
      setSelectedStudentId(String(childrenList[0].student_id))
    }
  }, [childrenList, selectedStudentId])

  useEffect(() => {
    async function loadSubjects() {
      try {
        const data = await fetchSubjects()
        setSubjects(data)
      } catch {
        setSubjects([])
      } finally {
        setLoadingSubjects(false)
      }
    }

    loadSubjects()
  }, [])

  useEffect(() => {
    if (!selectedSubjectId) {
      setGrades([])
      setSelectedGradeId('')
      return
    }

    async function loadGrades() {
      setLoadingGrades(true)
      try {
        const data = await fetchGrades(Number(selectedSubjectId))
        setGrades(data)
      } catch {
        setGrades([])
      } finally {
        setLoadingGrades(false)
      }
    }

    loadGrades()
  }, [selectedSubjectId])

  const canSend = input.trim().length > 0 && !sending
  const selectedChildName = useMemo(() => {
    const child = childrenList.find((item) => String(item.student_id) === selectedStudentId)
    return child?.student_name
  }, [childrenList, selectedStudentId])

  async function sendMessage(messageText: string) {
    const trimmed = messageText.trim()
    if (!trimmed || sending) return

    setInput('')
    setSending(true)
    setMessages((current) => [...current, { role: 'parent', content: trimmed }])

    try {
      const response = await sendParentAssistantMessage({
        message: trimmed,
        thread_id: threadId ?? undefined,
        student_id: selectedStudentId ? Number(selectedStudentId) : undefined,
        subject_id: selectedSubjectId ? Number(selectedSubjectId) : undefined,
        grade_id: selectedGradeId ? Number(selectedGradeId) : undefined,
      })
      setThreadId(response.thread_id)
      setMessages((current) => [
        ...current,
        {
          role: 'assistant',
          content: response.answer,
          intent: response.intent,
          data: response.data,
        },
      ])
      setSuggestions(response.suggestions.length > 0 ? response.suggestions : starterPrompts)
      if (response.intent === 'quiz_assignment' && response.data.assignment) {
        onAssignmentCreated?.()
      }
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'The assistant could not answer right now.'
      setMessages((current) => [...current, { role: 'assistant', content: message }])
    } finally {
      setSending(false)
    }
  }

  return (
    <section className="bg-surface-elevated border border-border rounded-2xl p-6 mb-8 shadow-sm">
      <div className="flex flex-col gap-5">
        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-sage-600" />
              <h2 className="text-lg font-display font-semibold text-text">Parent Assistant</h2>
            </div>
            <p className="mt-1 text-sm text-text-muted">
              Ask about strengths, weak topics, syllabus, or assign a quiz.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 md:min-w-[520px]">
            <select
              value={selectedStudentId}
              onChange={(event) => setSelectedStudentId(event.target.value)}
              className="h-11 px-3 bg-surface border border-border rounded-xl text-sm text-text focus:outline-none focus:ring-2 focus:ring-sage-500"
            >
              <option value="">Select child</option>
              {childrenList.map((child) => (
                <option key={child.student_id} value={child.student_id}>
                  {child.student_name}
                </option>
              ))}
            </select>

            <select
              value={selectedSubjectId}
              onChange={(event) => {
                setSelectedSubjectId(event.target.value)
                setSelectedGradeId('')
              }}
              disabled={loadingSubjects}
              className="h-11 px-3 bg-surface border border-border rounded-xl text-sm text-text focus:outline-none focus:ring-2 focus:ring-sage-500 disabled:opacity-60"
            >
              <option value="">Subject context</option>
              {subjects.map((subject) => (
                <option key={subject.id} value={subject.id}>
                  {subject.name}
                </option>
              ))}
            </select>

            <select
              value={selectedGradeId}
              onChange={(event) => setSelectedGradeId(event.target.value)}
              disabled={!selectedSubjectId || loadingGrades}
              className="h-11 px-3 bg-surface border border-border rounded-xl text-sm text-text focus:outline-none focus:ring-2 focus:ring-sage-500 disabled:opacity-60"
            >
              <option value="">Grade context</option>
              {grades.map((grade) => (
                <option key={grade.id} value={grade.id}>
                  {grade.display_name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="h-72 overflow-y-auto rounded-2xl bg-surface-muted border border-border-subtle p-4 space-y-3">
          {messages.map((message, index) => (
            <div
              key={`${message.role}-${index}`}
              className={`flex gap-3 ${message.role === 'parent' ? 'justify-end' : 'justify-start'}`}
            >
              {message.role === 'assistant' && (
                <div className="w-8 h-8 rounded-xl bg-sage-100 flex items-center justify-center shrink-0">
                  <Bot className="w-4 h-4 text-sage-700" />
                </div>
              )}
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm whitespace-pre-line ${
                  message.role === 'parent'
                    ? 'bg-sage-600 text-white'
                    : 'bg-surface-elevated border border-border text-text'
                }`}
              >
                <p>{message.content}</p>
                {message.role === 'assistant' && (
                  <AssistantResponseCard message={message} onAction={sendMessage} sending={sending} />
                )}
              </div>
              {message.role === 'parent' && (
                <div className="w-8 h-8 rounded-xl bg-coral-100 flex items-center justify-center shrink-0">
                  <User className="w-4 h-4 text-coral-700" />
                </div>
              )}
            </div>
          ))}
          {sending && (
            <div className="flex items-center gap-2 text-sm text-text-muted">
              <Loader2 className="w-4 h-4 animate-spin text-sage-600" />
              Checking learning data...
            </div>
          )}
        </div>

        <div className="flex flex-wrap gap-2">
          {suggestions.map((suggestion) => (
            <button
              key={suggestion}
              onClick={() => sendMessage(suggestion)}
              disabled={sending}
              className="px-3 py-1.5 rounded-lg bg-sage-100 text-sage-700 text-xs font-display font-medium hover:bg-sage-200 transition-colors disabled:opacity-50"
            >
              {selectedChildName && suggestion.includes('child')
                ? suggestion.replace("my child's", `${selectedChildName}'s`)
                : suggestion}
            </button>
          ))}
        </div>

        <form
          onSubmit={(event) => {
            event.preventDefault()
            sendMessage(input)
          }}
          className="flex gap-3"
        >
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Ask about weak topics, syllabus, or assign a quiz..."
            className="flex-1 h-12 px-4 bg-surface border border-border rounded-xl text-text focus:outline-none focus:ring-2 focus:ring-sage-500"
          />
          <button
            type="submit"
            disabled={!canSend}
            className="h-12 px-5 bg-sage-600 text-white rounded-xl font-display font-semibold hover:bg-sage-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            Ask
          </button>
        </form>
      </div>
    </section>
  )
}

interface AssistantResponseCardProps {
  message: ChatMessage
  onAction: (messageText: string) => void
  sending: boolean
}

function AssistantResponseCard({ message, onAction, sending }: AssistantResponseCardProps) {
  const data = message.data
  if (!data) return null

  const cardType = getString(data.card_type)
  if (cardType === 'topics' || message.intent === 'weak_topics' || message.intent === 'strong_topics') {
    const topics = getArray(data.weak_topics).length > 0
      ? getArray(data.weak_topics)
      : getArray(data.strong_topics)
    return <TopicCard topics={topics} focus={message.intent === 'strong_topics' ? 'strong' : 'weak'} onAction={onAction} sending={sending} />
  }

  if (cardType === 'syllabus') {
    return <SyllabusCard domains={getArray(data.domains)} />
  }

  if (cardType === 'quiz_preview') {
    return <QuizPreviewCard quiz={getRecord(data.pending_quiz)} onAction={onAction} sending={sending} />
  }

  if (cardType === 'assignment_confirmation') {
    return <AssignmentCard assignment={getRecord(data.assignment)} generatedQuestions={getNumber(data.generated_questions)} />
  }

  if (cardType === 'quiz_error') {
    return <ErrorCard error={getString(data.error) || 'Quiz assignment failed.'} />
  }

  return null
}

interface TopicCardProps {
  topics: unknown[]
  focus: 'weak' | 'strong'
  onAction: (messageText: string) => void
  sending: boolean
}

function TopicCard({ topics, focus, onAction, sending }: TopicCardProps) {
  if (topics.length === 0) return null
  const actionLabel = focus === 'weak' ? 'Assign practice on these' : 'Show weak topics'
  const actionPrompt = focus === 'weak' ? 'Assign a 5 question medium quiz on those weak topics' : 'Show weak topics'

  return (
    <div className="mt-3 rounded-xl border border-border bg-surface p-3 space-y-2 whitespace-normal">
      <div className="flex items-center gap-2 text-xs font-display font-semibold text-text-muted">
        <Target className="w-4 h-4 text-sage-600" />
        {focus === 'weak' ? 'Practice priorities' : 'Current strengths'}
      </div>
      <div className="space-y-2">
        {topics.slice(0, 3).map((topic, index) => {
          const item = getRecord(topic)
          const accuracy = getNumber(item.accuracy)
          const progress = getNumber(item.progress)
          const pct = accuracy !== null ? Math.round(accuracy * 100) : null
          const progressPct = progress !== null ? Math.round(progress * 100) : null
          return (
            <div key={`${getString(item.domain_code) || index}`} className="rounded-lg bg-surface-elevated border border-border-subtle p-3">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-display font-semibold text-text text-sm">
                    {getString(item.domain_name) || 'Topic'}
                  </p>
                  <p className="text-xs text-text-muted">
                    {getString(item.domain_code)} · {getString(item.level) || 'Skill level pending'}
                  </p>
                </div>
                {pct !== null && (
                  <span className="text-xs font-display font-semibold text-sage-700 bg-sage-100 rounded-lg px-2 py-1">
                    {pct}%
                  </span>
                )}
              </div>
              {progressPct !== null && (
                <div className="mt-2 h-1.5 rounded-full bg-sage-100 overflow-hidden">
                  <div className="h-full bg-sage-600" style={{ width: `${Math.min(100, Math.max(0, progressPct))}%` }} />
                </div>
              )}
            </div>
          )
        })}
      </div>
      <button
        type="button"
        onClick={() => onAction(actionPrompt)}
        disabled={sending}
        className="inline-flex items-center gap-2 rounded-lg bg-sage-600 px-3 py-2 text-xs font-display font-semibold text-white hover:bg-sage-700 disabled:opacity-50"
      >
        <ClipboardList className="w-3.5 h-3.5" />
        {actionLabel}
      </button>
    </div>
  )
}

function SyllabusCard({ domains }: { domains: unknown[] }) {
  if (domains.length === 0) return null
  return (
    <div className="mt-3 rounded-xl border border-border bg-surface p-3 whitespace-normal">
      <div className="flex items-center gap-2 text-xs font-display font-semibold text-text-muted mb-2">
        <BookOpen className="w-4 h-4 text-sage-600" />
        Syllabus domains
      </div>
      <div className="grid grid-cols-1 gap-2">
        {domains.slice(0, 6).map((domain, index) => {
          const item = getRecord(domain)
          return (
            <div key={`${getString(item.domain_code) || index}`} className="rounded-lg bg-surface-elevated border border-border-subtle p-3">
              <p className="font-display font-semibold text-text text-sm">
                {getString(item.domain_name) || 'Domain'}
              </p>
              <p className="text-xs text-text-muted">
                {getString(item.domain_code)} · {getNumber(item.standards_count) ?? 0} standards
              </p>
            </div>
          )
        })}
      </div>
    </div>
  )
}

interface QuizPreviewCardProps {
  quiz: Record<string, unknown>
  onAction: (messageText: string) => void
  sending: boolean
}

function QuizPreviewCard({ quiz, onAction, sending }: QuizPreviewCardProps) {
  if (Object.keys(quiz).length === 0) return null
  const domains = getArray(quiz.domains)
  return (
    <div className="mt-3 rounded-xl border border-sage-200 bg-sage-50 p-3 whitespace-normal">
      <div className="flex items-center gap-2 text-xs font-display font-semibold text-sage-700 mb-2">
        <ClipboardList className="w-4 h-4" />
        Quiz preview
      </div>
      <div className="grid grid-cols-2 gap-2 text-xs">
        <PreviewField label="Student" value={getString(quiz.student_name)} />
        <PreviewField label="Subject" value={getString(quiz.subject_name)} />
        <PreviewField label="Grade" value={getString(quiz.grade_name)} />
        <PreviewField label="Difficulty" value={getString(quiz.difficulty)} />
        <PreviewField label="Questions" value={String(getNumber(quiz.question_count) ?? 5)} />
        <PreviewField label="AI fill" value={quiz.generate_missing ? 'On' : 'Off'} />
      </div>
      {domains.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {domains.map((domain, index) => {
            const item = getRecord(domain)
            return (
              <span key={`${getString(item.domain_code) || index}`} className="rounded-lg bg-white border border-sage-200 px-2 py-1 text-xs text-sage-700">
                {getString(item.domain_name) || getString(item.domain_code)}
              </span>
            )
          })}
        </div>
      )}
      <div className="mt-3 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => onAction('Yes, assign it')}
          disabled={sending}
          className="inline-flex items-center gap-1.5 rounded-lg bg-sage-600 px-3 py-2 text-xs font-display font-semibold text-white hover:bg-sage-700 disabled:opacity-50"
        >
          <CheckCircle2 className="w-3.5 h-3.5" />
          Assign
        </button>
        <button
          type="button"
          onClick={() => onAction('Make it easier')}
          disabled={sending}
          className="rounded-lg bg-white border border-sage-200 px-3 py-2 text-xs font-display font-semibold text-sage-700 hover:bg-sage-100 disabled:opacity-50"
        >
          Easier
        </button>
        <button
          type="button"
          onClick={() => onAction('Make it harder')}
          disabled={sending}
          className="rounded-lg bg-white border border-sage-200 px-3 py-2 text-xs font-display font-semibold text-sage-700 hover:bg-sage-100 disabled:opacity-50"
        >
          Harder
        </button>
      </div>
    </div>
  )
}

function PreviewField({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="rounded-lg bg-white border border-sage-200 p-2">
      <p className="text-[11px] uppercase tracking-wide text-sage-700 font-display font-semibold">{label}</p>
      <p className="text-text font-display font-semibold capitalize">{value || '-'}</p>
    </div>
  )
}

function AssignmentCard({ assignment, generatedQuestions }: { assignment: Record<string, unknown>; generatedQuestions: number | null }) {
  if (Object.keys(assignment).length === 0) return null
  return (
    <div className="mt-3 rounded-xl border border-sage-200 bg-sage-50 p-3 whitespace-normal">
      <div className="flex items-center gap-2 text-xs font-display font-semibold text-sage-700 mb-2">
        <CheckCircle2 className="w-4 h-4" />
        Assignment created
      </div>
      <p className="font-display font-semibold text-text">{getString(assignment.title) || 'Practice Quiz'}</p>
      <p className="text-xs text-text-muted mt-1">
        {getString(assignment.student_name) || 'Student'} · {getNumber(assignment.question_count) ?? 0} questions · {getString(assignment.difficulty) || 'mixed'}
      </p>
      <p className="text-xs text-text-muted mt-1">
        {generatedQuestions && generatedQuestions > 0
          ? `${generatedQuestions} new questions generated`
          : 'Using existing unanswered questions'}
      </p>
    </div>
  )
}

function ErrorCard({ error }: { error: string }) {
  return (
    <div className="mt-3 rounded-xl border border-coral-200 bg-coral-50 p-3 whitespace-normal">
      <div className="flex items-start gap-2 text-coral-700">
        <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
        <p className="text-xs">{error}</p>
      </div>
    </div>
  )
}

function getRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    ? value as Record<string, unknown>
    : {}
}

function getArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : []
}

function getString(value: unknown): string | null {
  return typeof value === 'string' && value.trim() ? value : null
}

function getNumber(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null
}
