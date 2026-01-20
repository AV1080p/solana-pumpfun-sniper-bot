'use client'

import { useState, useEffect, useRef } from 'react'
import { api } from '@/lib/api'
import toast from 'react-hot-toast'

interface Message {
  role: 'user' | 'assistant'
  content: string
  confidence_score?: number
  suggested_faqs?: Array<{ id: number; question: string }>
  created_at?: string
}

interface AISupportAssistantProps {
  onEscalate?: () => void
}

export default function AISupportAssistant({ onEscalate }: AISupportAssistantProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [suggestions, setSuggestions] = useState<string[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      role: 'user',
      content: input
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const response = await api.post('/support/ai/chat', {
        message: input,
        session_id: sessionId,
        context: {}
      })

      if (!sessionId && response.data.session_id) {
        setSessionId(response.data.session_id)
      }

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.data.message,
        confidence_score: response.data.confidence_score,
        suggested_faqs: response.data.suggested_faqs
      }

      setMessages(prev => [...prev, assistantMessage])

      if (response.data.suggestions) {
        setSuggestions(response.data.suggestions)
      }

      if (response.data.escalate_to_human) {
        toast.info('Escalating to human support...')
        onEscalate?.()
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to get response')
      setMessages(prev => prev.slice(0, -1)) // Remove user message on error
    } finally {
      setIsLoading(false)
    }
  }

  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion)
  }

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-4 rounded-t-lg">
        <h3 className="text-lg font-semibold">AI Support Assistant</h3>
        <p className="text-sm opacity-90">Ask me anything, I'm here to help!</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <p className="text-lg font-medium mb-2">👋 Hello! How can I help you today?</p>
            <p className="text-sm">Try asking about bookings, payments, or account settings.</p>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-3 ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-800'
              }`}
            >
              <p className="text-sm">{message.content}</p>
              {message.confidence_score !== undefined && message.role === 'assistant' && (
                <p className="text-xs mt-1 opacity-70">
                  Confidence: {Math.round(message.confidence_score * 100)}%
                </p>
              )}
              {message.suggested_faqs && message.suggested_faqs.length > 0 && (
                <div className="mt-2 space-y-1">
                  <p className="text-xs font-semibold">Related FAQs:</p>
                  {message.suggested_faqs.map((faq) => (
                    <button
                      key={faq.id}
                      className="text-xs underline block"
                      onClick={() => {
                        // Navigate to FAQ or show FAQ modal
                        toast.info(`FAQ: ${faq.question}`)
                      }}
                    >
                      {faq.question}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg p-3">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggestions */}
      {suggestions.length > 0 && (
        <div className="px-4 py-2 border-t border-gray-200">
          <p className="text-xs text-gray-500 mb-2">Suggestions:</p>
          <div className="flex flex-wrap gap-2">
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => handleSuggestionClick(suggestion)}
                className="text-xs bg-blue-50 text-blue-600 px-3 py-1 rounded-full hover:bg-blue-100 transition"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <form onSubmit={handleSend} className="p-4 border-t border-gray-200">
        <div className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your question..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  )
}

