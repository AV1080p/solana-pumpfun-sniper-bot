'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useWallet } from '@solana/wallet-adapter-react'
import { WalletMultiButton } from '@solana/wallet-adapter-react-ui'
import { TourCard } from '@/components/TourCard'
import { PaymentModal } from '@/components/PaymentModal'
import { api } from '@/lib/api'
import { ShieldIcon, ZapIcon, GlobeIcon, SparklesIcon, CheckIcon } from '@/components/Icons'

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

export default function Home() {
  const { publicKey, connected } = useWallet()
  const [tours, setTours] = useState<Tour[]>([])
  const [selectedTour, setSelectedTour] = useState<Tour | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchTours()
  }, [])

  const fetchTours = async () => {
    try {
      const response = await api.get('/tours')
      setTours(response.data)
    } catch (error) {
      console.error('Error fetching tours:', error)
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
                href="/services" 
                className="text-gray-700 hover:text-primary-600 font-medium transition-colors relative group flex items-center gap-2"
              >
                <span className="text-lg">🎯</span>
                <span>Services</span>
                <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-primary-600 transition-all group-hover:w-full"></span>
              </Link>
              <Link 
                href="/bookings" 
                className="text-gray-700 hover:text-primary-600 font-medium transition-colors relative group flex items-center gap-2"
              >
                <span className="text-lg">📋</span>
                <span>My Bookings</span>
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

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-20 pb-32">
        <div className="absolute inset-0 bg-gradient-to-br from-primary-400/20 via-purple-400/20 to-pink-400/20"></div>
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iMC4wNSI+PHBhdGggZD0iTTM2IDM0djJoLTR2LTJoNHptMCA0djJoLTR2LTJoNHptMCA0djJoLTR2LTJoNHptLTYtNHYyaC00di0yaDR6bTAgNHYyaC00di0yaDR6bTAgNHYyaC00di0yaDR6bTYtNHYyaC00di0yaDR6bTAgNHYyaC00di0yaDR6bTAgNHYyaC00di0yaDR6Ii8+PC9nPjwvZz48L3N2Zz4=')] opacity-30"></div>
        
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center animate-fade-in">
          <div className="inline-flex items-center justify-center mb-6 gap-3">
            <span className="text-6xl animate-float" style={{ animationDelay: '0s' }}>✈️</span>
            <span className="text-5xl animate-float" style={{ animationDelay: '1s' }}>🌴</span>
            <span className="text-6xl animate-float" style={{ animationDelay: '2s' }}>🏖️</span>
          </div>
          <h1 className="text-5xl md:text-6xl lg:text-7xl font-extrabold mb-6">
            <span className="gradient-text">Discover</span>
            <br />
            <span className="text-gray-900">Amazing Tours</span>
          </h1>
          <p className="text-xl md:text-2xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Book your next adventure with <span className="font-semibold text-primary-600">crypto</span> or <span className="font-semibold text-purple-600">card</span> payments
          </p>
          <div className="flex flex-wrap justify-center gap-6 text-sm">
            <div className="flex items-center gap-2 glass px-4 py-2 rounded-full backdrop-blur-sm">
              <ShieldIcon size={18} className="text-green-500" />
              <span className="font-medium text-gray-700">Secure Payments</span>
            </div>
            <div className="flex items-center gap-2 glass px-4 py-2 rounded-full backdrop-blur-sm">
              <ZapIcon size={18} className="text-yellow-500" />
              <span className="font-medium text-gray-700">Instant Booking</span>
            </div>
            <div className="flex items-center gap-2 glass px-4 py-2 rounded-full backdrop-blur-sm">
              <GlobeIcon size={18} className="text-blue-500" />
              <span className="font-medium text-gray-700">24/7 Support</span>
            </div>
          </div>
          
          {/* Decorative Icons */}
          <div className="absolute top-20 left-10 hidden lg:block">
            <div className="text-6xl opacity-20 animate-float" style={{ animationDelay: '0s' }}>🌍</div>
          </div>
          <div className="absolute top-32 right-10 hidden lg:block">
            <div className="text-6xl opacity-20 animate-float" style={{ animationDelay: '2s' }}>🗺️</div>
          </div>
          <div className="absolute bottom-20 left-20 hidden lg:block">
            <div className="text-5xl opacity-20 animate-float" style={{ animationDelay: '4s' }}>✈️</div>
          </div>
          <div className="absolute bottom-32 right-20 hidden lg:block">
            <div className="text-5xl opacity-20 animate-float" style={{ animationDelay: '1s' }}>🏝️</div>
          </div>
        </div>
      </section>

      {/* Tours Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-16 pb-20">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="relative">
              <div className="w-16 h-16 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin"></div>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-2xl animate-pulse">🌴</span>
              </div>
            </div>
            <p className="mt-4 text-gray-600 font-medium flex items-center gap-2">
              <SparklesIcon size={20} className="text-primary-500 animate-pulse" />
              Loading amazing tours...
            </p>
          </div>
        ) : tours.length === 0 ? (
          <div className="text-center py-20">
            <div className="inline-flex items-center justify-center gap-3 mb-4">
              <span className="text-6xl animate-bounce" style={{ animationDelay: '0s' }}>🔍</span>
              <span className="text-5xl animate-bounce" style={{ animationDelay: '0.2s' }}>🗺️</span>
              <span className="text-6xl animate-bounce" style={{ animationDelay: '0.4s' }}>✈️</span>
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-2">No tours available</h3>
            <p className="text-gray-600">Check back later for new adventures!</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 animate-slide-up">
            {tours.map((tour, index) => (
              <div
                key={tour.id}
                style={{ animationDelay: `${index * 0.1}s` }}
                className="animate-fade-in"
              >
                <TourCard
                  tour={tour}
                  onBook={() => setSelectedTour(tour)}
                />
              </div>
            ))}
          </div>
        )}

        {selectedTour && (
          <PaymentModal
            tour={selectedTour}
            isOpen={!!selectedTour}
            onClose={() => setSelectedTour(null)}
            walletConnected={connected}
            publicKey={publicKey?.toString()}
          />
        )}
      </section>
    </main>
  )
}

