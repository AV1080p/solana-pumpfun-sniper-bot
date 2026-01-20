import { api } from './api'

export interface ChatRoom {
  id: number
  room_type: string
  name?: string
  provider_id?: number
  guide_id?: number
  is_active: boolean
  created_at: string
}

export interface Message {
  id: number
  room_id: number
  sender_id?: number
  sender_email?: string
  content: string
  message_type: string
  translated_content?: string
  original_language?: string
  translated_language?: string
  is_read: boolean
  created_at: string
}

export interface AIConversation {
  id: number
  user_id: number
  session_id: string
  created_at: string
  updated_at: string
}

export interface AIMessage {
  id: number
  conversation_id: number
  role: string
  content: string
  created_at: string
}

export interface CallSession {
  id: number
  call_type: string
  initiator_id?: number
  recipient_id?: number
  guide_id?: number
  session_id: string
  status: string
  started_at?: string
  ended_at?: string
  duration_seconds?: number
  created_at: string
}

export interface BroadcastAlert {
  id: number
  alert_type: string
  priority: string
  title: string
  message: string
  target_audience: string
  is_active: boolean
  expires_at?: string
  created_at: string
  viewed?: boolean
}

export interface ForumCategory {
  id: number
  name: string
  description?: string
  slug: string
  order: number
  is_active: boolean
  post_count?: number
}

export interface ForumPost {
  id: number
  category_id: number
  author_id?: number
  author_email?: string
  title: string
  content: string
  slug?: string
  is_pinned: boolean
  is_locked: boolean
  view_count: number
  reply_count: number
  last_reply_at?: string
  created_at: string
}

export interface ForumReply {
  id: number
  post_id: number
  author_id?: number
  author_email?: string
  parent_reply_id?: number
  content: string
  is_solution: boolean
  created_at: string
}

export const communicationApi = {
  // Chat Rooms
  async createChatRoom(data: {
    room_type: string
    provider_id?: number
    guide_id?: number
    name?: string
  }): Promise<ChatRoom> {
    const response = await api.post('/communication/chat/rooms', data)
    return response.data
  },

  async getChatRooms(): Promise<ChatRoom[]> {
    const response = await api.get('/communication/chat/rooms')
    return response.data
  },

  // Messages
  async sendMessage(data: {
    room_id: number
    content: string
    message_type?: string
    translate_to?: string
  }): Promise<Message> {
    const response = await api.post('/communication/chat/messages', data)
    return response.data
  },

  async getMessages(roomId: number, params?: {
    limit?: number
    offset?: number
  }): Promise<Message[]> {
    const response = await api.get(`/communication/chat/rooms/${roomId}/messages`, { params })
    return response.data
  },

  // AI Chatbot
  async aiChat(data: {
    message: string
    session_id?: string
    context?: any
  }): Promise<{ success: boolean; response: string; session_id: string; message: AIMessage }> {
    const response = await api.post('/communication/ai/chat', data)
    return response.data
  },

  async getAIConversation(sessionId: string): Promise<AIMessage[]> {
    const response = await api.get(`/communication/ai/conversations/${sessionId}`)
    return response.data
  },

  // Translation
  async translateText(data: {
    text: string
    target_language: string
    source_language?: string
  }): Promise<{ success: boolean; translated_text: string; original_text: string }> {
    const response = await api.post('/communication/translate', data)
    return response.data
  },

  // Calls
  async initiateCall(data: {
    call_type: string
    recipient_id?: number
    guide_id?: number
    room_id?: number
  }): Promise<CallSession> {
    const response = await api.post('/communication/calls/initiate', data)
    return response.data
  },

  async updateCallStatus(sessionId: string, status: string): Promise<CallSession> {
    const response = await api.patch(`/communication/calls/${sessionId}/status`, null, {
      params: { status }
    })
    return response.data
  },

  // Broadcasts
  async getBroadcasts(): Promise<BroadcastAlert[]> {
    const response = await api.get('/communication/broadcasts')
    return response.data
  },

  async markBroadcastViewed(alertId: number): Promise<{ success: boolean }> {
    const response = await api.post(`/communication/broadcasts/${alertId}/view`)
    return response.data
  },

  // Forums
  async getForumCategories(): Promise<ForumCategory[]> {
    const response = await api.get('/communication/forums/categories')
    return response.data
  },

  async getForumPosts(params?: {
    category_id?: number
    limit?: number
    offset?: number
  }): Promise<ForumPost[]> {
    const response = await api.get('/communication/forums/posts', { params })
    return response.data
  },

  async getForumPost(postId: number): Promise<ForumPost> {
    const response = await api.get(`/communication/forums/posts/${postId}`)
    return response.data
  },

  async createForumPost(data: {
    category_id: number
    title: string
    content: string
  }): Promise<ForumPost> {
    const response = await api.post('/communication/forums/posts', data)
    return response.data
  },

  async getForumReplies(postId: number): Promise<ForumReply[]> {
    const response = await api.get(`/communication/forums/posts/${postId}/replies`)
    return response.data
  },

  async createForumReply(data: {
    post_id: number
    content: string
    parent_reply_id?: number
  }): Promise<ForumReply> {
    const response = await api.post('/communication/forums/replies', data)
    return response.data
  }
}

