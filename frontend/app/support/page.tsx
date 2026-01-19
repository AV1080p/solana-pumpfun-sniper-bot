'use client'

import { useState } from 'react'
import Link from 'next/link'
import { api } from '@/lib/api'
import { ShieldIcon, GlobeIcon, SparklesIcon, CheckIcon } from '@/components/Icons'
import toast from 'react-hot-toast'

export default function SupportPage() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    message: ''
  })
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      await api.post('/support/contact', formData)
      toast.success('Message sent successfully! We\'ll get back to you soon.')
      setFormData({ name: '', email: '', subject: '', message: '' })
    } catch (error) {
      toast.error('Failed to send message. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const faqs = [
    {
      question: 'How do I book a tour?',
      answer: 'Simply browse our tours, select one you like, and click "Book Now". You can pay with credit card or cryptocurrency.'
    },
    {
      question: 'What payment methods do you accept?',
      answer: 'We accept credit/debit cards via Stripe, as well as Solana, Bitcoin, and Ethereum cryptocurrencies.'
    },
    {
      question: 'Can I cancel my booking?',
      answer: 'Yes, you can cancel your booking from the "My Bookings" page. Refunds are processed according to our cancellation policy.'
    },
    {
      question: 'How do I contact customer support?',
      answer: 'You can reach us through this support page, email us directly, or call our 24/7 support line.'
    },
    {
      question: 'Are tours refundable?',
      answer: 'Refunds are available for cancellations made at least 48 hours before the tour date. Processing may take 5-7 business days.'
    },
    {
      question: 'Do you offer group discounts?',
      answer: 'Yes! Contact us for group bookings of 10 or more people to receive special pricing.'
    }
  ]

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
                href="/bookings" 
                className="text-gray-700 hover:text-primary-600 font-medium transition-colors"
              >
                My Bookings
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-20 pb-16">
        <div className="absolute inset-0 bg-gradient-to-br from-primary-400/20 via-purple-400/20 to-pink-400/20"></div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center animate-fade-in">
          <div className="inline-flex items-center justify-center mb-6 gap-3">
            <span className="text-6xl animate-float" style={{ animationDelay: '0s' }}>💬</span>
            <span className="text-5xl animate-float" style={{ animationDelay: '1s' }}>🤝</span>
            <span className="text-6xl animate-float" style={{ animationDelay: '2s' }}>✨</span>
          </div>
          <h1 className="text-5xl md:text-6xl font-extrabold mb-6">
            <span className="gradient-text">We're Here to Help</span>
          </h1>
          <p className="text-xl md:text-2xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Have a question? Need assistance? Our support team is available 24/7
          </p>
        </div>
      </section>

      {/* Contact Form & FAQ Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-20">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Contact Form */}
          <div className="glass rounded-2xl p-8 animate-fade-in">
            <h2 className="text-3xl font-bold mb-6 gradient-text">Get in Touch</h2>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label htmlFor="name" className="block text-sm font-semibold text-gray-700 mb-2">
                  Name
                </label>
                <input
                  type="text"
                  id="name"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                  placeholder="Your name"
                />
              </div>
              
              <div>
                <label htmlFor="email" className="block text-sm font-semibold text-gray-700 mb-2">
                  Email
                </label>
                <input
                  type="email"
                  id="email"
                  required
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                  placeholder="your.email@example.com"
                />
              </div>
              
              <div>
                <label htmlFor="subject" className="block text-sm font-semibold text-gray-700 mb-2">
                  Subject
                </label>
                <input
                  type="text"
                  id="subject"
                  required
                  value={formData.subject}
                  onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                  className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                  placeholder="What's this about?"
                />
              </div>
              
              <div>
                <label htmlFor="message" className="block text-sm font-semibold text-gray-700 mb-2">
                  Message
                </label>
                <textarea
                  id="message"
                  required
                  rows={6}
                  value={formData.message}
                  onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                  className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all resize-none"
                  placeholder="Tell us how we can help..."
                />
              </div>
              
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full bg-gradient-to-r from-primary-600 to-purple-600 text-white py-4 px-6 rounded-xl hover:from-primary-700 hover:to-purple-700 transition-all font-semibold shadow-lg hover:shadow-glow transform hover:scale-105 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isSubmitting ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>Sending...</span>
                  </>
                ) : (
                  <>
                    <span>Send Message</span>
                    <span>→</span>
                  </>
                )}
              </button>
            </form>
          </div>

          {/* FAQ Section */}
          <div className="space-y-6 animate-fade-in">
            <div className="glass rounded-2xl p-8">
              <h2 className="text-3xl font-bold mb-6 gradient-text">Frequently Asked Questions</h2>
              <div className="space-y-4">
                {faqs.map((faq, index) => (
                  <details
                    key={index}
                    className="group bg-gray-50 rounded-xl p-4 hover:bg-gray-100 transition-all cursor-pointer"
                  >
                    <summary className="font-semibold text-gray-900 flex items-center justify-between">
                      <span>{faq.question}</span>
                      <span className="text-primary-600 group-open:rotate-180 transition-transform">▼</span>
                    </summary>
                    <p className="mt-3 text-gray-600 leading-relaxed">{faq.answer}</p>
                  </details>
                ))}
              </div>
            </div>

            {/* Contact Info */}
            <div className="glass rounded-2xl p-8">
              <h3 className="text-2xl font-bold mb-4 gradient-text">Other Ways to Reach Us</h3>
              <div className="space-y-4">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center">
                    <span className="text-2xl">📧</span>
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900">Email</p>
                    <p className="text-gray-600">support@touristapp.com</p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
                    <span className="text-2xl">📞</span>
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900">Phone</p>
                    <p className="text-gray-600">+1 (555) 123-4567</p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-pink-100 rounded-full flex items-center justify-center">
                    <span className="text-2xl">💬</span>
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900">Live Chat</p>
                    <p className="text-gray-600">Available 24/7</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  )
}

