import { useEffect, useRef, useState } from 'react'
import type { FormEvent, KeyboardEvent } from 'react'
import { Bot, Loader2, MessageSquare, Send, Trash2, User } from 'lucide-react'
import { sendAdminChatMessage } from '../../services/admin'
import type { AdminChatMessage } from '../../types/admin'

const openingMessage: AdminChatMessage = {
  role: 'assistant',
  content: 'Hi. Ask me anything you want to test against the configured model.',
}

export function AdminChat() {
  const [messages, setMessages] = useState<AdminChatMessage[]>([openingMessage])
  const [input, setInput] = useState('')
  const [model, setModel] = useState<string | null>(null)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const scrollRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: 'smooth',
    })
  }, [messages, sending])

  const canSend = input.trim().length > 0 && !sending

  async function sendMessage() {
    const trimmed = input.trim()
    if (!trimmed || sending) return

    const userMessage: AdminChatMessage = { role: 'user', content: trimmed }
    const conversation = [...messages, userMessage]
    setMessages(conversation)
    setInput('')
    setError(null)
    setSending(true)

    try {
      const response = await sendAdminChatMessage({
        messages: conversation,
        temperature: 0.3,
      })
      setModel(response.model)
      setMessages((current) => [...current, response.message])
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'The model could not respond right now.'
      setError(message)
      setMessages((current) => [
        ...current,
        { role: 'assistant', content: message },
      ])
    } finally {
      setSending(false)
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    sendMessage()
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      sendMessage()
    }
  }

  function clearChat() {
    setMessages([openingMessage])
    setInput('')
    setError(null)
  }

  return (
    <section className="bg-surface-elevated border border-border rounded-2xl shadow-sm overflow-hidden">
      <div className="px-6 py-4 border-b border-border flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-sage-100 flex items-center justify-center">
            <MessageSquare className="w-5 h-5 text-sage-700" />
          </div>
          <div>
            <h2 className="text-lg font-display font-semibold text-text">Chat</h2>
            <p className="text-sm text-text-muted">
              {model ? `Model: ${model}` : 'Uses the configured Ollama model'}
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={clearChat}
          className="h-10 px-3 rounded-xl border border-border text-text-muted hover:text-text hover:bg-surface-muted transition-colors inline-flex items-center justify-center gap-2 text-sm font-display font-medium"
        >
          <Trash2 className="w-4 h-4" />
          Clear
        </button>
      </div>

      <div
        ref={scrollRef}
        className="h-[520px] overflow-y-auto bg-surface-muted px-4 py-5 sm:px-6 space-y-4"
      >
        {messages.map((message, index) => {
          const isUser = message.role === 'user'
          return (
            <div
              key={`${message.role}-${index}`}
              className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
            >
              {!isUser && (
                <div className="w-9 h-9 rounded-xl bg-sage-100 flex items-center justify-center shrink-0">
                  <Bot className="w-4 h-4 text-sage-700" />
                </div>
              )}
              <div
                className={`max-w-[min(720px,80%)] rounded-2xl px-4 py-3 text-sm leading-6 whitespace-pre-wrap ${
                  isUser
                    ? 'bg-sage-600 text-white'
                    : error && index === messages.length - 1
                      ? 'bg-coral-50 border border-coral-200 text-coral-700'
                      : 'bg-surface-elevated border border-border text-text'
                }`}
              >
                {message.content}
              </div>
              {isUser && (
                <div className="w-9 h-9 rounded-xl bg-coral-100 flex items-center justify-center shrink-0">
                  <User className="w-4 h-4 text-coral-700" />
                </div>
              )}
            </div>
          )
        })}

        {sending && (
          <div className="flex items-center gap-2 text-sm text-text-muted">
            <Loader2 className="w-4 h-4 animate-spin text-sage-600" />
            Waiting for model...
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="p-4 sm:p-6 border-t border-border bg-surface-elevated">
        <div className="flex gap-3">
          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Message the model..."
            rows={2}
            className="min-h-12 max-h-40 flex-1 resize-y px-4 py-3 bg-surface border border-border rounded-xl text-text focus:outline-none focus:ring-2 focus:ring-sage-500"
          />
          <button
            type="submit"
            disabled={!canSend}
            className="h-12 px-5 bg-sage-600 text-white rounded-xl font-display font-semibold hover:bg-sage-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2 shrink-0"
          >
            {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            Send
          </button>
        </div>
      </form>
    </section>
  )
}
