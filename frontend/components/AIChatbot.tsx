'use client'

import { useState, useEffect, useRef } from 'react'
import { communicationApi, AIMessage } from '@/lib/communicationApi'
import { useAuth } from '@/contexts/AuthContext'
import toast from 'react-hot-toast'

interface AIChatbotProps {
  minimized?: boolean
  onToggle?: () => void
}

export function AIChatbot({ minimized = false, onToggle }: AIChatbotProps) {
  const { user } = useAuth()
  const [messages, setMessages] = useState<AIMessage[]>([])
  const [input, setInput] = useState('')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMessage = input
    setInput('')
    setLoading(true)

    // Add user message to UI immediately
    const tempUserMsg: AIMessage = {
      id: Date.now(),
      conversation_id: 0,
      role: 'user',
      content: userMessage,
      created_at: new Date().toISOString()
    }
    setMessages(prev => [...prev, tempUserMsg])

    try {
      const response = await communicationApi.aiChat({
        message: userMessage,
        session_id: sessionId || undefined
      })

      if (!sessionId) {
        setSessionId(response.session_id)
      }

      // Add AI response
      const aiMsg: AIMessage = {
        id: response.message.id,
        conversation_id: response.message.conversation_id,
        role: 'assistant',
        content: response.response,
        created_at: response.message.created_at
      }
      setMessages(prev => [...prev, aiMsg])
    } catch (error: any) {
      toast.error('Failed to get AI response')
      // Remove temp message on error
      setMessages(prev => prev.filter(m => m.id !== tempUserMsg.id))
    } finally {
      setLoading(false)
    }
  }

  const handleClear = () => {
    setMessages([])
    setSessionId(null)
  }

  if (minimized) {
    return (
      <div className="fixed bottom-4 right-4 z-50">
        <button
          onClick={onToggle}
          className="bg-primary-600 text-white rounded-full p-4 shadow-lg hover:bg-primary-700 transition-all"
        >
          <span className="text-2xl">🤖</span>
        </button>
      </div>
    )
  }

  return (
    <div className="fixed bottom-4 right-4 w-96 h-[600px] bg-white rounded-lg shadow-2xl flex flex-col z-50 border border-gray-200">
      {/* Header */}
      <div className="bg-primary-600 text-white p-4 rounded-t-lg flex justify-between items-center">
        <div>
          <h3 className="font-bold text-lg">AI Assistant</h3>
          <p className="text-sm opacity-90">How can I help you?</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleClear}
            className="text-white hover:bg-primary-700 p-2 rounded"
            title="Clear chat"
          >
            🗑️
          </button>
          {onToggle && (
            <button
              onClick={onToggle}
              className="text-white hover:bg-primary-700 p-2 rounded"
              title="Minimize"
            >
              ➖
            </button>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <p className="text-2xl mb-2">👋</p>
            <p>Start a conversation with our AI assistant!</p>
            <p className="text-sm mt-2">Ask about tours, bookings, or anything else.</p>
          </div>
        )}
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] px-4 py-2 rounded-lg ${
                message.role === 'user'
                  ? 'bg-primary-600 text-white'
                  : 'bg-white text-gray-800 border border-gray-200'
              }`}
            >
              <p className="text-sm whitespace-pre-wrap">{message.content}</p>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 px-4 py-2 rounded-lg">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 p-4 bg-white">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask me anything..."
            className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            disabled={loading}
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  )
}

