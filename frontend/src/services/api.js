import axios from 'axios'

const getApiUrl = () => {
  if (typeof window === 'undefined') return '/api'

  // Allow explicit override (e.g. VITE_API_URL=https://my-backend)
  if (import.meta.env?.VITE_API_URL) return import.meta.env.VITE_API_URL

  // Always use same-origin (empty baseURL)
  // In dev: Vite proxy handles /api → http://0.0.0.0:8000
  // In production: Deploy frontend and backend together
  return ''
}

const API_BASE_URL = getApiUrl()

if (typeof window !== 'undefined') {
  console.info('[API] Base URL resolved', {
    baseURL: API_BASE_URL || '(same-origin)',
    frontendOrigin: window.location.origin,
    hostname: window.location.hostname
  })
}

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'X-Tenant-ID': '1'
  }
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (typeof window !== 'undefined') {
      console.error('[API] Request failed', {
        message: error.message,
        code: error.code,
        url: error.config?.url,
        baseURL: error.config?.baseURL,
        fullUrl: error.config ? `${error.config.baseURL || ''}${error.config.url || ''}` : undefined,
        origin: window.location.origin
      })
    }
    return Promise.reject(error)
  }
)

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
