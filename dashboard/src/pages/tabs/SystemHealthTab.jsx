import React, { useEffect, useState } from 'react'
import { RefreshCw, Database, Server, Cpu, Wifi, CheckCircle, XCircle, AlertCircle, Users, ShieldBan } from 'lucide-react'
import { getSystemStats, recalculateScores, recalculateProfiles, recalculateFingerprints, checkAllModulesHealth } from '../../lib/api'

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

export default function SystemHealthTab() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [recalculating, setRecalculating] = useState(false)
  const [recalcProfiles, setRecalcProfiles] = useState(false)
  const [recalcFingerprints, setRecalcFingerprints] = useState(false)
  const [healthChecking, setHealthChecking] = useState(false)

  useEffect(() => { loadStats() }, [])

  async function loadStats() {
    try {
      const data = await getSystemStats()
      setStats(data)
    } catch (err) {
      console.error('Failed to load health stats:', err)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        <RefreshCw className="w-5 h-5 animate-spin mr-2" /> Loading health data...
      </div>
    )
  }

  if (!stats) {
    return (
      <div className="text-center py-16 text-gray-500">
        <XCircle className="w-12 h-12 mx-auto mb-4 text-[#ff2244]/30" />
        <p>Failed to load health data.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-end gap-3 flex-wrap">
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
        <button onClick={async () => { setRecalcProfiles(true); try { const r = await recalculateProfiles(); alert(`Profiles: ${r.recalculated}/${r.total} updated, ${r.enriched} enriched`) } catch (e) { alert(e.message) } finally { setRecalcProfiles(false) } }}
          disabled={recalcProfiles}
          className="flex items-center gap-2 text-sm text-gray-400 hover:text-[#00ff88] disabled:opacity-50 border border-[#1e1e2e] rounded-lg px-3 py-1.5">
          {recalcProfiles ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Users className="w-4 h-4" />} Recalculate Profiles
        </button>
        <button onClick={async () => { setRecalcFingerprints(true); try { const r = await recalculateFingerprints(); alert(`Fingerprints: ${r.recalculated}/${r.total} recalculated`) } catch (e) { alert(e.message) } finally { setRecalcFingerprints(false) } }}
          disabled={recalcFingerprints}
          className="flex items-center gap-2 text-sm text-gray-400 hover:text-[#00ff88] disabled:opacity-50 border border-[#1e1e2e] rounded-lg px-3 py-1.5">
          {recalcFingerprints ? <RefreshCw className="w-4 h-4 animate-spin" /> : <ShieldBan className="w-4 h-4" />} Recalculate Fingerprints
        </button>
        <button onClick={() => { setRefreshing(true); loadStats() }} disabled={refreshing}
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
    </div>
  )
}
