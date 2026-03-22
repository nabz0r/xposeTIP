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
export const getTargetProfile = (id) => request(`/targets/${id}/profile`)
export const getTargetSources = (id) => request(`/targets/${id}/sources`)
export const bulkImportTargets = (data) => request('/targets/bulk', { method: 'POST', body: JSON.stringify(data) })
export const getFingerprint = (id) => request(`/targets/${id}/fingerprint`)
export const getFingerprintHistory = (id) => request(`/targets/${id}/fingerprint/history`)
export const compareFingerprints = (id, withId) => request(`/targets/${id}/fingerprint/compare?with=${withId}`)
export const moveTarget = (targetId, workspaceId) => request(`/targets/${targetId}/move`, { method: 'PATCH', body: JSON.stringify({ workspace_id: workspaceId }) })

// Scans
export const createScan = (data) => request('/scans', { method: 'POST', body: JSON.stringify(data) })
export const getScans = (params = '') => request(`/scans${params ? '?' + params : ''}`)
export const getScan = (id) => request(`/scans/${id}`)
export const cancelScan = (scanId) => request(`/scans/${scanId}/cancel`, { method: 'POST' })
export const getScraperProgress = (scanId) => request(`/scans/${scanId}/scraper-progress`)

// Findings
export const getFindings = (params = '') => request(`/findings${params ? '?' + params : ''}`)
export const getFindingsStats = (params = '') => request(`/findings/stats${params ? '?' + params : ''}`)
export const patchFinding = (id, data) => request(`/findings/${id}`, { method: 'PATCH', body: JSON.stringify(data) })

// Modules
export const getModules = () => request('/modules')
export const patchModule = (id, data) => request(`/modules/${id}`, { method: 'PATCH', body: JSON.stringify(data) })
export const checkModuleHealth = (id) => request(`/modules/${id}/health`, { method: 'POST' })
export const checkAllModulesHealth = () => request('/modules/health-all', { method: 'POST' })

// Graph
export const getGraph = (targetId) => request(`/graph/${targetId}`)

// System
export const getSystemStats = () => request('/system/stats')
export const recalculateScores = () => request('/system/recalculate-scores', { method: 'POST' })
export const recalculateProfiles = () => request('/system/recalculate-profiles', { method: 'POST' })
export const recalculateFingerprints = () => request('/system/recalculate-fingerprints', { method: 'POST' })
export const getLogs = (params = '') => request(`/system/logs${params ? '?' + params : ''}`)
export const clearLogs = () => request('/system/logs', { method: 'DELETE' })

// Admin (superadmin only)
export const adminListUsers = () => request('/system/users')
export const adminUpdateUser = (userId, data) => request(`/system/users/${userId}`, { method: 'PATCH', body: JSON.stringify(data) })
export const adminListWorkspaces = () => request('/system/workspaces')

// Name Blacklist
export const getNameBlacklist = () => request('/system/name-blacklist')
export const addNameBlacklist = (data) => request('/system/name-blacklist', { method: 'POST', body: JSON.stringify(data) })
export const removeNameBlacklist = (id) => request(`/system/name-blacklist/${id}`, { method: 'DELETE' })

// Settings
export const getApiKeys = () => request('/settings/apikeys')
export const saveApiKey = (key_name, key_value) => request('/settings/apikeys', { method: 'POST', body: JSON.stringify({ key_name, key_value }) })
export const validateApiKey = (key_name) => request(`/settings/apikeys/${key_name}/validate`, { method: 'POST' })
export const deleteApiKey = (key_name) => request(`/settings/apikeys/${key_name}`, { method: 'DELETE' })
export const saveCustomKey = (data) => request('/settings/apikeys/custom', { method: 'POST', body: JSON.stringify(data) })
export const getDefaults = () => request('/settings/defaults')
export const updateDefaults = (data) => request('/settings/defaults', { method: 'PUT', body: JSON.stringify(data) })

// Plans
export const getPlans = () => request('/workspaces/plans')
export const getWorkspaceUsage = (id) => request(`/workspaces/${id}/usage`)
export const updateWorkspacePlan = (id, plan) => request(`/workspaces/${id}/plan`, { method: 'PATCH', body: JSON.stringify({ plan }) })

// Workspaces
export const getWorkspaces = () => request('/workspaces')
export const createWorkspace = (data) => request('/workspaces', { method: 'POST', body: JSON.stringify(data) })
export const updateWorkspace = (id, data) => request(`/workspaces/${id}`, { method: 'PATCH', body: JSON.stringify(data) })
export const deleteWorkspace = (id) => request(`/workspaces/${id}`, { method: 'DELETE' })
export const getWorkspaceMembers = (id) => request(`/workspaces/${id}/members`)
export const inviteMember = (id, data) => request(`/workspaces/${id}/invite`, { method: 'POST', body: JSON.stringify(data) })
export const updateMemberRole = (wsId, userId, data) => request(`/workspaces/${wsId}/members/${userId}`, { method: 'PATCH', body: JSON.stringify(data) })
export const removeMember = (wsId, userId) => request(`/workspaces/${wsId}/members/${userId}`, { method: 'DELETE' })
export const switchWorkspace = (workspace_id) => request('/auth/switch-workspace', { method: 'POST', body: JSON.stringify({ workspace_id }) })
export const getWorkspaceTargets = (id) => request(`/workspaces/${id}/targets`)
export const shareTarget = (wsId, data) => request(`/workspaces/${wsId}/targets`, { method: 'POST', body: JSON.stringify(data) })
export const unshareTarget = (wsId, targetId) => request(`/workspaces/${wsId}/targets/${targetId}`, { method: 'DELETE' })

// Connected Accounts (OAuth)
export const getAccounts = (targetId) => request(`/accounts${targetId ? '?target_id=' + targetId : ''}`)
export const startOAuth = (data) => request('/accounts/oauth/start', { method: 'POST', body: JSON.stringify(data) })
export const oauthCallback = (data) => request('/accounts/oauth/callback', { method: 'POST', body: JSON.stringify(data) })
export const auditAccount = (accountId) => request(`/accounts/${accountId}/audit`, { method: 'POST' })
export const disconnectAccount = (accountId) => request(`/accounts/${accountId}`, { method: 'DELETE' })

// Scrapers
export const getScrapers = (params = '') => request(`/scrapers${params ? '?' + params : ''}`)
export const getScraper = (id) => request(`/scrapers/${id}`)
export const createScraper = (data) => request('/scrapers', { method: 'POST', body: JSON.stringify(data) })
export const updateScraper = (id, data) => request(`/scrapers/${id}`, { method: 'PATCH', body: JSON.stringify(data) })
export const deleteScraper = (id) => request(`/scrapers/${id}`, { method: 'DELETE' })
export const testScraper = (id, input) => request(`/scrapers/${id}/test`, { method: 'POST', body: JSON.stringify({ input }) })
export const toggleScraper = (id) => request(`/scrapers/${id}/toggle`, { method: 'POST' })
export const exportScraper = (id) => request(`/scrapers/${id}/export`, { method: 'POST' })
export const importScraper = (data) => request('/scrapers/import', { method: 'POST', body: JSON.stringify(data) })

// User profile
export const updateProfile = (data) => request('/auth/profile', { method: 'PATCH', body: JSON.stringify(data) })
export const changePassword = (data) => request('/auth/password', { method: 'POST', body: JSON.stringify(data) })
