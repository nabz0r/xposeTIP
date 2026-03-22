import React, { useEffect, useState } from 'react'
import { RefreshCw, XCircle } from 'lucide-react'
import { getSystemStats } from '../../lib/api'
import useSSE from '../../hooks/useSSE'

export default function SystemDashboardTab() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  useEffect(() => { loadStats() }, [])
  useSSE({ 'scan.completed': () => loadStats() })

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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        <RefreshCw className="w-5 h-5 animate-spin mr-2" /> Loading stats...
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
      <div className="flex items-center justify-end">
        <button onClick={() => { setRefreshing(true); loadStats() }} disabled={refreshing}
          className="flex items-center gap-2 text-sm text-gray-400 hover:text-white disabled:opacity-50">
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} /> Refresh
        </button>
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
