'use client'

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { authApi, User, getAuthToken, getStoredUser, clearAuthTokens } from '@/lib/auth'
import toast from 'react-hot-toast'

interface AuthContextType {
  user: User | null
  loading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, fullName?: string, username?: string) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
  mfaRequired: boolean
  mfaUserId: number | null
  setMfaRequired: (required: boolean, userId?: number) => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [mfaRequired, setMfaRequiredState] = useState(false)
  const [mfaUserId, setMfaUserId] = useState<number | null>(null)

  const setMfaRequired = (required: boolean, userId?: number) => {
    setMfaRequiredState(required)
    setMfaUserId(userId || null)
  }

  useEffect(() => {
    // Check if user is already logged in
    const token = getAuthToken()
    const storedUser = getStoredUser()
    
    if (token && storedUser) {
      setUser(storedUser)
      // Verify token is still valid
      authApi.getCurrentUser()
        .then(setUser)
        .catch(() => {
          clearAuthTokens()
          setUser(null)
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = async (email: string, password: string) => {
    try {
      const response = await authApi.login(email, password)
      
      if (response.mfa_required) {
        setMfaRequired(true, response.user_id || null)
        toast.success('Please verify MFA code')
      } else {
        setUser(response.user)
        setMfaRequired(false)
        toast.success('Logged in successfully')
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Login failed')
      throw error
    }
  }

  const register = async (email: string, password: string, fullName?: string, username?: string) => {
    try {
      const response = await authApi.register(email, password, fullName, username)
      setUser(response.user)
      toast.success('Account created successfully')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Registration failed')
      throw error
    }
  }

  const logout = async () => {
    try {
      await authApi.logout()
      setUser(null)
      setMfaRequired(false)
      toast.success('Logged out successfully')
    } catch (error) {
      // Clear local state even if API call fails
      clearAuthTokens()
      setUser(null)
      setMfaRequired(false)
    }
  }

  const refreshUser = async () => {
    try {
      const updatedUser = await authApi.getCurrentUser()
      setUser(updatedUser)
    } catch (error) {
      // If refresh fails, user might be logged out
      clearAuthTokens()
      setUser(null)
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        refreshUser,
        mfaRequired,
        mfaUserId,
        setMfaRequired
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

