import axios from 'axios'

const getApiUrl = () => {
  if (typeof window === 'undefined') return '/api'

  // Allow explicit override (e.g. VITE_API_URL=https://my-backend)
  if (import.meta.env?.VITE_API_URL) return import.meta.env.VITE_API_URL
  
  const { protocol, hostname } = window.location

  // Local dev
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return 'http://localhost:8000'
  }

  // Replit multi-port: frontend served on "-00-", backend on "-01-"
  const replitMatch = hostname.match(/^(.*)-0\d-(.*)$/)
  if (replitMatch) {
    const [, prefix, suffix] = replitMatch
    return `${protocol}//${prefix}-01-${suffix}`
  }

  // Default to same-origin
  return `${protocol}//${hostname}`
}

const API_BASE_URL = getApiUrl()

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'X-Tenant-ID': '1'
  }
})

export const dealersApi = {
  getAll: (params) => api.get('/api/dealers', { params }),
  create: (data) => api.post('/api/dealers', data),
  importFromState: (state) => api.post(`/api/dealers/import/${state}`)
}

export const outreachApi = {
  getAll: (params) => api.get('/api/outreach', { params }),
  create: (data) => api.post('/api/outreach', data),
  approve: (id) => api.put(`/api/outreach/${id}/approve`)
}

export const statsApi = {
  get: () => api.get('/api/stats')
}

export const templatesApi = {
  getAll: () => api.get('/api/templates')
}

export const activityApi = {
  getAll: (params) => api.get('/api/activity', { params })
}

export default api
