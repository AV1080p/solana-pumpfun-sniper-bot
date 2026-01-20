import { api } from './api'

export interface AdminAnalytics {
  total_users: number
  total_bookings: number
  total_revenue: number
  total_payments: number
  active_users_30d: number
  new_users_30d: number
  revenue_by_month: Record<string, number>
  bookings_by_status: Record<string, number>
  payments_by_method: Record<string, number>
  top_tours: Array<{ id: number; name: string; bookings_count: number }>
  recent_activity: Array<{ type: string; description: string; date: string; user_email: string }>
}

export interface UserList {
  id: number
  email: string
  username?: string
  full_name?: string
  role: string
  is_active: boolean
  is_verified: boolean
  created_at: string
  last_login?: string
  total_bookings: number
  total_spent: number
}

export interface BillingSummary {
  total_revenue: number
  revenue_this_month: number
  revenue_last_month: number
  pending_payments: number
  failed_payments: number
  refunded_amount: number
  revenue_by_payment_method: Record<string, number>
  invoices_summary: {
    total: number
    paid: number
    pending: number
    cancelled: number
  }
}

export interface UsageReport {
  success: boolean
  period: {
    start_date: string
    end_date: string
  }
  summary: {
    total_users: number
    total_bookings: number
    total_payments: number
    total_revenue: number
  }
  daily_stats: Record<string, {
    users: number
    bookings: number
    payments: number
    revenue: number
  }>
}

export interface SystemHealth {
  status: string
  database: {
    connected: boolean
    pool_stats: any
    table_stats: any
  }
  api: {
    status: string
    response_time_ms: number
  }
  services: Record<string, string>
  uptime: number
  timestamp: string
}

export interface AuditLog {
  id: number
  user_id?: number
  user_email?: string
  action: string
  resource_type: string
  resource_id?: number
  description?: string
  ip_address?: string
  created_at: string
}

export const adminApi = {
  async getAnalytics(): Promise<AdminAnalytics> {
    const response = await api.get('/admin/analytics')
    return response.data
  },

  async getUsers(params?: {
    skip?: number
    limit?: number
    search?: string
  }): Promise<UserList[]> {
    const response = await api.get('/admin/users', { params })
    return response.data
  },

  async getUser(userId: number): Promise<UserList> {
    const response = await api.get(`/admin/users/${userId}`)
    return response.data
  },

  async updateUser(userId: number, data: {
    email?: string
    username?: string
    full_name?: string
    role?: string
    is_active?: boolean
    is_verified?: boolean
  }): Promise<{ success: boolean; message: string; user: any }> {
    const response = await api.patch(`/admin/users/${userId}`, data)
    return response.data
  },

  async deleteUser(userId: number): Promise<{ success: boolean; message: string }> {
    const response = await api.delete(`/admin/users/${userId}`)
    return response.data
  },

  async getBillingSummary(): Promise<BillingSummary> {
    const response = await api.get('/admin/billing')
    return response.data
  },

  async getUsageReport(params?: {
    start_date?: string
    end_date?: string
    report_type?: string
  }): Promise<UsageReport> {
    const response = await api.get('/admin/reports/usage', { params })
    return response.data
  },

  async getSystemHealth(): Promise<SystemHealth> {
    const response = await api.get('/admin/health')
    return response.data
  },

  async getAuditLogs(params?: {
    user_id?: number
    action?: string
    resource_type?: string
    start_date?: string
    end_date?: string
    limit?: number
    offset?: number
  }): Promise<AuditLog[]> {
    const response = await api.get('/admin/audit-logs', { params })
    return response.data
  }
}

