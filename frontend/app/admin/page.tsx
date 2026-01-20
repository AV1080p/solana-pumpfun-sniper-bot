'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { adminApi, AdminAnalytics, UserList, BillingSummary, UsageReport, SystemHealth, AuditLog } from '@/lib/adminApi'
import { CheckIcon, SparklesIcon, CameraIcon, UsersIcon, TrendingUpIcon, ShieldIcon } from '@/components/Icons'
import toast from 'react-hot-toast'
import { useAuth } from '@/contexts/AuthContext'

type TabType = 'analytics' | 'users' | 'billing' | 'reports' | 'health' | 'audit'

export default function AdminPage() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState<TabType>('analytics')
  const [loading, setLoading] = useState(true)
  
  // Analytics data
  const [analytics, setAnalytics] = useState<AdminAnalytics | null>(null)
  
  // User management
  const [users, setUsers] = useState<UserList[]>([])
  const [userSearch, setUserSearch] = useState('')
  const [selectedUser, setSelectedUser] = useState<UserList | null>(null)
  
  // Billing data
  const [billing, setBilling] = useState<BillingSummary | null>(null)
  
  // Reports data
  const [reports, setReports] = useState<UsageReport | null>(null)
  
  // System health
  const [health, setHealth] = useState<SystemHealth | null>(null)
  
  // Audit logs
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([])
  const [auditFilters, setAuditFilters] = useState({
    action: '',
    resource_type: '',
    limit: 100
  })

  useEffect(() => {
    if (user?.role !== 'admin') {
      toast.error('Access denied. Admin privileges required.')
      return
    }
    fetchData()
    // Set up auto-refresh for analytics
    const interval = setInterval(() => {
      if (activeTab === 'analytics' || activeTab === 'health') {
        fetchData()
      }
    }, 30000) // Refresh every 30 seconds
    
    return () => clearInterval(interval)
  }, [activeTab, user])

  const fetchData = async () => {
    setLoading(true)
    try {
      switch (activeTab) {
        case 'analytics':
          const analyticsData = await adminApi.getAnalytics()
          setAnalytics(analyticsData)
          break
        case 'users':
          const usersData = await adminApi.getUsers({ search: userSearch || undefined })
          setUsers(usersData)
          break
        case 'billing':
          const billingData = await adminApi.getBillingSummary()
          setBilling(billingData)
          break
        case 'reports':
          const reportsData = await adminApi.getUsageReport()
          setReports(reportsData)
          break
        case 'health':
          const healthData = await adminApi.getSystemHealth()
          setHealth(healthData)
          break
        case 'audit':
          const auditData = await adminApi.getAuditLogs({
            action: auditFilters.action || undefined,
            resource_type: auditFilters.resource_type || undefined,
            limit: auditFilters.limit
          })
          setAuditLogs(auditData)
          break
      }
    } catch (error: any) {
      console.error('Error fetching data:', error)
      toast.error(error.response?.data?.detail || 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  const handleUpdateUser = async (userId: number, updates: Partial<UserList>) => {
    try {
      await adminApi.updateUser(userId, updates)
      toast.success('User updated successfully')
      fetchData()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to update user')
    }
  }

  const handleDeleteUser = async (userId: number) => {
    if (!confirm('Are you sure you want to delete this user?')) return
    try {
      await adminApi.deleteUser(userId)
      toast.success('User deleted successfully')
      fetchData()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to delete user')
    }
  }

  if (user?.role !== 'admin') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Access Denied</h1>
          <p className="text-gray-600">Admin privileges required</p>
          <Link href="/" className="text-primary-600 hover:underline mt-4 inline-block">
            Return to Home
          </Link>
        </div>
      </div>
    )
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
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
                  <span>Administration Dashboard</span>
                  <span className="animate-pulse">🔐</span>
                </p>
              </div>
            </Link>
            <div className="flex items-center gap-6">
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
          <div className="flex gap-4 overflow-x-auto">
            {([
              { id: 'analytics', label: 'Analytics', icon: '📊' },
              { id: 'users', label: 'Users', icon: '👥' },
              { id: 'billing', label: 'Billing', icon: '💳' },
              { id: 'reports', label: 'Reports', icon: '📈' },
              { id: 'health', label: 'Health', icon: '🏥' },
              { id: 'audit', label: 'Audit Logs', icon: '📝' }
            ] as const).map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as TabType)}
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
            <p className="mt-4 text-gray-600 font-medium">Loading...</p>
          </div>
        ) : (
          <>
            {/* Analytics Dashboard */}
            {activeTab === 'analytics' && analytics && (
              <div className="space-y-6">
                <h2 className="text-3xl font-bold mb-6">Real-time Analytics Dashboard</h2>
                
                {/* Key Metrics */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  <div className="glass rounded-2xl p-6 hover:shadow-xl transition-all">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-gray-600 font-medium">Total Users</h3>
                      <UsersIcon size={24} className="text-blue-500" />
                    </div>
                    <p className="text-3xl font-bold gradient-text">{analytics.total_users}</p>
                    <p className="text-sm text-gray-500 mt-2">
                      {analytics.active_users_30d} active (30d)
                    </p>
                  </div>
                  
                  <div className="glass rounded-2xl p-6 hover:shadow-xl transition-all">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-gray-600 font-medium">Total Bookings</h3>
                      <CameraIcon size={24} className="text-purple-500" />
                    </div>
                    <p className="text-3xl font-bold gradient-text">{analytics.total_bookings}</p>
                  </div>
                  
                  <div className="glass rounded-2xl p-6 hover:shadow-xl transition-all">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-gray-600 font-medium">Total Revenue</h3>
                      <TrendingUpIcon size={24} className="text-green-500" />
                    </div>
                    <p className="text-3xl font-bold gradient-text">${analytics.total_revenue.toFixed(2)}</p>
                  </div>
                  
                  <div className="glass rounded-2xl p-6 hover:shadow-xl transition-all">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-gray-600 font-medium">New Users (30d)</h3>
                      <SparklesIcon size={24} className="text-yellow-500" />
                    </div>
                    <p className="text-3xl font-bold gradient-text">{analytics.new_users_30d}</p>
                  </div>
                </div>

                {/* Revenue Chart */}
                <div className="glass rounded-2xl p-6">
                  <h3 className="text-xl font-bold mb-4">Revenue by Month</h3>
                  <div className="space-y-2">
                    {Object.entries(analytics.revenue_by_month).map(([month, revenue]) => (
                      <div key={month} className="flex items-center justify-between">
                        <span className="text-gray-600">{month}</span>
                        <div className="flex items-center gap-4">
                          <div className="w-48 bg-gray-200 rounded-full h-4">
                            <div 
                              className="bg-primary-600 h-4 rounded-full"
                              style={{ width: `${(revenue / analytics.total_revenue) * 100}%` }}
                            ></div>
                          </div>
                          <span className="font-semibold">${revenue.toFixed(2)}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Top Tours */}
                <div className="glass rounded-2xl p-6">
                  <h3 className="text-xl font-bold mb-4">Top Tours</h3>
                  <div className="space-y-3">
                    {analytics.top_tours.map((tour, idx) => (
                      <div key={tour.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div className="flex items-center gap-3">
                          <span className="text-2xl font-bold text-primary-600">#{idx + 1}</span>
                          <span className="font-semibold">{tour.name}</span>
                        </div>
                        <span className="text-gray-600">{tour.bookings_count} bookings</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Recent Activity */}
                <div className="glass rounded-2xl p-6">
                  <h3 className="text-xl font-bold mb-4">Recent Activity</h3>
                  <div className="space-y-3">
                    {analytics.recent_activity.map((activity, idx) => (
                      <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div>
                          <p className="font-semibold">{activity.description}</p>
                          <p className="text-sm text-gray-500">{activity.user_email}</p>
                        </div>
                        <span className="text-sm text-gray-500">
                          {new Date(activity.date).toLocaleString()}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* User Management */}
            {activeTab === 'users' && (
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <h2 className="text-3xl font-bold">User Management</h2>
                  <div className="flex gap-4">
                    <input
                      type="text"
                      placeholder="Search users..."
                      value={userSearch}
                      onChange={(e) => {
                        setUserSearch(e.target.value)
                        setTimeout(() => fetchData(), 500)
                      }}
                      className="px-4 py-2 border rounded-lg"
                    />
                  </div>
                </div>

                <div className="glass rounded-2xl overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">ID</th>
                          <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Email</th>
                          <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Name</th>
                          <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Role</th>
                          <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Status</th>
                          <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Bookings</th>
                          <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Spent</th>
                          <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200">
                        {users.map((user) => (
                          <tr key={user.id} className="hover:bg-gray-50">
                            <td className="px-6 py-4 text-sm">{user.id}</td>
                            <td className="px-6 py-4 text-sm">{user.email}</td>
                            <td className="px-6 py-4 text-sm">{user.full_name || '-'}</td>
                            <td className="px-6 py-4 text-sm">
                              <span className={`px-2 py-1 rounded text-xs font-semibold ${
                                user.role === 'admin' ? 'bg-red-100 text-red-800' :
                                user.role === 'moderator' ? 'bg-blue-100 text-blue-800' :
                                'bg-gray-100 text-gray-800'
                              }`}>
                                {user.role}
                              </span>
                            </td>
                            <td className="px-6 py-4 text-sm">
                              <div className="flex gap-2">
                                <span className={`px-2 py-1 rounded text-xs font-semibold ${
                                  user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                                }`}>
                                  {user.is_active ? 'Active' : 'Inactive'}
                                </span>
                                {user.is_verified && (
                                  <span className="px-2 py-1 rounded text-xs font-semibold bg-blue-100 text-blue-800">
                                    Verified
                                  </span>
                                )}
                              </div>
                            </td>
                            <td className="px-6 py-4 text-sm">{user.total_bookings}</td>
                            <td className="px-6 py-4 text-sm font-semibold">${user.total_spent.toFixed(2)}</td>
                            <td className="px-6 py-4 text-sm">
                              <div className="flex gap-2">
                                <button
                                  onClick={() => setSelectedUser(user)}
                                  className="text-primary-600 hover:text-primary-800"
                                >
                                  Edit
                                </button>
                                <button
                                  onClick={() => handleDeleteUser(user.id)}
                                  className="text-red-600 hover:text-red-800"
                                >
                                  Delete
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* User Edit Modal */}
                {selectedUser && (
                  <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="glass rounded-2xl p-6 max-w-md w-full mx-4">
                      <h3 className="text-2xl font-bold mb-4">Edit User</h3>
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium mb-1">Role</label>
                          <select
                            value={selectedUser.role}
                            onChange={(e) => setSelectedUser({ ...selectedUser, role: e.target.value })}
                            className="w-full px-3 py-2 border rounded-lg"
                          >
                            <option value="user">User</option>
                            <option value="moderator">Moderator</option>
                            <option value="admin">Admin</option>
                          </select>
                        </div>
                        <div className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            checked={selectedUser.is_active}
                            onChange={(e) => setSelectedUser({ ...selectedUser, is_active: e.target.checked })}
                            className="w-4 h-4"
                          />
                          <label>Active</label>
                        </div>
                        <div className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            checked={selectedUser.is_verified}
                            onChange={(e) => setSelectedUser({ ...selectedUser, is_verified: e.target.checked })}
                            className="w-4 h-4"
                          />
                          <label>Verified</label>
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={() => {
                              handleUpdateUser(selectedUser.id, {
                                role: selectedUser.role,
                                is_active: selectedUser.is_active,
                                is_verified: selectedUser.is_verified
                              })
                              setSelectedUser(null)
                            }}
                            className="flex-1 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700"
                          >
                            Save
                          </button>
                          <button
                            onClick={() => setSelectedUser(null)}
                            className="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Billing & Payment Portal */}
            {activeTab === 'billing' && billing && (
              <div className="space-y-6">
                <h2 className="text-3xl font-bold mb-6">Billing & Payment Portal</h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  <div className="glass rounded-2xl p-6">
                    <h3 className="text-gray-600 font-medium mb-2">Total Revenue</h3>
                    <p className="text-3xl font-bold gradient-text">${billing.total_revenue.toFixed(2)}</p>
                  </div>
                  <div className="glass rounded-2xl p-6">
                    <h3 className="text-gray-600 font-medium mb-2">This Month</h3>
                    <p className="text-3xl font-bold gradient-text">${billing.revenue_this_month.toFixed(2)}</p>
                    <p className="text-sm text-gray-500 mt-2">
                      {billing.revenue_this_month > billing.revenue_last_month ? '↑' : '↓'} 
                      {Math.abs(((billing.revenue_this_month - billing.revenue_last_month) / (billing.revenue_last_month || 1)) * 100).toFixed(1)}% vs last month
                    </p>
                  </div>
                  <div className="glass rounded-2xl p-6">
                    <h3 className="text-gray-600 font-medium mb-2">Pending Payments</h3>
                    <p className="text-3xl font-bold text-yellow-600">${billing.pending_payments.toFixed(2)}</p>
                  </div>
                </div>

                <div className="glass rounded-2xl p-6">
                  <h3 className="text-xl font-bold mb-4">Revenue by Payment Method</h3>
                  <div className="space-y-3">
                    {Object.entries(billing.revenue_by_payment_method).map(([method, amount]) => (
                      <div key={method} className="flex items-center justify-between">
                        <span className="capitalize font-medium">{method}</span>
                        <span className="font-semibold">${amount.toFixed(2)}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="glass rounded-2xl p-6">
                  <h3 className="text-xl font-bold mb-4">Invoice Summary</h3>
                  <div className="grid grid-cols-4 gap-4">
                    <div>
                      <p className="text-sm text-gray-600">Total</p>
                      <p className="text-2xl font-bold">{billing.invoices_summary.total}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Paid</p>
                      <p className="text-2xl font-bold text-green-600">{billing.invoices_summary.paid}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Pending</p>
                      <p className="text-2xl font-bold text-yellow-600">{billing.invoices_summary.pending}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Cancelled</p>
                      <p className="text-2xl font-bold text-red-600">{billing.invoices_summary.cancelled}</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Usage Statistics & Reports */}
            {activeTab === 'reports' && reports && (
              <div className="space-y-6">
                <h2 className="text-3xl font-bold mb-6">Usage Statistics & Reports</h2>
                
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  <div className="glass rounded-2xl p-6">
                    <h3 className="text-gray-600 font-medium mb-2">Total Users</h3>
                    <p className="text-3xl font-bold gradient-text">{reports.summary.total_users}</p>
                  </div>
                  <div className="glass rounded-2xl p-6">
                    <h3 className="text-gray-600 font-medium mb-2">Total Bookings</h3>
                    <p className="text-3xl font-bold gradient-text">{reports.summary.total_bookings}</p>
                  </div>
                  <div className="glass rounded-2xl p-6">
                    <h3 className="text-gray-600 font-medium mb-2">Total Payments</h3>
                    <p className="text-3xl font-bold gradient-text">{reports.summary.total_payments}</p>
                  </div>
                  <div className="glass rounded-2xl p-6">
                    <h3 className="text-gray-600 font-medium mb-2">Total Revenue</h3>
                    <p className="text-3xl font-bold gradient-text">${reports.summary.total_revenue.toFixed(2)}</p>
                  </div>
                </div>

                <div className="glass rounded-2xl p-6">
                  <h3 className="text-xl font-bold mb-4">Daily Statistics</h3>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b">
                          <th className="px-4 py-2 text-left">Date</th>
                          <th className="px-4 py-2 text-left">Users</th>
                          <th className="px-4 py-2 text-left">Bookings</th>
                          <th className="px-4 py-2 text-left">Payments</th>
                          <th className="px-4 py-2 text-left">Revenue</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(reports.daily_stats).slice(0, 30).map(([date, stats]) => (
                          <tr key={date} className="border-b">
                            <td className="px-4 py-2">{date}</td>
                            <td className="px-4 py-2">{stats.users}</td>
                            <td className="px-4 py-2">{stats.bookings}</td>
                            <td className="px-4 py-2">{stats.payments}</td>
                            <td className="px-4 py-2 font-semibold">${stats.revenue.toFixed(2)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {/* System Health Monitoring */}
            {activeTab === 'health' && health && (
              <div className="space-y-6">
                <h2 className="text-3xl font-bold mb-6">System Health Monitoring</h2>
                
                <div className={`glass rounded-2xl p-6 border-2 ${
                  health.status === 'healthy' ? 'border-green-500' : 'border-yellow-500'
                }`}>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-2xl font-bold">Overall Status</h3>
                    <span className={`px-4 py-2 rounded-full font-semibold ${
                      health.status === 'healthy' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {health.status.toUpperCase()}
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="glass rounded-2xl p-6">
                    <h3 className="text-xl font-bold mb-4">Database</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span>Status:</span>
                        <span className={health.database.connected ? 'text-green-600 font-semibold' : 'text-red-600 font-semibold'}>
                          {health.database.connected ? 'Connected' : 'Disconnected'}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="glass rounded-2xl p-6">
                    <h3 className="text-xl font-bold mb-4">API</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span>Status:</span>
                        <span className={health.api.status === 'healthy' ? 'text-green-600 font-semibold' : 'text-red-600 font-semibold'}>
                          {health.api.status}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Response Time:</span>
                        <span>{health.api.response_time_ms.toFixed(2)} ms</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="glass rounded-2xl p-6">
                  <h3 className="text-xl font-bold mb-4">Services</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {Object.entries(health.services).map(([service, status]) => (
                      <div key={service} className="p-3 bg-gray-50 rounded-lg">
                        <p className="font-semibold capitalize">{service}</p>
                        <p className={`text-sm ${
                          status === 'healthy' ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {status}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Audit Logs & Activity Tracking */}
            {activeTab === 'audit' && (
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <h2 className="text-3xl font-bold">Audit Logs & Activity Tracking</h2>
                  <div className="flex gap-4">
                    <input
                      type="text"
                      placeholder="Filter by action..."
                      value={auditFilters.action}
                      onChange={(e) => {
                        setAuditFilters({ ...auditFilters, action: e.target.value })
                        setTimeout(() => fetchData(), 500)
                      }}
                      className="px-4 py-2 border rounded-lg"
                    />
                    <input
                      type="text"
                      placeholder="Filter by resource..."
                      value={auditFilters.resource_type}
                      onChange={(e) => {
                        setAuditFilters({ ...auditFilters, resource_type: e.target.value })
                        setTimeout(() => fetchData(), 500)
                      }}
                      className="px-4 py-2 border rounded-lg"
                    />
                  </div>
                </div>

                <div className="glass rounded-2xl overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">ID</th>
                          <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">User</th>
                          <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Action</th>
                          <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Resource</th>
                          <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Description</th>
                          <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">IP Address</th>
                          <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Timestamp</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200">
                        {auditLogs.map((log) => (
                          <tr key={log.id} className="hover:bg-gray-50">
                            <td className="px-6 py-4 text-sm">{log.id}</td>
                            <td className="px-6 py-4 text-sm">
                              {log.user_email || `User #${log.user_id}` || 'System'}
                            </td>
                            <td className="px-6 py-4 text-sm">
                              <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-semibold">
                                {log.action}
                              </span>
                            </td>
                            <td className="px-6 py-4 text-sm">
                              <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs font-semibold">
                                {log.resource_type}
                              </span>
                            </td>
                            <td className="px-6 py-4 text-sm">{log.description || '-'}</td>
                            <td className="px-6 py-4 text-sm text-gray-500">{log.ip_address || '-'}</td>
                            <td className="px-6 py-4 text-sm text-gray-500">
                              {new Date(log.created_at).toLocaleString()}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </section>
    </main>
  )
}
