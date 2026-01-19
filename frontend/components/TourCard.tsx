'use client'

import { useState } from 'react'
import { LocationIcon, ClockIcon, StarIcon } from './Icons'

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

interface TourCardProps {
  tour: Tour
  onBook: () => void
}

const tourIcons = ['🏖️', '⛰️', '🏛️', '🦁', '🌃', '🏝️', '🏔️', '🗺️', '🌊', '🌴']

// Tour images from Unsplash - high quality placeholder images
const tourImages = [
  'https://images.unsplash.com/photo-1507525421304-677d4f1a0cfe?w=800&h=600&fit=crop',
  'https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?w=800&h=600&fit=crop',
  'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&h=600&fit=crop',
  'https://images.unsplash.com/photo-1518546305927-5a555bb7020d?w=800&h=600&fit=crop',
  'https://images.unsplash.com/photo-1501594907352-04c32438d422?w=800&h=600&fit=crop',
  'https://images.unsplash.com/photo-1504280390367-361c6d9f38f4?w=800&h=600&fit=crop',
  'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&h=600&fit=crop',
  'https://images.unsplash.com/photo-1519681393784-d120267933ba?w=800&h=600&fit=crop',
  'https://images.unsplash.com/photo-1507525421304-677d4f1a0cfe?w=800&h=600&fit=crop',
  'https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?w=800&h=600&fit=crop',
]

export function TourCard({ tour, onBook }: TourCardProps) {
  const [isHovered, setIsHovered] = useState(false)
  const [imageError, setImageError] = useState(false)
  const icon = tourIcons[tour.id % tourIcons.length] || '✈️'
  const imageUrl = tour.image_url || tourImages[tour.id % tourImages.length]

  return (
    <div
      className="group relative bg-white rounded-2xl shadow-lg overflow-hidden hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-2"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Image Section */}
      <div className="relative h-56 bg-gradient-to-br from-primary-400 via-purple-400 to-pink-400 overflow-hidden">
        {!imageError ? (
          <img 
            src={imageUrl} 
            alt={tour.name}
            onError={() => setImageError(true)}
            className={`w-full h-full object-cover transition-transform duration-500 ${isHovered ? 'scale-110' : 'scale-100'}`}
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-primary-400 via-purple-400 to-pink-400">
            <span className="text-8xl transform transition-transform duration-300 group-hover:scale-125">{icon}</span>
          </div>
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
        
        {/* Rating Badge */}
        <div className="absolute top-4 left-4 flex items-center gap-1 glass px-2.5 py-1 rounded-full backdrop-blur-sm">
          <StarIcon size={14} className="text-yellow-400 fill-yellow-400" />
          <span className="text-xs font-bold text-gray-800">4.{Math.floor(Math.random() * 9) + 1}</span>
        </div>
        
        {/* Popular Badge */}
        <div className="absolute top-4 right-4">
          <span className="glass px-3 py-1 rounded-full text-xs font-semibold text-gray-800 backdrop-blur-sm flex items-center gap-1">
            <span className="text-red-500">🔥</span>
            Popular
          </span>
        </div>
      </div>

      {/* Content Section */}
      <div className="p-6">
        <h3 className="text-xl font-bold text-gray-900 mb-2 group-hover:text-primary-600 transition-colors">
          {tour.name}
        </h3>
        <p className="text-gray-600 mb-4 line-clamp-2 text-sm leading-relaxed">
          {tour.description}
        </p>
        
        {/* Info Icons */}
        <div className="flex items-center gap-4 mb-4 text-sm text-gray-500">
          <div className="flex items-center gap-1.5">
            <LocationIcon size={16} className="text-primary-500" />
            <span className="font-medium">{tour.location}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <ClockIcon size={16} className="text-purple-500" />
            <span className="font-medium">{tour.duration}</span>
          </div>
        </div>

        {/* Price Section */}
        <div className="flex items-baseline justify-between mb-6 pb-6 border-b border-gray-200">
          <div>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold bg-gradient-to-r from-primary-600 to-purple-600 bg-clip-text text-transparent">
                ${tour.price}
              </span>
              <span className="text-xs text-gray-400 line-through">${(tour.price * 1.2).toFixed(0)}</span>
            </div>
            <div className="flex items-center gap-1.5 mt-1">
              <span className="text-xs text-gray-500">or</span>
              <span className="text-sm font-semibold text-purple-600">{tour.price_sol.toFixed(4)} SOL</span>
              <span className="text-xs text-gray-400">💎</span>
            </div>
          </div>
        </div>

        {/* Book Button */}
        <button
          onClick={onBook}
          className="w-full bg-gradient-to-r from-primary-600 to-purple-600 text-white py-3 px-6 rounded-xl hover:from-primary-700 hover:to-purple-700 transition-all duration-300 font-semibold shadow-lg hover:shadow-glow transform hover:scale-105 active:scale-95 flex items-center justify-center gap-2"
        >
          <span>Book Now</span>
          <span className="transform transition-transform group-hover:translate-x-1">→</span>
        </button>
      </div>

      {/* Shine Effect */}
      <div className="absolute inset-0 -top-full group-hover:top-full transition-all duration-700 bg-gradient-to-b from-transparent via-white/20 to-transparent pointer-events-none"></div>
    </div>
  )
}

