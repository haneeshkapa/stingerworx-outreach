import axios from 'axios'

const getApiUrl = () => {
  if (typeof window === 'undefined') return '/api'
  
  const hostname = window.location.hostname
  
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return 'http://localhost:8000'
  }
  
  return ''
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

export default api
