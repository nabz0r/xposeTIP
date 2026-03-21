import React, { useEffect, useState } from 'react'
import { RefreshCw, Database, Server, Cpu, Wifi, CheckCircle, XCircle, AlertCircle, ScrollText, Users, Building2, Search, ChevronDown, ChevronRight, ShieldBan } from 'lucide-react'
import { getSystemStats, recalculateScores, checkAllModulesHealth, adminListUsers, adminUpdateUser, adminListWorkspaces, updateWorkspacePlan, getNameBlacklist, addNameBlacklist, removeNameBlacklist } from '../lib/api'
import { useAuth } from '../lib/auth'
import LogViewer from '../components/LogViewer'

const statusIcon = (status) => {
  if (status === 'healthy') return <CheckCircle className="w-4 h-4 text-[#00ff88]" />
  if (status === 'unhealthy') return <XCircle className="w-4 h-4 text-[#ff2244]" />
  return <AlertCircle className="w-4 h-4 text-[#ffcc00]" />
}

const statusColor = (status) => {
  if (status === 'healthy') return '#00ff88'
  if (status === 'unhealthy') return '#ff2244'
  return '#ffcc00'
}

const infraIcons = {
  postgresql: Database,
  redis: Server,
  celery: Cpu,
  api: Wifi,
}

function InfraCard({ name, data }) {
  const Icon = infraIcons[name] || Server
  const color = statusColor(data.status)
  return (
    <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5 hover:shadow-[0_0_20px_rgba(0,255,136,0.05)] transition-shadow">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Icon className="w-5 h-5" style={{ color }} />
          <span className="text-sm font-semibold capitalize">{name}</span>
        </div>
        {statusIcon(data.status)}
      </div>
      <div className="space-y-1 text-xs">
        <div className="flex justify-between">
          <span className="text-gray-500">Status</span>
          <span className="font-mono" style={{ color }}>{data.status}</span>
        </div>
        {data.version && (
          <div className="flex justify-between">
            <span className="text-gray-500">Version</span>
            <span className="font-mono text-gray-400 truncate max-w-[200px]">{data.version}</span>
          </div>
        )}
        {data.workers !== undefined && (
          <div className="flex justify-between">
            <span className="text-gray-500">Workers</span>
            <span className="font-mono">{data.workers}</span>
          </div>
        )}
        {data.active_tasks !== undefined && (
          <div className="flex justify-between">
            <span className="text-gray-500">Active Tasks</span>
            <span className="font-mono">{data.active_tasks}</span>
          </div>
        )}
        {data.connected_clients !== undefined && (
          <div className="flex justify-between">
            <span className="text-gray-500">Connections</span>
            <span className="font-mono">{data.connected_clients}</span>
          </div>
        )}
        {data.error && (
          <div className="text-[#ff2244] font-mono truncate mt-1" title={data.error}>{data.error}</div>
        )}
      </div>
    </div>
  )
}

function DashboardTab() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [recalculating, setRecalculating] = useState(false)
  const [healthChecking, setHealthChecking] = useState(false)

  useEffect(() => { loadStats() }, [])

  async function loadStats() {
    try {
      const data = await getSystemStats()
      setStats(data)
    } catch (err) {
      console.error('Failed to load system stats:', err)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  function handleRefresh() {
    setRefreshing(true)
    loadStats()
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        <RefreshCw className="w-5 h-5 animate-spin mr-2" /> Loading system stats...
      </div>
    )
  }

  if (!stats) {
    return (
      <div className="text-center py-16 text-gray-500">
        <XCircle className="w-12 h-12 mx-auto mb-4 text-[#ff2244]/30" />
        <p>Failed to load system stats.</p>
        <p className="text-xs mt-1">You may need superadmin access.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-end gap-3">
        <button onClick={async () => {
            setHealthChecking(true)
            try {
              const r = await checkAllModulesHealth()
              const healthy = r.results.filter(m => m.health_status === 'healthy').length
              alert(`Health checks done: ${healthy}/${r.total} healthy`)
              loadStats()
            } catch (e) { alert(e.message) }
            finally { setHealthChecking(false) }
          }}
          disabled={healthChecking}
          className="flex items-center gap-2 text-sm text-gray-400 hover:text-[#00ff88] disabled:opacity-50 border border-[#1e1e2e] rounded-lg px-3 py-1.5">
          {healthChecking ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Cpu className="w-4 h-4" />} Run Health Checks
        </button>
        <button onClick={async () => { setRecalculating(true); try { const r = await recalculateScores(); alert(`Recalculated ${r.recalculated}/${r.total} targets`) } catch (e) { alert(e.message) } finally { setRecalculating(false) } }}
          disabled={recalculating}
          className="flex items-center gap-2 text-sm text-gray-400 hover:text-[#00ff88] disabled:opacity-50 border border-[#1e1e2e] rounded-lg px-3 py-1.5">
          {recalculating ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Database className="w-4 h-4" />} Recalculate Scores
        </button>
        <button onClick={handleRefresh} disabled={refreshing}
          className="flex items-center gap-2 text-sm text-gray-400 hover:text-white disabled:opacity-50">
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} /> Refresh
        </button>
      </div>

      {/* Infrastructure Health */}
      <div>
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">Infrastructure Health</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Object.entries(stats.infrastructure || {}).map(([name, data]) => (
            <InfraCard key={name} name={name} data={data} />
          ))}
        </div>
      </div>

      {/* Database Explorer */}
      <div>
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">Database Explorer</h2>
        <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-gray-500 uppercase tracking-wider border-b border-[#1e1e2e]">
                <th className="text-left px-5 py-3">Table</th>
                <th className="text-right px-5 py-3">Row Count</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(stats.tables || {}).map(([table, data], i) => (
                <tr key={table} className={`border-t border-[#1e1e2e] ${i % 2 === 1 ? 'bg-white/[0.02]' : ''}`}>
                  <td className="px-5 py-3 font-mono">{table}</td>
                  <td className="px-5 py-3 font-mono text-right">{data.count.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Module Health Matrix */}
      <div>
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">Module Health Matrix</h2>
        <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-gray-500 uppercase tracking-wider border-b border-[#1e1e2e]">
                <th className="text-left px-5 py-3">Module</th>
                <th className="text-left px-5 py-3">Layer</th>
                <th className="text-left px-5 py-3">Status</th>
                <th className="text-left px-5 py-3">Health</th>
                <th className="text-right px-5 py-3">Findings</th>
                <th className="text-left px-5 py-3">Last Check</th>
              </tr>
            </thead>
            <tbody>
              {(stats.modules || []).map((m, i) => (
                <tr key={m.id} className={`border-t border-[#1e1e2e] ${i % 2 === 1 ? 'bg-white/[0.02]' : ''}`}>
                  <td className="px-5 py-3">
                    <div className="font-mono text-xs">{m.id}</div>
                    <div className="text-[10px] text-gray-500">{m.display_name}</div>
                  </td>
                  <td className="px-5 py-3">
                    <span className="text-xs font-mono bg-[#1e1e2e] px-2 py-0.5 rounded">L{m.layer}</span>
                  </td>
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-2">
                      {m.enabled ? (
                        <span className="text-xs text-[#00ff88]">Enabled</span>
                      ) : (
                        <span className="text-xs text-gray-500">Disabled</span>
                      )}
                      {!m.implemented && (
                        <span className="text-[10px] bg-[#ffcc00]/15 text-[#ffcc00] px-1.5 py-0.5 rounded">No scanner</span>
                      )}
                    </div>
                  </td>
                  <td className="px-5 py-3">
                    <span className="inline-flex items-center gap-1.5 text-xs">
                      {statusIcon(m.health_status === 'unknown' ? 'warning' : m.health_status === 'healthy' ? 'healthy' : 'unhealthy')}
                      <span className="text-gray-400">{m.health_status}</span>
                    </span>
                  </td>
                  <td className="px-5 py-3 text-right font-mono">{m.findings_count}</td>
                  <td className="px-5 py-3 text-gray-500 text-xs">
                    {m.last_health ? new Date(m.last_health).toLocaleString() : 'Never'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recent Scans */}
      {(stats.recent_scans || []).length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">Recent Activity</h2>
          <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs text-gray-500 uppercase tracking-wider border-b border-[#1e1e2e]">
                  <th className="text-left px-5 py-3">Target</th>
                  <th className="text-left px-5 py-3">Status</th>
                  <th className="text-left px-5 py-3">Modules</th>
                  <th className="text-right px-5 py-3">Findings</th>
                  <th className="text-left px-5 py-3">Date</th>
                </tr>
              </thead>
              <tbody>
                {stats.recent_scans.map((s, i) => {
                  const statusColors = { queued: '#666688', running: '#ffcc00', completed: '#00ff88', failed: '#ff2244' }
                  return (
                    <tr key={s.id} className={`border-t border-[#1e1e2e] ${i % 2 === 1 ? 'bg-white/[0.02]' : ''}`}>
                      <td className="px-5 py-3 font-mono text-xs text-gray-300 truncate max-w-[200px]">{s.target_email || s.id.slice(0, 8)}</td>
                      <td className="px-5 py-3">
                        <span className="inline-flex items-center gap-1.5 text-xs font-medium px-2 py-0.5 rounded-full"
                          style={{ backgroundColor: (statusColors[s.status] || '#666688') + '26', color: statusColors[s.status] || '#666688' }}>
                          <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: statusColors[s.status] || '#666688' }} />
                          {s.status}
                        </span>
                      </td>
                      <td className="px-5 py-3 font-mono text-xs text-gray-400">{(s.modules || []).join(', ')}</td>
                      <td className="px-5 py-3 font-mono text-right">{s.findings_count || 0}</td>
                      <td className="px-5 py-3 text-gray-500 text-xs">{s.created_at ? new Date(s.created_at).toLocaleString() : '-'}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

const roleColors = {
  superadmin: '#ff2244', admin: '#ff8800', consultant: '#3388ff', client: '#00ff88', user: '#666688',
}
const planColors = { free: '#666688', consultant: '#3388ff', enterprise: '#00ff88' }

// ===================== Users Tab (superadmin only) =====================
function UsersTab() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [expanded, setExpanded] = useState(null)

  useEffect(() => { loadUsers() }, [])

  async function loadUsers() {
    try {
      const data = await adminListUsers()
      setUsers(data.items || [])
    } catch {}
    finally { setLoading(false) }
  }

  async function toggleActive(userId, currentActive) {
    try {
      await adminUpdateUser(userId, { is_active: !currentActive })
      loadUsers()
    } catch (err) { alert(err.message) }
  }

  if (loading) return <div className="text-gray-500 py-8 text-center">Loading users...</div>

  const filtered = users.filter(u =>
    !search || u.email.toLowerCase().includes(search.toLowerCase()) || (u.display_name || '').toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-500 uppercase tracking-wider font-semibold">Platform Users ({users.length})</span>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
        <input type="text" value={search} onChange={e => setSearch(e.target.value)} placeholder="Search by email or name..."
          className="w-full bg-[#12121a] border border-[#1e1e2e] rounded-lg pl-10 pr-3 py-2 text-sm font-mono focus:outline-none focus:border-[#00ff88]/50" />
      </div>

      <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-gray-500 uppercase tracking-wider border-b border-[#1e1e2e]">
              <th className="text-left px-5 py-3 w-8"></th>
              <th className="text-left px-5 py-3">Email</th>
              <th className="text-left px-5 py-3">Display Name</th>
              <th className="text-left px-5 py-3">Role</th>
              <th className="text-left px-5 py-3">Workspaces</th>
              <th className="text-left px-5 py-3">Last Login</th>
              <th className="text-left px-5 py-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((u, i) => {
              const isExpanded = expanded === u.id
              return (
                <React.Fragment key={u.id}>
                  <tr
                    onClick={() => setExpanded(isExpanded ? null : u.id)}
                    className={`border-t border-[#1e1e2e] cursor-pointer hover:bg-white/[0.03] ${i % 2 === 1 ? 'bg-white/[0.02]' : ''}`}
                  >
                    <td className="px-5 py-3 text-gray-500">
                      {isExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                    </td>
                    <td className="px-5 py-3 font-mono">{u.email}</td>
                    <td className="px-5 py-3 text-gray-400">{u.display_name || '-'}</td>
                    <td className="px-5 py-3">
                      <span className="text-xs font-medium px-2 py-0.5 rounded"
                        style={{ backgroundColor: (roleColors[u.highest_role] || '#666688') + '26', color: roleColors[u.highest_role] || '#666688' }}>
                        {u.highest_role}
                      </span>
                    </td>
                    <td className="px-5 py-3 font-mono text-gray-400">{u.workspace_count}</td>
                    <td className="px-5 py-3 text-xs text-gray-500">
                      {u.last_login ? new Date(u.last_login).toLocaleString() : 'Never'}
                    </td>
                    <td className="px-5 py-3">
                      <button onClick={(e) => { e.stopPropagation(); toggleActive(u.id, u.is_active) }}
                        className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                          u.is_active ? 'bg-[#00ff88]/15 text-[#00ff88]' : 'bg-[#ff2244]/15 text-[#ff2244]'
                        }`}>
                        {u.is_active ? 'active' : 'inactive'}
                      </button>
                    </td>
                  </tr>
                  {isExpanded && (
                    <tr className="border-t border-[#1e1e2e]/50">
                      <td colSpan={7} className="px-10 py-3 bg-[#0a0a0f]">
                        <div className="text-xs text-gray-500 mb-2">Workspace memberships</div>
                        <div className="space-y-1.5">
                          {u.workspaces.map(ws => (
                            <div key={ws.workspace_id} className="flex items-center gap-3 text-xs">
                              <span className="text-gray-300">{ws.workspace_name}</span>
                              <span className="font-medium px-1.5 py-0.5 rounded text-[10px]"
                                style={{ backgroundColor: (roleColors[ws.role] || '#666688') + '26', color: roleColors[ws.role] || '#666688' }}>
                                {ws.role}
                              </span>
                              <span className="font-mono px-1.5 py-0.5 rounded text-[10px]"
                                style={{ backgroundColor: (planColors[ws.plan] || '#666688') + '15', color: planColors[ws.plan] || '#666688' }}>
                                {ws.plan}
                              </span>
                            </div>
                          ))}
                          {u.workspaces.length === 0 && <span className="text-gray-600">No workspaces</span>}
                        </div>
                        <div className="mt-2 text-[10px] text-gray-600">
                          Created: {u.created_at ? new Date(u.created_at).toLocaleString() : '-'}
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              )
            })}
            {filtered.length === 0 && (
              <tr><td colSpan={7} className="px-5 py-8 text-center text-gray-500">No users found</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ===================== Workspaces Tab (superadmin only) =====================
function WorkspacesTab() {
  const [workspaces, setWorkspaces] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => { loadWorkspaces() }, [])

  async function loadWorkspaces() {
    try {
      const data = await adminListWorkspaces()
      setWorkspaces(data.items || [])
    } catch {}
    finally { setLoading(false) }
  }

  async function handlePlanChange(wsId, newPlan) {
    try {
      await updateWorkspacePlan(wsId, newPlan)
      loadWorkspaces()
    } catch (err) { alert(err.message) }
  }

  if (loading) return <div className="text-gray-500 py-8 text-center">Loading workspaces...</div>

  return (
    <div className="space-y-4">
      <span className="text-xs text-gray-500 uppercase tracking-wider font-semibold">All Workspaces ({workspaces.length})</span>

      <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-gray-500 uppercase tracking-wider border-b border-[#1e1e2e]">
              <th className="text-left px-5 py-3">Name</th>
              <th className="text-left px-5 py-3">Plan</th>
              <th className="text-right px-5 py-3">Members</th>
              <th className="text-right px-5 py-3">Targets</th>
              <th className="text-right px-5 py-3">Scans</th>
              <th className="text-left px-5 py-3">Created</th>
            </tr>
          </thead>
          <tbody>
            {workspaces.map((ws, i) => (
              <tr key={ws.id} className={`border-t border-[#1e1e2e] ${i % 2 === 1 ? 'bg-white/[0.02]' : ''}`}>
                <td className="px-5 py-3">
                  <div className="font-medium">{ws.name}</div>
                  <div className="text-[10px] text-gray-600 font-mono">{ws.slug}</div>
                </td>
                <td className="px-5 py-3">
                  <select value={ws.plan} onChange={e => handlePlanChange(ws.id, e.target.value)}
                    className="bg-[#0a0a0f] border border-[#1e1e2e] rounded px-2 py-1 text-xs focus:outline-none focus:border-[#00ff88]/50"
                    style={{ color: planColors[ws.plan] || '#666688' }}>
                    <option value="free">free</option>
                    <option value="consultant">consultant</option>
                    <option value="enterprise">enterprise</option>
                  </select>
                </td>
                <td className="px-5 py-3 text-right font-mono">{ws.member_count}</td>
                <td className="px-5 py-3 text-right font-mono">{ws.target_count}</td>
                <td className="px-5 py-3 text-right font-mono">{ws.scan_count}</td>
                <td className="px-5 py-3 text-xs text-gray-500">
                  {ws.created_at ? new Date(ws.created_at).toLocaleDateString() : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ===================== Name Rules Tab =====================
function NameRulesTab() {
  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(true)
  const [newPattern, setNewPattern] = useState('')
  const [newType, setNewType] = useState('exact')
  const [newReason, setNewReason] = useState('')
  const [testName, setTestName] = useState('')
  const [testResult, setTestResult] = useState(null)

  useEffect(() => { loadEntries() }, [])

  async function loadEntries() {
    try {
      const data = await getNameBlacklist()
      setEntries(data.items || [])
    } catch {}
    finally { setLoading(false) }
  }

  async function handleAdd(e) {
    e.preventDefault()
    if (!newPattern.trim()) return
    try {
      await addNameBlacklist({ pattern: newPattern.trim(), type: newType, reason: newReason.trim() || null })
      setNewPattern('')
      setNewReason('')
      loadEntries()
    } catch (err) { alert(err.message) }
  }

  async function handleDelete(id) {
    try {
      await removeNameBlacklist(id)
      loadEntries()
    } catch (err) { alert(err.message) }
  }

  function handleTest(name) {
    setTestName(name)
    if (!name.trim() || name.trim().length < 3) {
      setTestResult({ blocked: true, reason: 'Too short (< 3 chars)' })
      return
    }
    const val = name.trim()
    const valLower = val.toLowerCase()
    for (const entry of entries) {
      const pattern = entry.pattern.toLowerCase()
      if (entry.type === 'exact' && valLower === pattern) {
        setTestResult({ blocked: true, reason: `Exact match: "${entry.pattern}" — ${entry.reason || ''}` })
        return
      }
      if (entry.type === 'contains' && valLower.includes(pattern)) {
        setTestResult({ blocked: true, reason: `Contains: "${entry.pattern}" — ${entry.reason || ''}` })
        return
      }
      if (entry.type === 'regex') {
        try {
          if (new RegExp(entry.pattern, 'i').test(val)) {
            setTestResult({ blocked: true, reason: `Regex: "${entry.pattern}" — ${entry.reason || ''}` })
            return
          }
        } catch {}
      }
    }
    setTestResult({ blocked: false })
  }

  if (loading) return <div className="text-gray-500 py-8 text-center">Loading name rules...</div>

  const typeColors = { exact: '#3388ff', contains: '#ffcc00', regex: '#ff8800' }

  return (
    <div className="space-y-4">
      <span className="text-xs text-gray-500 uppercase tracking-wider font-semibold">Name Blacklist Rules ({entries.length})</span>

      {/* Test input */}
      <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-4">
        <label className="text-xs text-gray-400 mb-2 block">Test a name against the blacklist</label>
        <div className="flex gap-3 items-center">
          <input type="text" value={testName} onChange={e => { handleTest(e.target.value) }}
            placeholder="Type a name to test..."
            className="flex-1 bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:border-[#00ff88]/50" />
          {testResult && (
            <span className={`text-xs font-mono px-3 py-1.5 rounded-lg ${
              testResult.blocked ? 'bg-[#ff2244]/15 text-[#ff2244]' : 'bg-[#00ff88]/15 text-[#00ff88]'
            }`}>
              {testResult.blocked ? `BLOCKED — ${testResult.reason}` : 'OK — passes all rules'}
            </span>
          )}
        </div>
      </div>

      {/* Add form */}
      <form onSubmit={handleAdd} className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-4">
        <label className="text-xs text-gray-400 mb-2 block">Add new rule</label>
        <div className="flex gap-2 items-end">
          <div className="flex-1">
            <input type="text" value={newPattern} onChange={e => setNewPattern(e.target.value)} required placeholder="Pattern..."
              className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:border-[#00ff88]/50" />
          </div>
          <select value={newType} onChange={e => setNewType(e.target.value)}
            className="bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#00ff88]/50">
            <option value="exact">exact</option>
            <option value="contains">contains</option>
            <option value="regex">regex</option>
          </select>
          <div className="w-40">
            <input type="text" value={newReason} onChange={e => setNewReason(e.target.value)} placeholder="Reason..."
              className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#00ff88]/50" />
          </div>
          <button type="submit" className="bg-[#00ff88] text-black font-semibold rounded-lg px-4 py-2 text-sm hover:bg-[#00ff88]/90">
            Add Rule
          </button>
        </div>
      </form>

      {/* Rules table */}
      <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-gray-500 uppercase tracking-wider border-b border-[#1e1e2e]">
              <th className="text-left px-5 py-3">Pattern</th>
              <th className="text-left px-5 py-3">Type</th>
              <th className="text-left px-5 py-3">Reason</th>
              <th className="text-right px-5 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {entries.map((e, i) => (
              <tr key={e.id} className={`border-t border-[#1e1e2e] ${i % 2 === 1 ? 'bg-white/[0.02]' : ''}`}>
                <td className="px-5 py-2 font-mono text-xs">{e.pattern}</td>
                <td className="px-5 py-2">
                  <span className="text-[10px] font-medium px-2 py-0.5 rounded"
                    style={{ backgroundColor: (typeColors[e.type] || '#666688') + '26', color: typeColors[e.type] || '#666688' }}>
                    {e.type}
                  </span>
                </td>
                <td className="px-5 py-2 text-xs text-gray-400">{e.reason || '-'}</td>
                <td className="px-5 py-2 text-right">
                  <button onClick={() => handleDelete(e.id)} className="text-xs text-gray-500 hover:text-[#ff2244]">Delete</button>
                </td>
              </tr>
            ))}
            {entries.length === 0 && (
              <tr><td colSpan={4} className="px-5 py-8 text-center text-gray-500">No rules defined</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default function System() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const { user } = useAuth()

  // Check if superadmin from JWT
  const isSuperAdmin = (() => {
    const token = localStorage.getItem('xpose_token')
    if (!token) return false
    try {
      return JSON.parse(atob(token.split('.')[1])).role === 'superadmin'
    } catch { return false }
  })()

  const TABS = [
    { id: 'dashboard', label: 'Dashboard', icon: Server },
    { id: 'logs', label: 'Logs', icon: ScrollText },
    ...(isSuperAdmin ? [
      { id: 'users', label: 'Users', icon: Users },
      { id: 'workspaces', label: 'Workspaces', icon: Building2 },
      { id: 'namerules', label: 'Name Rules', icon: ShieldBan },
    ] : []),
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">System</h1>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-[#1e1e2e]">
        {TABS.map(tab => {
          const Icon = tab.icon
          const active = activeTab === tab.id
          return (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                active
                  ? 'border-[#00ff88] text-[#00ff88]'
                  : 'border-transparent text-gray-500 hover:text-gray-300'
              }`}>
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* Tab content */}
      {activeTab === 'dashboard' && <DashboardTab />}
      {activeTab === 'logs' && <LogViewer />}
      {activeTab === 'users' && isSuperAdmin && <UsersTab />}
      {activeTab === 'workspaces' && isSuperAdmin && <WorkspacesTab />}
      {activeTab === 'namerules' && isSuperAdmin && <NameRulesTab />}
    </div>
  )
}
