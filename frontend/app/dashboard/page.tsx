'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { api } from '@/lib/api'
import { ShieldIcon, SparklesIcon, CheckIcon, TrendingUpIcon, UsersIcon, CameraIcon, GlobeIcon } from '@/components/Icons'
import toast from 'react-hot-toast'

interface AccountSettings {
  email: string
  full_name?: string
  username?: string
  phone_number?: string
  avatar_url?: string
  is_verified: boolean
  created_at?: string
}

interface Invoice {
  id: number
  invoice_number: string
  amount: number
  total_amount: number
  currency: string
  status: string
  created_at: string
  due_date?: string
}

interface Analytics {
  total_bookings: number
  total_spent: number
  favorite_destinations: Array<{ location: string; count: number }>
  booking_trends: Record<string, number>
  payment_methods_used: Record<string, number>
  recent_activity: Array<{ type: string; description: string; date: string }>
}

interface Feedback {
  id: number
  feedback_type: string
  subject: string
  message: string
  rating?: number
  status: string
  created_at: string
}

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<'overview' | 'account' | 'billing' | 'analytics' | 'docs' | 'support' | 'feedback'>('overview')
  const [accountSettings, setAccountSettings] = useState<AccountSettings | null>(null)
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [analytics, setAnalytics] = useState<Analytics | null>(null)
  const [feedback, setFeedback] = useState<Feedback[]>([])
  const [loading, setLoading] = useState(true)
  const [userEmail, setUserEmail] = useState<string>('')
  
  // Form states
  const [accountForm, setAccountForm] = useState({
    full_name: '',
    username: '',
    phone_number: '',
    avatar_url: ''
  })
  const [feedbackForm, setFeedbackForm] = useState({
    feedback_type: 'general',
    subject: '',
    message: '',
    rating: 5
  })

  useEffect(() => {
    // Get user email from localStorage or use a default for demo
    const email = localStorage.getItem('user_email') || 'demo@example.com'
    setUserEmail(email)
    fetchDashboardData(email)
  }, [])

  const fetchDashboardData = async (email: string) => {
    setLoading(true)
    try {
      const [accountRes, invoicesRes, analyticsRes, feedbackRes] = await Promise.all([
        api.get(`/dashboard/account?user_email=${email}`).catch(() => ({ data: null })),
        api.get(`/dashboard/invoices?user_email=${email}`).catch(() => ({ data: [] })),
        api.get(`/dashboard/analytics?user_email=${email}`).catch(() => ({ data: null })),
        api.get(`/dashboard/feedback?user_email=${email}`).catch(() => ({ data: [] }))
      ])
      
      if (accountRes.data) setAccountSettings(accountRes.data)
      if (accountRes.data) {
        setAccountForm({
          full_name: accountRes.data.full_name || '',
          username: accountRes.data.username || '',
          phone_number: accountRes.data.phone_number || '',
          avatar_url: accountRes.data.avatar_url || ''
        })
      }
      setInvoices(invoicesRes.data || [])
      setAnalytics(analyticsRes.data)
      setFeedback(feedbackRes.data || [])
    } catch (error) {
      console.error('Error fetching dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleAccountUpdate = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await api.patch(`/dashboard/account?user_email=${userEmail}`, accountForm)
      toast.success('Account settings updated successfully!')
      fetchDashboardData(userEmail)
    } catch (error) {
      toast.error('Failed to update account settings')
    }
  }

  const handleFeedbackSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await api.post(`/dashboard/feedback?user_email=${userEmail}`, feedbackForm)
      toast.success('Feedback submitted successfully!')
      setFeedbackForm({ feedback_type: 'general', subject: '', message: '', rating: 5 })
      fetchDashboardData(userEmail)
    } catch (error) {
      toast.error('Failed to submit feedback')
    }
  }

  return (
    <main className="min-h-screen">
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
                <p className="text-xs text-gray-500 flex items-center gap-1">
                  <span>Customer Dashboard</span>
                  <span className="animate-pulse">📊</span>
                </p>
              </div>
            </Link>
            <div className="flex items-center gap-6">
              <Link 
                href="/" 
                className="text-gray-700 hover:text-primary-600 font-medium transition-colors"
              >
                Home
              </Link>
              <Link 
                href="/bookings" 
                className="text-gray-700 hover:text-primary-600 font-medium transition-colors"
              >
                Bookings
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Tabs */}
      <div className="glass border-b border-white/20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex gap-4 overflow-x-auto">
            {[
              { id: 'overview', label: 'Overview', icon: '📊' },
              { id: 'account', label: 'Account', icon: '👤' },
              { id: 'billing', label: 'Billing', icon: '💳' },
              { id: 'analytics', label: 'Analytics', icon: '📈' },
              { id: 'docs', label: 'Documentation', icon: '📚' },
              { id: 'support', label: 'Support', icon: '💬' },
              { id: 'feedback', label: 'Feedback', icon: '💡' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`px-6 py-4 font-semibold transition-all relative whitespace-nowrap flex items-center gap-2 ${
                  activeTab === tab.id
                    ? 'text-primary-600'
                    : 'text-gray-600 hover:text-primary-600'
                }`}
              >
                <span>{tab.icon}</span>
                <span>{tab.label}</span>
                {activeTab === tab.id && (
                  <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-600"></span>
                )}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="relative">
              <div className="w-16 h-16 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin"></div>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-2xl">🌴</span>
              </div>
            </div>
            <p className="mt-4 text-gray-600 font-medium">Loading dashboard...</p>
          </div>
        ) : activeTab === 'overview' ? (
          <div className="space-y-6">
            <h2 className="text-3xl font-bold mb-6 gradient-text">Dashboard Overview</h2>
            
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="glass rounded-2xl p-6 hover:shadow-xl transition-all">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-gray-600 font-medium">Total Bookings</h3>
                  <CameraIcon size={24} className="text-primary-500" />
                </div>
                <p className="text-3xl font-bold gradient-text">{analytics?.total_bookings || 0}</p>
              </div>
              
              <div className="glass rounded-2xl p-6 hover:shadow-xl transition-all">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-gray-600 font-medium">Total Spent</h3>
                  <TrendingUpIcon size={24} className="text-green-500" />
                </div>
                <p className="text-3xl font-bold gradient-text">${analytics?.total_spent.toFixed(2) || '0.00'}</p>
              </div>
              
              <div className="glass rounded-2xl p-6 hover:shadow-xl transition-all">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-gray-600 font-medium">Invoices</h3>
                  <UsersIcon size={24} className="text-purple-500" />
                </div>
                <p className="text-3xl font-bold gradient-text">{invoices.length}</p>
              </div>
              
              <div className="glass rounded-2xl p-6 hover:shadow-xl transition-all">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-gray-600 font-medium">Feedback</h3>
                  <SparklesIcon size={24} className="text-yellow-500" />
                </div>
                <p className="text-3xl font-bold gradient-text">{feedback.length}</p>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="glass rounded-2xl p-6">
              <h3 className="text-2xl font-bold mb-4">Recent Activity</h3>
              <div className="space-y-3">
                {analytics?.recent_activity.slice(0, 5).map((activity, index) => (
                  <div key={index} className="flex items-center gap-4 p-3 bg-gray-50 rounded-xl">
                    <span className="text-2xl">📅</span>
                    <div className="flex-1">
                      <p className="font-semibold">{activity.description}</p>
                      <p className="text-sm text-gray-600">
                        {new Date(activity.date).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                )) || <p className="text-gray-600">No recent activity</p>}
              </div>
            </div>
          </div>
        ) : activeTab === 'account' ? (
          <div className="space-y-6">
            <h2 className="text-3xl font-bold mb-6 gradient-text">Account Settings</h2>
            <div className="glass rounded-2xl p-8">
              <form onSubmit={handleAccountUpdate} className="space-y-6">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Email
                  </label>
                  <input
                    type="email"
                    value={accountSettings?.email || userEmail}
                    disabled
                    className="w-full px-4 py-3 rounded-xl border border-gray-300 bg-gray-100 text-gray-600"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Full Name
                  </label>
                  <input
                    type="text"
                    value={accountForm.full_name}
                    onChange={(e) => setAccountForm({ ...accountForm, full_name: e.target.value })}
                    className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    placeholder="Your full name"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Username
                  </label>
                  <input
                    type="text"
                    value={accountForm.username}
                    onChange={(e) => setAccountForm({ ...accountForm, username: e.target.value })}
                    className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    placeholder="Choose a username"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Phone Number
                  </label>
                  <input
                    type="tel"
                    value={accountForm.phone_number}
                    onChange={(e) => setAccountForm({ ...accountForm, phone_number: e.target.value })}
                    className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    placeholder="+1 (555) 123-4567"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Avatar URL
                  </label>
                  <input
                    type="url"
                    value={accountForm.avatar_url}
                    onChange={(e) => setAccountForm({ ...accountForm, avatar_url: e.target.value })}
                    className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    placeholder="https://example.com/avatar.jpg"
                  />
                </div>
                
                <button
                  type="submit"
                  className="w-full bg-gradient-to-r from-primary-600 to-purple-600 text-white py-4 px-6 rounded-xl hover:from-primary-700 hover:to-purple-700 transition-all font-semibold shadow-lg hover:shadow-glow"
                >
                  Save Changes
                </button>
              </form>
            </div>
          </div>
        ) : activeTab === 'billing' ? (
          <div className="space-y-6">
            <h2 className="text-3xl font-bold mb-6 gradient-text">Billing History & Invoices</h2>
            {invoices.length === 0 ? (
              <div className="glass rounded-2xl p-12 text-center">
                <span className="text-6xl mb-4 block">💳</span>
                <h3 className="text-2xl font-bold text-gray-900 mb-2">No invoices yet</h3>
                <p className="text-gray-600">Your invoices will appear here after you make bookings</p>
              </div>
            ) : (
              <div className="glass rounded-2xl overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Invoice #</th>
                        <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Amount</th>
                        <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Status</th>
                        <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Date</th>
                        <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {invoices.map((invoice) => (
                        <tr key={invoice.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 text-sm font-semibold">{invoice.invoice_number}</td>
                          <td className="px-6 py-4 text-sm">${invoice.total_amount.toFixed(2)} {invoice.currency}</td>
                          <td className="px-6 py-4 text-sm">
                            <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                              invoice.status === 'paid' ? 'bg-green-100 text-green-800' :
                              invoice.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                              'bg-red-100 text-red-800'
                            }`}>
                              {invoice.status}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-sm">
                            {new Date(invoice.created_at).toLocaleDateString()}
                          </td>
                          <td className="px-6 py-4 text-sm">
                            <button className="text-primary-600 hover:text-primary-700 font-semibold">
                              View
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        ) : activeTab === 'analytics' ? (
          <div className="space-y-6">
            <h2 className="text-3xl font-bold mb-6 gradient-text">Usage Analytics</h2>
            
            {analytics ? (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="glass rounded-2xl p-6">
                    <h3 className="text-xl font-bold mb-4">Favorite Destinations</h3>
                    <div className="space-y-3">
                      {analytics.favorite_destinations.map((dest, index) => (
                        <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                          <span className="font-semibold">{dest.location}</span>
                          <span className="text-primary-600 font-bold">{dest.count} bookings</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <div className="glass rounded-2xl p-6">
                    <h3 className="text-xl font-bold mb-4">Payment Methods Used</h3>
                    <div className="space-y-3">
                      {Object.entries(analytics.payment_methods_used).map(([method, count]) => (
                        <div key={method} className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                          <span className="font-semibold capitalize">{method}</span>
                          <span className="text-primary-600 font-bold">{count} times</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
                
                <div className="glass rounded-2xl p-6">
                  <h3 className="text-xl font-bold mb-4">Booking Trends</h3>
                  <div className="space-y-2">
                    {Object.entries(analytics.booking_trends).map(([month, count]) => (
                      <div key={month} className="flex items-center gap-4">
                        <span className="w-24 text-sm font-medium">{month}</span>
                        <div className="flex-1 bg-gray-200 rounded-full h-4">
                          <div 
                            className="bg-primary-600 h-4 rounded-full"
                            style={{ width: `${(count / Math.max(...Object.values(analytics.booking_trends))) * 100}%` }}
                          ></div>
                        </div>
                        <span className="w-12 text-sm font-semibold text-right">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <div className="glass rounded-2xl p-12 text-center">
                <span className="text-6xl mb-4 block">📈</span>
                <h3 className="text-2xl font-bold text-gray-900 mb-2">No analytics data yet</h3>
                <p className="text-gray-600">Start booking tours to see your usage analytics</p>
              </div>
            )}
          </div>
        ) : activeTab === 'docs' ? (
          <div className="space-y-6">
            <h2 className="text-3xl font-bold mb-6 gradient-text">Documentation</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {[
                { title: 'Getting Started Guide', icon: '🚀', description: 'Learn how to book your first tour' },
                { title: 'Payment Methods', icon: '💳', description: 'Information about payment options' },
                { title: 'API Documentation', icon: '🔧', description: 'Complete API reference' },
                { title: 'FAQ', icon: '❓', description: 'Frequently asked questions' }
              ].map((doc, index) => (
                <Link
                  key={index}
                  href="/support"
                  className="glass rounded-2xl p-6 hover:shadow-xl transition-all group"
                >
                  <div className="text-4xl mb-4">{doc.icon}</div>
                  <h3 className="text-xl font-bold mb-2 group-hover:text-primary-600 transition-colors">
                    {doc.title}
                  </h3>
                  <p className="text-gray-600">{doc.description}</p>
                </Link>
              ))}
            </div>
          </div>
        ) : activeTab === 'support' ? (
          <div className="space-y-6">
            <h2 className="text-3xl font-bold mb-6 gradient-text">Support Center</h2>
            <div className="glass rounded-2xl p-8">
              <p className="text-lg text-gray-700 mb-6">
                Need help? Visit our support page or contact us directly.
              </p>
              <Link
                href="/support"
                className="inline-flex items-center gap-2 bg-gradient-to-r from-primary-600 to-purple-600 text-white py-4 px-8 rounded-xl hover:from-primary-700 hover:to-purple-700 transition-all font-semibold shadow-lg hover:shadow-glow"
              >
                <GlobeIcon size={20} className="text-white" />
                <span>Go to Support Page</span>
                <span>→</span>
              </Link>
            </div>
          </div>
        ) : activeTab === 'feedback' ? (
          <div className="space-y-6">
            <h2 className="text-3xl font-bold mb-6 gradient-text">Submit Feedback</h2>
            
            <div className="glass rounded-2xl p-8">
              <form onSubmit={handleFeedbackSubmit} className="space-y-6">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Feedback Type
                  </label>
                  <select
                    value={feedbackForm.feedback_type}
                    onChange={(e) => setFeedbackForm({ ...feedbackForm, feedback_type: e.target.value })}
                    className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  >
                    <option value="general">General Feedback</option>
                    <option value="bug">Bug Report</option>
                    <option value="feature">Feature Request</option>
                    <option value="complaint">Complaint</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Subject
                  </label>
                  <input
                    type="text"
                    required
                    value={feedbackForm.subject}
                    onChange={(e) => setFeedbackForm({ ...feedbackForm, subject: e.target.value })}
                    className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    placeholder="Brief description"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Message
                  </label>
                  <textarea
                    required
                    rows={6}
                    value={feedbackForm.message}
                    onChange={(e) => setFeedbackForm({ ...feedbackForm, message: e.target.value })}
                    className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
                    placeholder="Tell us what you think..."
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Rating (1-5)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="5"
                    value={feedbackForm.rating}
                    onChange={(e) => setFeedbackForm({ ...feedbackForm, rating: parseInt(e.target.value) })}
                    className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>
                
                <button
                  type="submit"
                  className="w-full bg-gradient-to-r from-primary-600 to-purple-600 text-white py-4 px-6 rounded-xl hover:from-primary-700 hover:to-purple-700 transition-all font-semibold shadow-lg hover:shadow-glow"
                >
                  Submit Feedback
                </button>
              </form>
            </div>
            
            {feedback.length > 0 && (
              <div className="glass rounded-2xl p-6">
                <h3 className="text-xl font-bold mb-4">Your Previous Feedback</h3>
                <div className="space-y-4">
                  {feedback.map((item) => (
                    <div key={item.id} className="p-4 bg-gray-50 rounded-xl">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold">{item.subject}</span>
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                          item.status === 'resolved' ? 'bg-green-100 text-green-800' :
                          item.status === 'in_progress' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {item.status}
                        </span>
                      </div>
                      <p className="text-gray-600 text-sm">{item.message}</p>
                      <p className="text-xs text-gray-500 mt-2">
                        {new Date(item.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : null}
      </section>
    </main>
  )
}

