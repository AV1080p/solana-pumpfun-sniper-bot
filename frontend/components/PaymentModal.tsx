'use client'

import { useState } from 'react'
import { useWallet, useConnection } from '@solana/wallet-adapter-react'
import { Connection, PublicKey, Transaction, SystemProgram, LAMPORTS_PER_SOL } from '@solana/web3.js'
import { api } from '@/lib/api'
import { processSolanaPayment, swapTokens } from '@/lib/solana'
import { loadStripe } from '@stripe/stripe-js'
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js'
import toast from 'react-hot-toast'
import { SparklesIcon, CheckIcon } from './Icons'

const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY || '')

interface Tour {
  id: number
  name: string
  price: number
  price_sol: number
}

interface PaymentModalProps {
  tour: Tour
  isOpen: boolean
  onClose: () => void
  walletConnected: boolean
  publicKey?: string
}

function PaymentForm({ tour, onClose }: { tour: Tour; onClose: () => void }) {
  const stripe = useStripe()
  const elements = useElements()
  const [processing, setProcessing] = useState(false)

  const handleCardPayment = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!stripe || !elements) return

    setProcessing(true)
    try {
      const cardElement = elements.getElement(CardElement)
      if (!cardElement) return

      const { error: stripeError, paymentMethod } = await stripe.createPaymentMethod({
        type: 'card',
        card: cardElement,
      })

      if (stripeError) {
        toast.error(stripeError.message || 'Payment failed')
        return
      }

      const response = await api.post('/payments/stripe', {
        tour_id: tour.id,
        payment_method_id: paymentMethod.id,
        amount: tour.price,
      })

      if (response.data.success) {
        toast.success('Payment successful! Booking confirmed.')
        onClose()
      }
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Payment failed')
    } finally {
      setProcessing(false)
    }
  }

  return (
    <form onSubmit={handleCardPayment} className="space-y-4">
      <div className="p-5 border-2 border-gray-200 rounded-xl bg-white focus-within:border-primary-500 transition-colors">
        <CardElement
          options={{
            style: {
              base: {
                fontSize: '16px',
                color: '#1f2937',
                fontFamily: 'system-ui, sans-serif',
                '::placeholder': {
                  color: '#9ca3af',
                },
              },
            },
          }}
        />
      </div>
      <button
        type="submit"
        disabled={!stripe || processing}
        className="w-full bg-gradient-to-r from-primary-600 to-purple-600 text-white py-4 px-6 rounded-xl hover:from-primary-700 hover:to-purple-700 disabled:opacity-50 transition-all font-bold text-lg shadow-lg hover:shadow-glow transform hover:scale-105 active:scale-95 flex items-center justify-center gap-2"
      >
        {processing ? (
          <>
            <span className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
            Processing...
          </>
        ) : (
          <>
            <span>Pay ${tour.price}</span>
            <span>💳</span>
          </>
        )}
      </button>
      <p className="text-xs text-center text-gray-500">
        🔒 Secure payment powered by Stripe
      </p>
    </form>
  )
}

export function PaymentModal({ tour, isOpen, onClose, walletConnected, publicKey }: PaymentModalProps) {
  const { sendTransaction } = useWallet()
  const { connection } = useConnection()
  const [paymentMethod, setPaymentMethod] = useState<'crypto' | 'card'>('crypto')
  const [processing, setProcessing] = useState(false)
  const [tokenSwap, setTokenSwap] = useState(false)

  if (!isOpen) return null

  const handleSolanaPayment = async () => {
    if (!publicKey || !sendTransaction) {
      toast.error('Please connect your wallet')
      return
    }

    setProcessing(true)
    try {
      const result = await processSolanaPayment(
        publicKey,
        tour.price_sol,
        tour.id,
        sendTransaction,
        connection
      )

      if (result.success) {
        toast.success('Payment successful! Booking confirmed.')
        onClose()
      } else {
        toast.error(result.error || 'Payment failed')
      }
    } catch (error: any) {
      toast.error(error.message || 'Payment failed')
    } finally {
      setProcessing(false)
    }
  }

  const handleTokenSwap = async () => {
    if (!publicKey || !sendTransaction) {
      toast.error('Please connect your wallet')
      return
    }

    setProcessing(true)
    try {
      // Swap USDC to SOL for payment
      const result = await swapTokens(publicKey, tour.price_sol, sendTransaction, connection)
      if (result.success) {
        toast.success('Tokens swapped successfully!')
        setTokenSwap(false)
        await handleSolanaPayment()
      } else {
        toast.error(result.error || 'Token swap failed')
      }
    } catch (error: any) {
      toast.error(error.message || 'Token swap failed')
    } finally {
      setProcessing(false)
    }
  }

  return (
    <div 
      className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in"
      onClick={onClose}
    >
      <div 
        className="glass rounded-2xl p-8 max-w-md w-full mx-4 shadow-2xl animate-slide-up transform"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-start mb-6">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-3xl animate-pulse">🎫</span>
              <h2 className="text-3xl font-bold gradient-text">Book Your Adventure</h2>
            </div>
            <p className="text-gray-600 font-medium flex items-center gap-2">
              <span>✈️</span>
              <span>{tour.name}</span>
            </p>
          </div>
          <button 
            onClick={onClose} 
            className="text-gray-400 hover:text-gray-600 transition-colors p-2 hover:bg-gray-100 rounded-full"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="mb-6">
          {/* Price Display */}
          <div className="bg-gradient-to-r from-primary-50 to-purple-50 rounded-xl p-6 mb-6 border border-primary-100">
            <p className="text-sm text-gray-600 mb-2">Total Amount</p>
            <div className="flex items-baseline gap-3">
              <span className="text-4xl font-bold gradient-text">${tour.price}</span>
              <span className="text-gray-400">or</span>
              <span className="text-2xl font-bold text-purple-600">{tour.price_sol.toFixed(4)} SOL</span>
            </div>
          </div>

          {/* Payment Method Selection */}
          <div className="mb-6">
            <p className="text-sm font-semibold text-gray-700 mb-3">Choose Payment Method</p>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => setPaymentMethod('crypto')}
                className={`relative p-4 rounded-xl border-2 transition-all duration-300 ${
                  paymentMethod === 'crypto'
                    ? 'border-primary-500 bg-gradient-to-br from-primary-50 to-purple-50 shadow-lg scale-105'
                    : 'border-gray-200 bg-white hover:border-primary-300 hover:shadow-md'
                }`}
              >
                <div className="text-3xl mb-2">💎</div>
                <div className="font-semibold text-gray-900">Crypto</div>
                <div className="text-xs text-gray-500 mt-1">Pay with SOL</div>
                {paymentMethod === 'crypto' && (
                  <div className="absolute top-2 right-2 w-5 h-5 bg-primary-600 rounded-full flex items-center justify-center">
                    <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                )}
              </button>
              <button
                onClick={() => setPaymentMethod('card')}
                className={`relative p-4 rounded-xl border-2 transition-all duration-300 ${
                  paymentMethod === 'card'
                    ? 'border-primary-500 bg-gradient-to-br from-primary-50 to-purple-50 shadow-lg scale-105'
                    : 'border-gray-200 bg-white hover:border-primary-300 hover:shadow-md'
                }`}
              >
                <div className="text-3xl mb-2">💳</div>
                <div className="font-semibold text-gray-900">Card</div>
                <div className="text-xs text-gray-500 mt-1">Debit/Credit</div>
                {paymentMethod === 'card' && (
                  <div className="absolute top-2 right-2 w-5 h-5 bg-primary-600 rounded-full flex items-center justify-center">
                    <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                )}
              </button>
            </div>
          </div>

          {paymentMethod === 'crypto' && (
            <div className="space-y-4">
              {!walletConnected ? (
                <div className="text-center py-8 bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl border border-purple-200">
                  <div className="flex justify-center gap-2 mb-3">
                    <span className="text-5xl animate-pulse">🔐</span>
                    <span className="text-4xl animate-pulse" style={{ animationDelay: '0.2s' }}>💎</span>
                  </div>
                  <p className="text-gray-700 font-medium mb-2">
                    Connect Your Wallet
                  </p>
                  <p className="text-sm text-gray-500">
                    Please connect your Solana wallet to pay with crypto
                  </p>
                </div>
              ) : (
                <>
                  {tokenSwap && (
                    <div className="p-4 bg-gradient-to-r from-yellow-50 to-orange-50 border-2 border-yellow-300 rounded-xl mb-4 animate-fade-in">
                      <div className="flex items-start gap-3">
                        <div className="flex flex-col items-center gap-1">
                          <span className="text-2xl animate-spin">🔄</span>
                          <SparklesIcon size={16} className="text-yellow-600" />
                        </div>
                        <div className="flex-1">
                          <p className="text-sm font-semibold text-yellow-900 mb-1 flex items-center gap-2">
                            Token Swap Available
                            <span className="text-xs bg-yellow-200 px-2 py-0.5 rounded-full">NEW</span>
                          </p>
                          <p className="text-xs text-yellow-700 mb-3">
                            Swap your USDC to SOL for payment
                          </p>
                          <button
                            onClick={handleTokenSwap}
                            disabled={processing}
                            className="w-full bg-gradient-to-r from-yellow-500 to-orange-500 text-white py-2.5 px-4 rounded-lg hover:from-yellow-600 hover:to-orange-600 disabled:opacity-50 transition-all font-semibold shadow-md"
                          >
                            {processing ? (
                              <span className="flex items-center justify-center gap-2">
                                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                                Swapping...
                              </span>
                            ) : (
                              'Swap Tokens Now'
                            )}
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                  <button
                    onClick={handleSolanaPayment}
                    disabled={processing}
                    className="w-full bg-gradient-to-r from-primary-600 to-purple-600 text-white py-4 px-6 rounded-xl hover:from-primary-700 hover:to-purple-700 disabled:opacity-50 transition-all font-bold text-lg shadow-lg hover:shadow-glow transform hover:scale-105 active:scale-95 flex items-center justify-center gap-2"
                  >
                    {processing ? (
                      <>
                        <span className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                        Processing Payment...
                      </>
                    ) : (
                      <>
                        <span>Pay {tour.price_sol.toFixed(4)} SOL</span>
                        <span>💎</span>
                      </>
                    )}
                  </button>
                  <button
                    onClick={() => setTokenSwap(!tokenSwap)}
                    className="w-full text-primary-600 hover:text-primary-700 text-sm font-medium py-2 transition-colors"
                  >
                    {tokenSwap ? '← Cancel Swap' : '🔄 Swap Tokens Instead'}
                  </button>
                </>
              )}
            </div>
          )}

          {paymentMethod === 'card' && (
            <Elements stripe={stripePromise}>
              <PaymentForm tour={tour} onClose={onClose} />
            </Elements>
          )}
        </div>
      </div>
    </div>
  )
}

