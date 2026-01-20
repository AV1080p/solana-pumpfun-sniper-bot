'use client'

import { useState, useEffect, useRef } from 'react'
import { communicationApi, ChatRoom, Message } from '@/lib/communicationApi'
import { useAuth } from '@/contexts/AuthContext'
import toast from 'react-hot-toast'

interface ChatInterfaceProps {
  roomId?: number
  onRoomSelect?: (roomId: number) => void
}

export function ChatInterface({ roomId, onRoomSelect }: ChatInterfaceProps) {
  const { user } = useAuth()
  const [rooms, setRooms] = useState<ChatRoom[]>([])
  const [selectedRoom, setSelectedRoom] = useState<number | null>(roomId || null)
  const [messages, setMessages] = useState<Message[]>([])
  const [newMessage, setNewMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [translateTo, setTranslateTo] = useState<string>('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetchRooms()
    if (selectedRoom) {
      fetchMessages(selectedRoom)
      // Poll for new messages
      const interval = setInterval(() => {
        fetchMessages(selectedRoom)
      }, 3000)
      return () => clearInterval(interval)
    }
  }, [selectedRoom])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const fetchRooms = async () => {
    try {
      const data = await communicationApi.getChatRooms()
      setRooms(data)
    } catch (error: any) {
      toast.error('Failed to load chat rooms')
    }
  }

  const fetchMessages = async (roomId: number) => {
    try {
      const data = await communicationApi.getMessages(roomId)
      setMessages(data)
    } catch (error: any) {
      console.error('Failed to load messages:', error)
    }
  }

  const handleSendMessage = async () => {
    if (!newMessage.trim() || !selectedRoom) return

    setLoading(true)
    try {
      await communicationApi.sendMessage({
        room_id: selectedRoom,
        content: newMessage,
        translate_to: translateTo || undefined
      })
      setNewMessage('')
      await fetchMessages(selectedRoom)
    } catch (error: any) {
      toast.error('Failed to send message')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateRoom = async (providerId?: number) => {
    try {
      const room = await communicationApi.createChatRoom({
        room_type: providerId ? 'user_provider' : 'user_guide',
        provider_id: providerId
      })
      setRooms([room, ...rooms])
      setSelectedRoom(room.id)
      if (onRoomSelect) onRoomSelect(room.id)
    } catch (error: any) {
      toast.error('Failed to create chat room')
    }
  }

  return (
    <div className="flex h-[600px] bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Sidebar - Chat Rooms */}
      <div className="w-1/3 border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <h3 className="font-bold text-lg">Chats</h3>
          <button
            onClick={() => handleCreateRoom()}
            className="mt-2 w-full bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700"
          >
            + New Chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto">
          {rooms.map((room) => (
            <button
              key={room.id}
              onClick={() => {
                setSelectedRoom(room.id)
                if (onRoomSelect) onRoomSelect(room.id)
              }}
              className={`w-full p-4 text-left hover:bg-gray-50 border-b border-gray-100 ${
                selectedRoom === room.id ? 'bg-primary-50 border-primary-200' : ''
              }`}
            >
              <p className="font-semibold">{room.name || `Chat ${room.id}`}</p>
              <p className="text-sm text-gray-500">{room.room_type}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {selectedRoom ? (
          <>
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.sender_id === user?.id ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                      message.sender_id === user?.id
                        ? 'bg-primary-600 text-white'
                        : 'bg-gray-200 text-gray-800'
                    }`}
                  >
                    <p className="text-sm font-semibold mb-1">
                      {message.sender_email || 'System'}
                    </p>
                    <p className="text-sm">{message.content}</p>
                    {message.translated_content && (
                      <p className="text-xs mt-2 opacity-75 italic">
                        {message.translated_content}
                      </p>
                    )}
                    <p className="text-xs mt-1 opacity-75">
                      {new Date(message.created_at).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="border-t border-gray-200 p-4">
              <div className="flex gap-2 mb-2">
                <select
                  value={translateTo}
                  onChange={(e) => setTranslateTo(e.target.value)}
                  className="px-3 py-2 border rounded-lg text-sm"
                >
                  <option value="">No Translation</option>
                  <option value="es">Spanish</option>
                  <option value="fr">French</option>
                  <option value="de">German</option>
                  <option value="it">Italian</option>
                  <option value="pt">Portuguese</option>
                </select>
              </div>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                  placeholder="Type a message..."
                  className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  disabled={loading}
                />
                <button
                  onClick={handleSendMessage}
                  disabled={loading || !newMessage.trim()}
                  className="bg-primary-600 text-white px-6 py-2 rounded-lg hover:bg-primary-700 disabled:opacity-50"
                >
                  Send
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            <p>Select a chat or create a new one</p>
          </div>
        )}
      </div>
    </div>
  )
}

