import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Auto-refresh on 401
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      const refresh = localStorage.getItem('refresh_token')
      if (refresh) {
        try {
          const { data } = await axios.post(`${BASE_URL}/auth/refresh`, { refresh_token: refresh })
          localStorage.setItem('access_token', data.access_token)
          localStorage.setItem('refresh_token', data.refresh_token)
          original.headers.Authorization = `Bearer ${data.access_token}`
          return api(original)
        } catch {
          localStorage.clear()
          window.location.href = '/login'
        }
      } else {
        localStorage.clear()
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// ─── Auth ───────────────────────────────────────────────────────────────────
export const authApi = {
  register: (data: { email: string; username: string; password: string; full_name?: string }) =>
    api.post('/auth/register', data).then(r => r.data),
  login: (data: { email: string; password: string }) =>
    api.post('/auth/login', data).then(r => r.data),
  me: () => api.get('/auth/me').then(r => r.data),
  updateSMTP: (data: object) => api.put('/auth/smtp-settings', data).then(r => r.data),
}

// ─── Campaigns ──────────────────────────────────────────────────────────────
export const campaignsApi = {
  list: (params?: object) => api.get('/campaigns/', { params }).then(r => r.data),
  create: (data: object) => api.post('/campaigns/', data).then(r => r.data),
  get: (id: string) => api.get(`/campaigns/${id}`).then(r => r.data),
  update: (id: string, data: object) => api.put(`/campaigns/${id}`, data).then(r => r.data),
  delete: (id: string) => api.delete(`/campaigns/${id}`),
  launch: (id: string) => api.post(`/campaigns/${id}/launch`).then(r => r.data),
  pause: (id: string) => api.post(`/campaigns/${id}/pause`).then(r => r.data),
  resume: (id: string) => api.post(`/campaigns/${id}/resume`).then(r => r.data),
  clone: (id: string) => api.post(`/campaigns/${id}/clone`).then(r => r.data),
  generateEmails: (id: string, candidateProfile: string) =>
    api.post(`/campaigns/${id}/generate-emails`, null, { params: { candidate_profile: candidateProfile } }).then(r => r.data),
  generateAISummary: (id: string) => api.post(`/campaigns/${id}/ai-summary`).then(r => r.data),
}

// ─── Contacts ───────────────────────────────────────────────────────────────
export const contactsApi = {
  list: (campaignId: string, params?: object) =>
    api.get(`/contacts/${campaignId}`, { params }).then(r => r.data),
  get: (campaignId: string, contactId: string) =>
    api.get(`/contacts/${campaignId}/${contactId}`).then(r => r.data),
  getEmails: (campaignId: string, contactId: string) =>
    api.get(`/contacts/${campaignId}/${contactId}/emails`).then(r => r.data),
  delete: (campaignId: string, contactId: string) =>
    api.delete(`/contacts/${campaignId}/${contactId}`),
}

// ─── Upload ─────────────────────────────────────────────────────────────────
export const uploadApi = {
  contacts: (campaignId: string, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post(`/upload/contacts/${campaignId}`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(r => r.data)
  },
  resume: (campaignId: string, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post(`/upload/resume/${campaignId}`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(r => r.data)
  },
}

// ─── Analytics ──────────────────────────────────────────────────────────────
export const analyticsApi = {
  overview: (days?: number) => api.get('/analytics/overview', { params: { days } }).then(r => r.data),
  campaign: (campaignId: string) => api.get(`/analytics/campaign/${campaignId}`).then(r => r.data),
}

// ─── Templates ──────────────────────────────────────────────────────────────
export const templatesApi = {
  list: () => api.get('/templates/').then(r => r.data),
  create: (data: object) => api.post('/templates/', data).then(r => r.data),
  update: (id: string, data: object) => api.put(`/templates/${id}`, data).then(r => r.data),
  delete: (id: string) => api.delete(`/templates/${id}`),
}

// ─── AI ─────────────────────────────────────────────────────────────────────
export const aiApi = {
  generateEmail: (data: object) => api.post('/ai/generate-email', data).then(r => r.data),
}

// ─── Replies ────────────────────────────────────────────────────────────────
export const repliesApi = {
  list: (campaignId: string) => api.get(`/replies/${campaignId}`).then(r => r.data),
  triggerCheck: () => api.post('/replies/check').then(r => r.data),
}

// ─── Export ─────────────────────────────────────────────────────────────────
export const exportApi = {
  csv: (campaignId: string) => `${BASE_URL}/export/campaign/${campaignId}/csv`,
  excel: (campaignId: string) => `${BASE_URL}/export/campaign/${campaignId}/excel`,
  pdf: (campaignId: string) => `${BASE_URL}/export/campaign/${campaignId}/pdf`,
}

// ─── Audit ──────────────────────────────────────────────────────────────────
export const auditApi = {
  list: (params?: object) => api.get('/audit/', { params }).then(r => r.data),
}

export default api
