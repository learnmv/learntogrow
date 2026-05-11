import { useEffect, useMemo, useState } from 'react'
import { Bot, Loader2, Send, Sparkles, User } from 'lucide-react'
import { fetchGrades, fetchSubjects } from '../../services/standards'
import { sendParentAssistantMessage } from '../../services/parent'
import type { Grade, Subject } from '../../types/standards'
import type { ParentStudentLink } from '../../types/parent'

interface ParentAssistantProps {
  childrenList: ParentStudentLink[]
}

interface ChatMessage {
  role: 'assistant' | 'parent'
  content: string
}

const starterPrompts = [
  "What are my child's weak topics?",
  "What are my child's strong topics?",
  'Show syllabus',
]

export function ParentAssistant({ childrenList }: ParentAssistantProps) {
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
        student_id: selectedStudentId ? Number(selectedStudentId) : undefined,
        subject_id: selectedSubjectId ? Number(selectedSubjectId) : undefined,
        grade_id: selectedGradeId ? Number(selectedGradeId) : undefined,
      })
      setMessages((current) => [...current, { role: 'assistant', content: response.answer }])
      setSuggestions(response.suggestions.length > 0 ? response.suggestions : starterPrompts)
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
              Ask about strengths, weak topics, progress, or curriculum syllabus.
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
                {message.content}
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
            placeholder="Ask about weak topics, strong topics, or syllabus..."
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
