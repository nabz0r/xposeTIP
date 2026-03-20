const BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

async function request(path, options = {}) {
  const token = localStorage.getItem('xpose_token')
  const headers = { 'Content-Type': 'application/json', ...options.headers }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers })

  if (res.status === 401) {
    // Try refresh
    const refreshToken = localStorage.getItem('xpose_refresh')
    if (refreshToken && !path.includes('/auth/')) {
      try {
        const refreshRes = await fetch(`${BASE_URL}/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refreshToken }),
        })
        if (refreshRes.ok) {
          const data = await refreshRes.json()
          localStorage.setItem('xpose_token', data.access_token)
          localStorage.setItem('xpose_refresh', data.refresh_token)
          headers['Authorization'] = `Bearer ${data.access_token}`
          const retry = await fetch(`${BASE_URL}${path}`, { ...options, headers })
          if (!retry.ok) throw new Error(`${retry.status}`)
          return retry.status === 204 ? null : retry.json()
        }
      } catch {}
    }
    localStorage.removeItem('xpose_token')
    localStorage.removeItem('xpose_refresh')
    window.location.href = '/login'
    throw new Error('Unauthorized')
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Request failed: ${res.status}`)
  }

  return res.status === 204 ? null : res.json()
}

// Auth
export const login = (email, password) =>
  request('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) })

export const register = (email, password, display_name) =>
  request('/auth/register', { method: 'POST', body: JSON.stringify({ email, password, display_name }) })

export const getMe = () => request('/auth/me')

// Targets
export const getTargets = (params = '') => request(`/targets${params ? '?' + params : ''}`)
export const createTarget = (data) => request('/targets', { method: 'POST', body: JSON.stringify(data) })
export const getTarget = (id) => request(`/targets/${id}`)
export const deleteTarget = (id) => request(`/targets/${id}?confirm=true`, { method: 'DELETE' })

// Scans
export const createScan = (data) => request('/scans', { method: 'POST', body: JSON.stringify(data) })
export const getScans = (params = '') => request(`/scans${params ? '?' + params : ''}`)
export const getScan = (id) => request(`/scans/${id}`)

// Findings
export const getFindings = (params = '') => request(`/findings${params ? '?' + params : ''}`)
export const getFindingsStats = (params = '') => request(`/findings/stats${params ? '?' + params : ''}`)
export const patchFinding = (id, data) => request(`/findings/${id}`, { method: 'PATCH', body: JSON.stringify(data) })

// Modules
export const getModules = () => request('/modules')
export const patchModule = (id, data) => request(`/modules/${id}`, { method: 'PATCH', body: JSON.stringify(data) })

// Graph
export const getGraph = (targetId) => request(`/graph/${targetId}`)
