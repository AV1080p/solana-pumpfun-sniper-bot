'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { WalletMultiButton } from '@solana/wallet-adapter-react-ui'
import { api } from '@/lib/api'
import { CheckIcon, SparklesIcon, CameraIcon } from '@/components/Icons'

interface Booking {
  id: number
  tour_name: string
  booking_date: string
  payment_method: string
  amount: number
  status: string
}

export default function BookingsPage() {
  const [bookings, setBookings] = useState<Booking[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchBookings()
  }, [])

  const fetchBookings = async () => {
    try {
      const response = await api.get('/bookings')
      setBookings(response.data)
    } catch (error) {
      console.error('Error fetching bookings:', error)
    } finally {
      setLoading(false)
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
                  <span>Your Adventure Awaits</span>
                  <span className="animate-pulse">🌟</span>
                </p>
              </div>
            </Link>
            <div className="flex items-center gap-6">
              <Link 
                href="/" 
                className="text-gray-700 hover:text-primary-600 font-medium transition-colors relative group flex items-center gap-2"
              >
                <span className="text-lg">🗺️</span>
                <span>Tours</span>
                <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-primary-600 transition-all group-hover:w-full"></span>
              </Link>
              <Link 
                href="/services" 
                className="text-gray-700 hover:text-primary-600 font-medium transition-colors relative group flex items-center gap-2"
              >
                <span className="text-lg">🎯</span>
                <span>Services</span>
                <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-primary-600 transition-all group-hover:w-full"></span>
              </Link>
              <Link 
                href="/support" 
                className="text-gray-700 hover:text-primary-600 font-medium transition-colors relative group flex items-center gap-2"
              >
                <span className="text-lg">💬</span>
                <span>Support</span>
                <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-primary-600 transition-all group-hover:w-full"></span>
              </Link>
              <div className="wallet-adapter-button-trigger">
                <WalletMultiButton className="!bg-gradient-to-r !from-primary-600 !to-purple-600 hover:!from-primary-700 hover:!to-purple-700 !rounded-xl !font-semibold !shadow-lg hover:!shadow-glow transition-all" />
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Header Section */}
      <section className="relative overflow-hidden pt-16 pb-12">
        <div className="absolute inset-0 bg-gradient-to-br from-primary-400/20 via-purple-400/20 to-pink-400/20"></div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center animate-fade-in">
            <h1 className="text-5xl md:text-6xl font-extrabold mb-4">
              <span className="gradient-text">My Bookings</span>
            </h1>
            <p className="text-xl text-gray-600">Manage your travel adventures</p>
          </div>
        </div>
      </section>

      {/* Bookings Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-20">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="relative">
              <div className="w-16 h-16 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin"></div>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-2xl">🌴</span>
              </div>
            </div>
            <p className="mt-4 text-gray-600 font-medium">Loading your bookings...</p>
          </div>
        ) : bookings.length === 0 ? (
          <div className="text-center py-20 animate-fade-in">
            <div className="inline-flex items-center justify-center gap-2 p-6 bg-gradient-to-br from-primary-100 to-purple-100 rounded-full mb-6">
              <span className="text-6xl animate-bounce" style={{ animationDelay: '0s' }}>📋</span>
              <span className="text-5xl animate-bounce" style={{ animationDelay: '0.2s' }}>🗺️</span>
              <span className="text-6xl animate-bounce" style={{ animationDelay: '0.4s' }}>✈️</span>
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-2">No bookings yet</h3>
            <p className="text-gray-600 mb-6">Start exploring amazing tours and book your first adventure!</p>
            <Link
              href="/"
              className="inline-flex items-center gap-2 bg-gradient-to-r from-primary-600 to-purple-600 text-white py-3 px-8 rounded-xl hover:from-primary-700 hover:to-purple-700 transition-all font-semibold shadow-lg hover:shadow-glow transform hover:scale-105"
            >
              <SparklesIcon size={20} className="text-white" />
              <span>Browse Tours</span>
              <span>→</span>
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-slide-up">
            {bookings.map((booking, index) => (
              <div
                key={booking.id}
                className="group glass rounded-2xl p-6 hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1 animate-fade-in"
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-3">
                      <CameraIcon size={20} className="text-primary-500" />
                      <h3 className="text-xl font-bold text-gray-900 group-hover:text-primary-600 transition-colors">
                        {booking.tour_name}
                      </h3>
                    </div>
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center gap-2 text-gray-600">
                        <span className="text-base animate-pulse">📅</span>
                        <span className="font-medium">{new Date(booking.booking_date).toLocaleDateString('en-US', { 
                          weekday: 'short', 
                          year: 'numeric', 
                          month: 'short', 
                          day: 'numeric' 
                        })}</span>
                      </div>
                      <div className="flex items-center gap-2 text-gray-600">
                        <span className="text-base">
                          {booking.payment_method === 'solana' ? '💎' : '💳'}
                        </span>
                        <span className="capitalize font-medium">{booking.payment_method}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-lg font-bold gradient-text">${booking.amount}</span>
                        <SparklesIcon size={16} className="text-purple-500" />
                      </div>
                    </div>
                  </div>
                </div>
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <span
                    className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold ${
                      booking.status === 'confirmed'
                        ? 'bg-gradient-to-r from-green-100 to-emerald-100 text-green-800 border border-green-200'
                        : booking.status === 'pending'
                        ? 'bg-gradient-to-r from-yellow-100 to-amber-100 text-yellow-800 border border-yellow-200'
                        : 'bg-gradient-to-r from-red-100 to-pink-100 text-red-800 border border-red-200'
                    }`}
                  >
                    {booking.status === 'confirmed' && (
                      <>
                        <CheckIcon size={14} className="text-green-600" />
                        <span className="capitalize">{booking.status}</span>
                      </>
                    )}
                    {booking.status === 'pending' && (
                      <>
                        <span className="animate-spin">⏳</span>
                        <span className="capitalize">{booking.status}</span>
                      </>
                    )}
                    {booking.status === 'cancelled' && (
                      <>
                        <span>✕</span>
                        <span className="capitalize">{booking.status}</span>
                      </>
                    )}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </main>
  )
}

