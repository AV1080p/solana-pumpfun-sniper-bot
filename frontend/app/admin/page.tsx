'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { api } from '@/lib/api'
import { CheckIcon, SparklesIcon, CameraIcon, UsersIcon, TrendingUpIcon, ShieldIcon } from '@/components/Icons'
import toast from 'react-hot-toast'

interface Tour {
  id: number
  name: string
  description: string
  price: number
  price_sol: number
  duration: string
  location: string
  image_url: string
}

interface Booking {
  id: number
  tour_id: number
  user_email: string
  booking_date: string
  status: string
  tour?: Tour
}

interface Payment {
  id: number
  booking_id: number
  amount: number
  payment_method: string
  transaction_id: string
  status: string
  created_at: string
}

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'tours' | 'bookings' | 'payments'>('dashboard')
  const [tours, setTours] = useState<Tour[]>([])
  const [bookings, setBookings] = useState<Booking[]>([])
  const [payments, setPayments] = useState<Payment[]>([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({
    totalTours: 0,
    totalBookings: 0,
    totalRevenue: 0,
    pendingBookings: 0
  })

  useEffect(() => {
    fetchData()
  }, [activeTab])

  const fetchData = async () => {
    setLoading(true)
    try {
      if (activeTab === 'dashboard' || activeTab === 'tours') {
        const toursRes = await api.get('/tours')
        setTours(toursRes.data)
      }
      if (activeTab === 'dashboard' || activeTab === 'bookings') {
        const bookingsRes = await api.get('/bookings')
        setBookings(bookingsRes.data)
      }
      if (activeTab === 'dashboard' || activeTab === 'payments') {
        const paymentsRes = await api.get('/payments')
        setPayments(paymentsRes.data)
      }
      
      // Calculate stats
      const toursRes = await api.get('/tours')
      const bookingsRes = await api.get('/bookings')
      const paymentsRes = await api.get('/payments')
      
      const allTours = toursRes.data
      const allBookings = bookingsRes.data
      const allPayments = paymentsRes.data
      
      setStats({
        totalTours: allTours.length,
        totalBookings: allBookings.length,
        totalRevenue: allPayments
          .filter((p: Payment) => p.status === 'completed')
          .reduce((sum: number, p: Payment) => sum + p.amount, 0),
        pendingBookings: allBookings.filter((b: Booking) => b.status === 'pending').length
      })
    } catch (error) {
      console.error('Error fetching data:', error)
      toast.error('Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteTour = async (tourId: number) => {
    if (!confirm('Are you sure you want to delete this tour?')) return
    
    try {
      await api.delete(`/tours/${tourId}`)
      toast.success('Tour deleted successfully')
      fetchData()
    } catch (error) {
      toast.error('Failed to delete tour')
    }
  }

  const handleUpdateBookingStatus = async (bookingId: number, newStatus: string) => {
    try {
      await api.patch(`/bookings/${bookingId}`, { status: newStatus })
      toast.success('Booking status updated')
      fetchData()
    } catch (error) {
      toast.error('Failed to update booking status')
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
                  <span>Admin Dashboard</span>
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
          <div className="flex gap-4">
            {(['dashboard', 'tours', 'bookings', 'payments'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-6 py-4 font-semibold transition-all relative ${
                  activeTab === tab
                    ? 'text-primary-600'
                    : 'text-gray-600 hover:text-primary-600'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
                {activeTab === tab && (
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
        ) : activeTab === 'dashboard' ? (
          <div className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="glass rounded-2xl p-6 hover:shadow-xl transition-all">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-gray-600 font-medium">Total Tours</h3>
                  <CameraIcon size={24} className="text-primary-500" />
                </div>
                <p className="text-3xl font-bold gradient-text">{stats.totalTours}</p>
              </div>
              
              <div className="glass rounded-2xl p-6 hover:shadow-xl transition-all">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-gray-600 font-medium">Total Bookings</h3>
                  <UsersIcon size={24} className="text-purple-500" />
                </div>
                <p className="text-3xl font-bold gradient-text">{stats.totalBookings}</p>
              </div>
              
              <div className="glass rounded-2xl p-6 hover:shadow-xl transition-all">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-gray-600 font-medium">Total Revenue</h3>
                  <TrendingUpIcon size={24} className="text-green-500" />
                </div>
                <p className="text-3xl font-bold gradient-text">${stats.totalRevenue.toFixed(2)}</p>
              </div>
              
              <div className="glass rounded-2xl p-6 hover:shadow-xl transition-all">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-gray-600 font-medium">Pending Bookings</h3>
                  <ShieldIcon size={24} className="text-yellow-500" />
                </div>
                <p className="text-3xl font-bold gradient-text">{stats.pendingBookings}</p>
              </div>
            </div>

            {/* Recent Bookings */}
            <div className="glass rounded-2xl p-6">
              <h2 className="text-2xl font-bold mb-4">Recent Bookings</h2>
              <div className="space-y-4">
                {bookings.slice(0, 5).map((booking) => (
                  <div key={booking.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                    <div>
                      <p className="font-semibold">{booking.user_email}</p>
                      <p className="text-sm text-gray-600">
                        {new Date(booking.booking_date).toLocaleDateString()}
                      </p>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                      booking.status === 'confirmed' ? 'bg-green-100 text-green-800' :
                      booking.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {booking.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : activeTab === 'tours' ? (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold">Manage Tours</h2>
              <Link
                href="/admin/tours/new"
                className="bg-gradient-to-r from-primary-600 to-purple-600 text-white px-6 py-3 rounded-xl hover:from-primary-700 hover:to-purple-700 transition-all font-semibold"
              >
                + Add New Tour
              </Link>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {tours.map((tour) => (
                <div key={tour.id} className="glass rounded-2xl p-6 hover:shadow-xl transition-all">
                  <h3 className="text-xl font-bold mb-2">{tour.name}</h3>
                  <p className="text-gray-600 mb-4 line-clamp-2">{tour.description}</p>
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-2xl font-bold gradient-text">${tour.price}</span>
                    <span className="text-sm text-gray-500">{tour.location}</span>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleDeleteTour(tour.id)}
                      className="flex-1 bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600 transition-all"
                    >
                      Delete
                    </button>
                    <Link
                      href={`/admin/tours/${tour.id}/edit`}
                      className="flex-1 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-all text-center"
                    >
                      Edit
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : activeTab === 'bookings' ? (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold">Manage Bookings</h2>
            <div className="glass rounded-2xl overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">ID</th>
                      <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Email</th>
                      <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Date</th>
                      <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Status</th>
                      <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {bookings.map((booking) => (
                      <tr key={booking.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 text-sm">{booking.id}</td>
                        <td className="px-6 py-4 text-sm">{booking.user_email}</td>
                        <td className="px-6 py-4 text-sm">
                          {new Date(booking.booking_date).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 text-sm">
                          <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                            booking.status === 'confirmed' ? 'bg-green-100 text-green-800' :
                            booking.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {booking.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm">
                          <select
                            value={booking.status}
                            onChange={(e) => handleUpdateBookingStatus(booking.id, e.target.value)}
                            className="px-3 py-1 border rounded-lg text-sm"
                          >
                            <option value="pending">Pending</option>
                            <option value="confirmed">Confirmed</option>
                            <option value="cancelled">Cancelled</option>
                            <option value="completed">Completed</option>
                          </select>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        ) : activeTab === 'payments' ? (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold">Payment History</h2>
            <div className="glass rounded-2xl overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">ID</th>
                      <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Booking ID</th>
                      <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Amount</th>
                      <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Method</th>
                      <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Status</th>
                      <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Date</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {payments.map((payment) => (
                      <tr key={payment.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 text-sm">{payment.id}</td>
                        <td className="px-6 py-4 text-sm">{payment.booking_id}</td>
                        <td className="px-6 py-4 text-sm font-semibold">${payment.amount}</td>
                        <td className="px-6 py-4 text-sm capitalize">{payment.payment_method}</td>
                        <td className="px-6 py-4 text-sm">
                          <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                            payment.status === 'completed' ? 'bg-green-100 text-green-800' :
                            payment.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                            payment.status === 'failed' ? 'bg-red-100 text-red-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {payment.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm">
                          {new Date(payment.created_at).toLocaleDateString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        ) : null}
      </section>
    </main>
  )
}

