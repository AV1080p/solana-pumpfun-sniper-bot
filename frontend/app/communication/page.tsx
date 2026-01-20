'use client'

import { useState, useEffect } from 'react'
import { ChatInterface } from '@/components/ChatInterface'
import { AIChatbot } from '@/components/AIChatbot'
import { BroadcastAlerts } from '@/components/BroadcastAlerts'
import { communicationApi, ForumCategory, ForumPost, ForumReply } from '@/lib/communicationApi'
import { useAuth } from '@/contexts/AuthContext'
import toast from 'react-hot-toast'
import Link from 'next/link'

type TabType = 'chat' | 'forums'

export default function CommunicationPage() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState<TabType>('chat')
  const [aiChatbotOpen, setAiChatbotOpen] = useState(false)
  
  // Forum state
  const [categories, setCategories] = useState<ForumCategory[]>([])
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null)
  const [posts, setPosts] = useState<ForumPost[]>([])
  const [selectedPost, setSelectedPost] = useState<ForumPost | null>(null)
  const [replies, setReplies] = useState<ForumReply[]>([])
  const [newPostTitle, setNewPostTitle] = useState('')
  const [newPostContent, setNewPostContent] = useState('')
  const [newReplyContent, setNewReplyContent] = useState('')
  const [showNewPostForm, setShowNewPostForm] = useState(false)

  useEffect(() => {
    if (activeTab === 'forums') {
      fetchCategories()
      fetchPosts()
    }
  }, [activeTab, selectedCategory])

  useEffect(() => {
    if (selectedPost) {
      fetchReplies(selectedPost.id)
    }
  }, [selectedPost])

  const fetchCategories = async () => {
    try {
      const data = await communicationApi.getForumCategories()
      setCategories(data)
    } catch (error: any) {
      toast.error('Failed to load forum categories')
    }
  }

  const fetchPosts = async () => {
    try {
      const data = await communicationApi.getForumPosts({
        category_id: selectedCategory || undefined
      })
      setPosts(data)
    } catch (error: any) {
      toast.error('Failed to load forum posts')
    }
  }

  const fetchReplies = async (postId: number) => {
    try {
      const data = await communicationApi.getForumReplies(postId)
      setReplies(data)
    } catch (error: any) {
      toast.error('Failed to load replies')
    }
  }

  const handleCreatePost = async () => {
    if (!newPostTitle.trim() || !newPostContent.trim() || !selectedCategory) return

    try {
      await communicationApi.createForumPost({
        category_id: selectedCategory,
        title: newPostTitle,
        content: newPostContent
      })
      toast.success('Post created successfully')
      setNewPostTitle('')
      setNewPostContent('')
      setShowNewPostForm(false)
      fetchPosts()
    } catch (error: any) {
      toast.error('Failed to create post')
    }
  }

  const handleCreateReply = async () => {
    if (!newReplyContent.trim() || !selectedPost) return

    try {
      await communicationApi.createForumReply({
        post_id: selectedPost.id,
        content: newReplyContent
      })
      toast.success('Reply posted successfully')
      setNewReplyContent('')
      fetchReplies(selectedPost.id)
      fetchPosts() // Update reply count
    } catch (error: any) {
      toast.error('Failed to post reply')
    }
  }

  const handleViewPost = async (post: ForumPost) => {
    try {
      const fullPost = await communicationApi.getForumPost(post.id)
      setSelectedPost(fullPost)
    } catch (error: any) {
      toast.error('Failed to load post')
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <BroadcastAlerts />
      
      {/* Navigation */}
      <nav className="glass sticky top-0 z-40 border-b border-white/20 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-20">
            <Link href="/" className="flex items-center space-x-3 group">
              <div className="relative">
                <div className="text-4xl animate-float">🌴</div>
                <div className="absolute -top-1 -right-1 text-lg animate-pulse">✨</div>
              </div>
              <div>
                <h1 className="text-2xl font-bold gradient-text">TouristApp</h1>
                <p className="text-xs text-gray-500">Communication Hub</p>
              </div>
            </Link>
            <div className="flex items-center gap-6">
              <button
                onClick={() => setAiChatbotOpen(!aiChatbotOpen)}
                className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700"
              >
                {aiChatbotOpen ? 'Hide' : 'Show'} AI Assistant
              </button>
              <Link 
                href="/" 
                className="text-gray-700 hover:text-primary-600 font-medium transition-colors"
              >
                Back to Home
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Tabs */}
      <div className="glass border-b border-white/20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex gap-4">
            <button
              onClick={() => setActiveTab('chat')}
              className={`px-6 py-4 font-semibold transition-all relative ${
                activeTab === 'chat' ? 'text-primary-600' : 'text-gray-600 hover:text-primary-600'
              }`}
            >
              💬 Chat
              {activeTab === 'chat' && (
                <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-600"></span>
              )}
            </button>
            <button
              onClick={() => setActiveTab('forums')}
              className={`px-6 py-4 font-semibold transition-all relative ${
                activeTab === 'forums' ? 'text-primary-600' : 'text-gray-600 hover:text-primary-600'
              }`}
            >
              💭 Forums
              {activeTab === 'forums' && (
                <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-600"></span>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'chat' && (
          <div className="glass rounded-2xl p-6">
            <h2 className="text-2xl font-bold mb-4">In-App Chat</h2>
            <ChatInterface />
          </div>
        )}

        {activeTab === 'forums' && (
          <div className="space-y-6">
            {!selectedPost ? (
              <>
                {/* Categories and Posts List */}
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                  {/* Categories Sidebar */}
                  <div className="lg:col-span-1">
                    <div className="glass rounded-2xl p-4">
                      <h3 className="font-bold text-lg mb-4">Categories</h3>
                      <div className="space-y-2">
                        <button
                          onClick={() => setSelectedCategory(null)}
                          className={`w-full text-left p-2 rounded-lg ${
                            selectedCategory === null ? 'bg-primary-100 text-primary-700' : 'hover:bg-gray-100'
                          }`}
                        >
                          All Categories
                        </button>
                        {categories.map((cat) => (
                          <button
                            key={cat.id}
                            onClick={() => setSelectedCategory(cat.id)}
                            className={`w-full text-left p-2 rounded-lg ${
                              selectedCategory === cat.id ? 'bg-primary-100 text-primary-700' : 'hover:bg-gray-100'
                            }`}
                          >
                            {cat.name} ({cat.post_count || 0})
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Posts List */}
                  <div className="lg:col-span-3">
                    <div className="glass rounded-2xl p-6">
                      <div className="flex justify-between items-center mb-4">
                        <h3 className="text-2xl font-bold">Forum Posts</h3>
                        {selectedCategory && (
                          <button
                            onClick={() => setShowNewPostForm(!showNewPostForm)}
                            className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700"
                          >
                            + New Post
                          </button>
                        )}
                      </div>

                      {showNewPostForm && selectedCategory && (
                        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                          <input
                            type="text"
                            placeholder="Post title..."
                            value={newPostTitle}
                            onChange={(e) => setNewPostTitle(e.target.value)}
                            className="w-full px-4 py-2 border rounded-lg mb-2"
                          />
                          <textarea
                            placeholder="Post content..."
                            value={newPostContent}
                            onChange={(e) => setNewPostContent(e.target.value)}
                            rows={4}
                            className="w-full px-4 py-2 border rounded-lg mb-2"
                          />
                          <div className="flex gap-2">
                            <button
                              onClick={handleCreatePost}
                              className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700"
                            >
                              Post
                            </button>
                            <button
                              onClick={() => {
                                setShowNewPostForm(false)
                                setNewPostTitle('')
                                setNewPostContent('')
                              }}
                              className="bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400"
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      )}

                      <div className="space-y-4">
                        {posts.map((post) => (
                          <div
                            key={post.id}
                            onClick={() => handleViewPost(post)}
                            className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors"
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-2">
                                  {post.is_pinned && <span className="text-yellow-500">📌</span>}
                                  <h4 className="font-bold text-lg">{post.title}</h4>
                                </div>
                                <p className="text-gray-600 text-sm line-clamp-2">{post.content}</p>
                                <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                                  <span>By {post.author_email || 'Anonymous'}</span>
                                  <span>{post.reply_count} replies</span>
                                  <span>{post.view_count} views</span>
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              /* Post Detail View */
              <div className="glass rounded-2xl p-6">
                <button
                  onClick={() => setSelectedPost(null)}
                  className="mb-4 text-primary-600 hover:text-primary-800"
                >
                  ← Back to Posts
                </button>
                
                <div className="mb-6">
                  <h2 className="text-3xl font-bold mb-2">{selectedPost.title}</h2>
                  <div className="flex items-center gap-4 text-sm text-gray-500 mb-4">
                    <span>By {selectedPost.author_email || 'Anonymous'}</span>
                    <span>{selectedPost.view_count} views</span>
                    <span>{selectedPost.reply_count} replies</span>
                    <span>{new Date(selectedPost.created_at).toLocaleString()}</span>
                  </div>
                  <div className="prose max-w-none">
                    <p className="whitespace-pre-wrap">{selectedPost.content}</p>
                  </div>
                </div>

                <div className="border-t pt-6">
                  <h3 className="text-xl font-bold mb-4">Replies ({replies.length})</h3>
                  
                  <div className="space-y-4 mb-6">
                    {replies.map((reply) => (
                      <div key={reply.id} className="p-4 bg-gray-50 rounded-lg">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="font-semibold">{reply.author_email || 'Anonymous'}</span>
                          {reply.is_solution && (
                            <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs font-semibold">
                              ✓ Solution
                            </span>
                          )}
                          <span className="text-sm text-gray-500">
                            {new Date(reply.created_at).toLocaleString()}
                          </span>
                        </div>
                        <p className="whitespace-pre-wrap">{reply.content}</p>
                      </div>
                    ))}
                  </div>

                  {!selectedPost.is_locked && (
                    <div className="border-t pt-4">
                      <textarea
                        placeholder="Write a reply..."
                        value={newReplyContent}
                        onChange={(e) => setNewReplyContent(e.target.value)}
                        rows={4}
                        className="w-full px-4 py-2 border rounded-lg mb-2"
                      />
                      <button
                        onClick={handleCreateReply}
                        className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700"
                      >
                        Post Reply
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </section>

      {/* AI Chatbot */}
      {aiChatbotOpen && (
        <AIChatbot minimized={false} onToggle={() => setAiChatbotOpen(false)} />
      )}
      {!aiChatbotOpen && (
        <AIChatbot minimized={true} onToggle={() => setAiChatbotOpen(true)} />
      )}
    </main>
  )
}

