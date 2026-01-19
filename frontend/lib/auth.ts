import { api } from './api'

export interface User {
  id: number
  email: string
  username?: string
  full_name?: string
  role: string
  avatar_url?: string
  is_verified: boolean
  auth_provider: string
  mfa_enabled?: boolean
}

export interface AuthResponse {
  success: boolean
  access_token: string
  refresh_token?: string
  token_type: string
  user: User
  expires_at?: string
  mfa_required?: boolean
  user_id?: number
}

export interface Session {
  id: number
  device_info?: string
  ip_address?: string
  status: string
  created_at: string
  last_activity: string
  expires_at: string
  is_current?: boolean
}

// Token management
export const getAuthToken = (): string | null => {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('auth_token')
}

export const getRefreshToken = (): string | null => {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('refresh_token')
}

export const setAuthTokens = (accessToken: string, refreshToken?: string): void => {
  if (typeof window === 'undefined') return
  localStorage.setItem('auth_token', accessToken)
  if (refreshToken) {
    localStorage.setItem('refresh_token', refreshToken)
  }
}

export const clearAuthTokens = (): void => {
  if (typeof window === 'undefined') return
  localStorage.removeItem('auth_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('user')
}

export const getStoredUser = (): User | null => {
  if (typeof window === 'undefined') return null
  const userStr = localStorage.getItem('user')
  if (!userStr) return null
  try {
    return JSON.parse(userStr)
  } catch {
    return null
  }
}

export const setStoredUser = (user: User): void => {
  if (typeof window === 'undefined') return
  localStorage.setItem('user', JSON.stringify(user))
}

// Auth API calls
export const authApi = {
  async register(email: string, password: string, fullName?: string, username?: string): Promise<AuthResponse> {
    const response = await api.post('/auth/register', {
      email,
      password,
      full_name: fullName,
      username
    })
    const data = response.data
    if (data.success && data.access_token) {
      setAuthTokens(data.access_token, data.refresh_token)
      setStoredUser(data.user)
    }
    return data
  },

  async login(email: string, password: string): Promise<AuthResponse> {
    const response = await api.post('/auth/login', {
      email,
      password
    })
    const data = response.data
    if (data.success && data.access_token) {
      setAuthTokens(data.access_token, data.refresh_token)
      setStoredUser(data.user)
    }
    return data
  },

  async loginMfaVerify(userId: number, code: string): Promise<AuthResponse> {
    const response = await api.post(`/auth/login/mfa-verify?user_id=${userId}`, {
      code
    })
    const data = response.data
    if (data.success && data.access_token) {
      setAuthTokens(data.access_token, data.refresh_token)
      if (data.user) {
        setStoredUser(data.user)
      }
    }
    return data
  },

  async logout(): Promise<void> {
    clearAuthTokens()
    // Optionally call backend to revoke session
    try {
      await api.post('/auth/sessions/revoke-all')
    } catch (error) {
      // Ignore errors on logout
    }
  },

  async getCurrentUser(): Promise<User> {
    const response = await api.get('/auth/me')
    const user = response.data
    setStoredUser(user)
    return user
  },

  async refreshToken(): Promise<{ access_token: string; expires_at: string }> {
    const refreshToken = getRefreshToken()
    if (!refreshToken) {
      throw new Error('No refresh token available')
    }
    const response = await api.post('/auth/sessions/refresh', {
      refresh_token: refreshToken
    })
    const data = response.data
    if (data.success && data.access_token) {
      localStorage.setItem('auth_token', data.access_token)
    }
    return data
  },

  async getOAuthUrl(provider: string): Promise<{ url: string; provider: string }> {
    const response = await api.get(`/auth/oauth/${provider}/url`)
    return response.data
  },

  // MFA
  async setupMFA(deviceName: string): Promise<{ secret: string; qr_code: string; manual_entry_key: string }> {
    const response = await api.post('/auth/mfa/setup', { device_name: deviceName })
    return response.data
  },

  async verifyAndEnableMFA(code: string): Promise<{ backup_codes: string[] }> {
    const response = await api.post('/auth/mfa/verify-enable', { code })
    return response.data
  },

  async disableMFA(password: string): Promise<void> {
    await api.post('/auth/mfa/disable', { password })
  },

  async regenerateBackupCodes(): Promise<{ backup_codes: string[] }> {
    const response = await api.post('/auth/mfa/regenerate-backup-codes')
    return response.data
  },

  // Sessions
  async getSessions(): Promise<Session[]> {
    const response = await api.get('/auth/sessions')
    return response.data.sessions
  },

  async revokeSession(sessionId?: number, sessionToken?: string): Promise<void> {
    await api.post('/auth/sessions/revoke', {
      session_id: sessionId,
      session_token: sessionToken
    })
  },

  async revokeAllSessions(): Promise<void> {
    await api.post('/auth/sessions/revoke-all')
  },

  // Invitations
  async acceptInvitation(token: string, password: string, fullName?: string, username?: string): Promise<AuthResponse> {
    const response = await api.post('/auth/invitations/accept', {
      token,
      password,
      full_name: fullName,
      username
    })
    const data = response.data
    if (data.success && data.access_token) {
      setAuthTokens(data.access_token, data.refresh_token)
      setStoredUser(data.user)
    }
    return data
  },

  // Permissions
  async getPermissions(): Promise<string[]> {
    const response = await api.get('/auth/permissions')
    return response.data.permissions
  }
}

