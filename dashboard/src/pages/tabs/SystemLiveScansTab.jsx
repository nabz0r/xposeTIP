import React, { useEffect, useRef, useState } from 'react'
import { RefreshCw, XCircle, Radar, AlertCircle } from 'lucide-react'
import { useAuth } from '../../lib/auth'
import { getLiveScans, superadminCancelScan } from '../../lib/api'

export default function SystemLiveScansTab() {
  const { refreshKey } = useAuth()
  const [data, setData] = useState({ items: [], total: 0 })
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState(null)
  const pollRef = useRef(null)

  async function load(silent = false) {
    if (!silent) setLoading(true)
    try {
      const res = await getLiveScans()
      setData(res)
      setError(null)
    } catch (err) {
      setError(err.message || 'Failed to load live scans')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    load()
  }, [refreshKey])

  // Polling — 3s cadence, only while at least one scan is live
  useEffect(() => {
    if (data.total === 0) {
      if (pollRef.current) clearInterval(pollRef.current)
      return
    }
    pollRef.current = setInterval(() => load(true), 3000)
    return () => clearInterval(pollRef.current)
  }, [data.total])

  async function handleCancel(scanId, email) {
    if (!window.confirm(`Cancel scan for ${email}? This kills the Celery task.`)) return
    try {
      await superadminCancelScan(scanId)
      load(true)
    } catch (err) {
      alert(`Cancel failed: ${err.message || err}`)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        <RefreshCw className="w-5 h-5 animate-spin mr-2" /> Loading live scans...
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-16 text-gray-500">
        <XCircle className="w-12 h-12 mx-auto mb-4 text-[#ff2244]/30" />
        <p>{error}</p>
        <p className="text-xs mt-1">Superadmin access required.</p>
      </div>
    )
  }

  const statusColors = {
    queued: '#666688',
    running: '#ffcc00',
    completed: '#00ff88',
    failed: '#ff2244',
    cancelled: '#666688',
  }

  function formatAge(seconds) {
    if (seconds == null) return '—'
    if (seconds < 60) return `${seconds}s`
    const m = Math.floor(seconds / 60)
    if (m < 60) return `${m}m ${seconds % 60}s`
    const h = Math.floor(m / 60)
    return `${h}h ${m % 60}m`
  }

  function cascadeBadge(scan) {
    if (!scan.cascade_state || scan.cascade_state === 'done') return null
    const color = scan.cascade_state === 'failed' ? '#ff2244' : '#3388ff'
    return (
      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded ml-2"
        style={{ backgroundColor: color + '26', color }}>
        {scan.cascade_state}
      </span>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Live Scans</h2>
          <p className="text-xs text-gray-500 mt-1">
            {data.total === 0 ? 'No scans in flight' : `${data.total} scan${data.total > 1 ? 's' : ''} in flight across all workspaces`}
            {data.total > 0 && ' · polling every 3s'}
          </p>
        </div>
        <button onClick={() => { setRefreshing(true); load(true) }} disabled={refreshing}
          className="flex items-center gap-2 text-sm text-gray-400 hover:text-white disabled:opacity-50">
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} /> Refresh
        </button>
      </div>

      {data.total === 0 ? (
        <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl py-16 text-center">
          <Radar className="w-10 h-10 mx-auto mb-3 text-gray-700" />
          <p className="text-sm text-gray-500">All scans idle.</p>
          <p className="text-xs text-gray-600 mt-1">New activity will appear here automatically.</p>
        </div>
      ) : (
        <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-gray-500 uppercase tracking-wider border-b border-[#1e1e2e]">
                <th className="text-left px-4 py-3">Workspace</th>
                <th className="text-left px-4 py-3">Target</th>
                <th className="text-left px-4 py-3">Status</th>
                <th className="text-left px-4 py-3">Modules</th>
                <th className="text-right px-4 py-3">Age</th>
                <th className="text-right px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((scan, i) => {
                const pct = scan.modules_total > 0
                  ? Math.round((scan.modules_done / scan.modules_total) * 100)
                  : 0
                const c = statusColors[scan.status] || '#666688'
                return (
                  <tr key={scan.id} className={`border-t border-[#1e1e2e] ${i % 2 === 1 ? 'bg-white/[0.02]' : ''}`}>
                    <td className="px-4 py-3 text-xs text-gray-300 truncate max-w-[140px]">{scan.workspace_name}</td>
                    <td className="px-4 py-3 font-mono text-xs text-gray-300 truncate max-w-[220px]">{scan.target_email}</td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center gap-1.5 text-xs font-medium px-2 py-0.5 rounded-full"
                        style={{ backgroundColor: c + '26', color: c }}>
                        <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: c }} />
                        {scan.status}
                      </span>
                      {cascadeBadge(scan)}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs text-gray-400">
                          {scan.modules_done}/{scan.modules_total}
                        </span>
                        <div className="w-20 h-1 bg-[#0a0a0f] rounded-full overflow-hidden">
                          <div className="h-full bg-[#00ff88] transition-all" style={{ width: `${pct}%` }} />
                        </div>
                        <span className="font-mono text-xs text-gray-500">{pct}%</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-xs text-gray-400">
                      {formatAge(scan.age_seconds)}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => handleCancel(scan.id, scan.target_email)}
                        className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded bg-[#ff2244]/10 text-[#ff2244] hover:bg-[#ff2244]/20 transition-colors"
                      >
                        <XCircle className="w-3 h-3" /> Cancel
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      <div className="text-[10px] text-gray-600 flex items-center gap-1.5">
        <AlertCircle className="w-3 h-3" />
        Superadmin-only view. Cancel uses Celery task revoke + status='cancelled'. Watchdog (S148) catches anything left stuck.
      </div>
    </div>
  )
}
