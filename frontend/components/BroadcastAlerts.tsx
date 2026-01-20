'use client'

import { useState, useEffect } from 'react'
import { communicationApi, BroadcastAlert } from '@/lib/communicationApi'
import { useAuth } from '@/contexts/AuthContext'
import toast from 'react-hot-toast'

export function BroadcastAlerts() {
  const { user } = useAuth()
  const [alerts, setAlerts] = useState<BroadcastAlert[]>([])
  const [dismissed, setDismissed] = useState<Set<number>>(new Set())

  useEffect(() => {
    fetchAlerts()
    // Refresh alerts every 30 seconds
    const interval = setInterval(fetchAlerts, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchAlerts = async () => {
    try {
      const data = await communicationApi.getBroadcasts()
      // Filter out dismissed alerts
      const active = data.filter(alert => !dismissed.has(alert.id) && !alert.viewed)
      setAlerts(active)
    } catch (error: any) {
      console.error('Failed to fetch alerts:', error)
    }
  }

  const handleDismiss = async (alert: BroadcastAlert) => {
    setDismissed(prev => new Set(prev).add(alert.id))
    setAlerts(prev => prev.filter(a => a.id !== alert.id))
    
    // Mark as viewed
    try {
      await communicationApi.markBroadcastViewed(alert.id)
    } catch (error: any) {
      console.error('Failed to mark alert as viewed:', error)
    }
  }

  const getAlertColor = (priority: string, alertType: string) => {
    if (alertType === 'emergency' || priority === 'critical') {
      return 'bg-red-600 border-red-700'
    }
    if (priority === 'high') {
      return 'bg-orange-600 border-orange-700'
    }
    if (priority === 'normal') {
      return 'bg-blue-600 border-blue-700'
    }
    return 'bg-gray-600 border-gray-700'
  }

  const getAlertIcon = (alertType: string) => {
    switch (alertType) {
      case 'emergency':
        return '🚨'
      case 'announcement':
        return '📢'
      case 'maintenance':
        return '🔧'
      default:
        return 'ℹ️'
    }
  }

  if (alerts.length === 0) return null

  return (
    <div className="fixed top-20 right-4 z-50 space-y-3 max-w-md">
      {alerts.map((alert) => (
        <div
          key={alert.id}
          className={`${getAlertColor(alert.priority, alert.alert_type)} text-white rounded-lg shadow-xl p-4 animate-slide-in`}
        >
          <div className="flex justify-between items-start mb-2">
            <div className="flex items-center gap-2">
              <span className="text-2xl">{getAlertIcon(alert.alert_type)}</span>
              <h4 className="font-bold text-lg">{alert.title}</h4>
            </div>
            <button
              onClick={() => handleDismiss(alert)}
              className="text-white hover:bg-white/20 rounded p-1"
            >
              ✕
            </button>
          </div>
          <p className="text-sm opacity-90">{alert.message}</p>
          {alert.expires_at && (
            <p className="text-xs opacity-75 mt-2">
              Expires: {new Date(alert.expires_at).toLocaleString()}
            </p>
          )}
        </div>
      ))}
    </div>
  )
}

