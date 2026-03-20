import { useEffect, useState } from 'react'
import { RefreshCw, Database, Server, Cpu, Wifi, CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import { getSystemStats, recalculateScores, checkAllModulesHealth } from '../lib/api'

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

export default function System() {
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
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">System</h1>
        <div className="flex items-center gap-3">
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
                  <th className="text-left px-5 py-3">Scan</th>
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
                      <td className="px-5 py-3 font-mono text-xs text-gray-400">{s.id.slice(0, 8)}</td>
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
