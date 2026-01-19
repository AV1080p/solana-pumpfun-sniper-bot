'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useWallet } from '@solana/wallet-adapter-react'
import { WalletMultiButton } from '@solana/wallet-adapter-react-ui'
import { TourCard } from '@/components/TourCard'
import { PaymentModal } from '@/components/PaymentModal'
import { api } from '@/lib/api'
import { ShieldIcon, ZapIcon, GlobeIcon, SparklesIcon, FilterIcon } from '@/components/Icons'

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

export default function ServicesPage() {
  const { publicKey, connected } = useWallet()
  const [tours, setTours] = useState<Tour[]>([])
  const [filteredTours, setFilteredTours] = useState<Tour[]>([])
  const [selectedTour, setSelectedTour] = useState<Tour | null>(null)
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [locationFilter, setLocationFilter] = useState('all')
  const [priceFilter, setPriceFilter] = useState('all')

  useEffect(() => {
    fetchTours()
  }, [])

  useEffect(() => {
    filterTours()
  }, [tours, searchTerm, locationFilter, priceFilter])

  const fetchTours = async () => {
    try {
      const response = await api.get('/tours')
      setTours(response.data)
      setFilteredTours(response.data)
    } catch (error) {
      console.error('Error fetching tours:', error)
    } finally {
      setLoading(false)
    }
  }

  const filterTours = () => {
    let filtered = [...tours]

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(tour =>
        tour.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        tour.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        tour.location.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }

    // Location filter
    if (locationFilter !== 'all') {
      filtered = filtered.filter(tour => tour.location === locationFilter)
    }

    // Price filter
    if (priceFilter === 'low') {
      filtered = filtered.filter(tour => tour.price < 100)
    } else if (priceFilter === 'medium') {
      filtered = filtered.filter(tour => tour.price >= 100 && tour.price < 300)
    } else if (priceFilter === 'high') {
      filtered = filtered.filter(tour => tour.price >= 300)
    }

    setFilteredTours(filtered)
  }

  const locations = Array.from(new Set(tours.map(tour => tour.location)))

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
                className="text-gray-700 hover:text-primary-600 font-medium transition-colors"
              >
                Home
              </Link>
              <Link 
                href="/dashboard" 
                className="text-gray-700 hover:text-primary-600 font-medium transition-colors"
              >
                Dashboard
              </Link>
              <Link 
                href="/bookings" 
                className="text-gray-700 hover:text-primary-600 font-medium transition-colors"
              >
                My Bookings
              </Link>
              <Link 
                href="/support" 
                className="text-gray-700 hover:text-primary-600 font-medium transition-colors"
              >
                Support
              </Link>
              <div className="wallet-adapter-button-trigger">
                <WalletMultiButton className="!bg-gradient-to-r !from-primary-600 !to-purple-600 hover:!from-primary-700 hover:!to-purple-700 !rounded-xl !font-semibold !shadow-lg hover:!shadow-glow transition-all" />
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-20 pb-16">
        <div className="absolute inset-0 bg-gradient-to-br from-primary-400/20 via-purple-400/20 to-pink-400/20"></div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center animate-fade-in">
          <div className="inline-flex items-center justify-center mb-6 gap-3">
            <span className="text-6xl animate-float" style={{ animationDelay: '0s' }}>🎯</span>
            <span className="text-5xl animate-float" style={{ animationDelay: '1s' }}>🌟</span>
            <span className="text-6xl animate-float" style={{ animationDelay: '2s' }}>✨</span>
          </div>
          <h1 className="text-5xl md:text-6xl font-extrabold mb-6">
            <span className="gradient-text">Our Services</span>
          </h1>
          <p className="text-xl md:text-2xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Discover amazing tours and experiences tailored for your adventure
          </p>
        </div>
      </section>

      {/* Filters Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-8 mb-8">
        <div className="glass rounded-2xl p-6 animate-fade-in">
          <div className="flex flex-col md:flex-row gap-4">
            {/* Search */}
            <div className="flex-1">
              <input
                type="text"
                placeholder="Search services..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
              />
            </div>
            
            {/* Location Filter */}
            <div className="md:w-48">
              <select
                value={locationFilter}
                onChange={(e) => setLocationFilter(e.target.value)}
                className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
              >
                <option value="all">All Locations</option>
                {locations.map(location => (
                  <option key={location} value={location}>{location}</option>
                ))}
              </select>
            </div>
            
            {/* Price Filter */}
            <div className="md:w-48">
              <select
                value={priceFilter}
                onChange={(e) => setPriceFilter(e.target.value)}
                className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
              >
                <option value="all">All Prices</option>
                <option value="low">Under $100</option>
                <option value="medium">$100 - $300</option>
                <option value="high">Over $300</option>
              </select>
            </div>
          </div>
        </div>
      </section>

      {/* Services Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-20">
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
              Loading amazing services...
            </p>
          </div>
        ) : filteredTours.length === 0 ? (
          <div className="text-center py-20">
            <div className="inline-flex items-center justify-center gap-3 mb-4">
              <span className="text-6xl animate-bounce" style={{ animationDelay: '0s' }}>🔍</span>
              <span className="text-5xl animate-bounce" style={{ animationDelay: '0.2s' }}>🗺️</span>
              <span className="text-6xl animate-bounce" style={{ animationDelay: '0.4s' }}>✈️</span>
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-2">No services found</h3>
            <p className="text-gray-600 mb-6">Try adjusting your filters or search terms</p>
            <button
              onClick={() => {
                setSearchTerm('')
                setLocationFilter('all')
                setPriceFilter('all')
              }}
              className="inline-flex items-center gap-2 bg-gradient-to-r from-primary-600 to-purple-600 text-white py-3 px-8 rounded-xl hover:from-primary-700 hover:to-purple-700 transition-all font-semibold shadow-lg hover:shadow-glow"
            >
              <span>Clear Filters</span>
            </button>
          </div>
        ) : (
          <>
            <div className="mb-6 flex items-center justify-between">
              <p className="text-gray-600">
                Showing <span className="font-semibold text-gray-900">{filteredTours.length}</span> of{' '}
                <span className="font-semibold text-gray-900">{tours.length}</span> services
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 animate-slide-up">
              {filteredTours.map((tour, index) => (
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
          </>
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

