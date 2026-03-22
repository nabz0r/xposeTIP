import React, { useEffect, useState } from 'react'
import { RefreshCw, CheckCircle, XCircle, AlertCircle, ChevronDown, ChevronRight } from 'lucide-react'
import { getSystemStats, patchModule } from '../../lib/api'

const statusIcon = (status) => {
  if (status === 'healthy') return <CheckCircle className="w-4 h-4 text-[#00ff88]" />
  if (status === 'unhealthy') return <XCircle className="w-4 h-4 text-[#ff2244]" />
  return <AlertCircle className="w-4 h-4 text-[#ffcc00]" />
}

export default function SystemModulesTab() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [expandedModule, setExpandedModule] = useState(null)

  useEffect(() => { loadModules() }, [])

  async function loadModules() {
    try {
      const data = await getSystemStats()
      setStats(data)
    } catch (err) {
      console.error('Failed to load module data:', err)
    } finally {
      setLoading(false)
    }
  }

  async function handleToggle(m) {
    try {
      await patchModule(m.id, { enabled: !m.enabled })
      loadModules()
    } catch (err) { alert(err.message) }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        <RefreshCw className="w-5 h-5 animate-spin mr-2" /> Loading modules...
      </div>
    )
  }

  const modules = stats?.modules || []

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-500 uppercase tracking-wider font-semibold">Module Health Matrix ({modules.length})</span>
        <button onClick={() => { setLoading(true); loadModules() }}
          className="flex items-center gap-2 text-sm text-gray-400 hover:text-white">
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </div>

      <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-gray-500 uppercase tracking-wider border-b border-[#1e1e2e]">
              <th className="text-left px-5 py-3 w-8"></th>
              <th className="text-left px-5 py-3">Module</th>
              <th className="text-left px-5 py-3">Layer</th>
              <th className="text-left px-5 py-3">Status</th>
              <th className="text-left px-5 py-3">Health</th>
              <th className="text-right px-5 py-3">Findings</th>
              <th className="text-left px-5 py-3">Last Check</th>
            </tr>
          </thead>
          <tbody>
            {modules.map((m, i) => {
              const isExpanded = expandedModule === m.id
              return (
                <React.Fragment key={m.id}>
                  <tr
                    onClick={() => setExpandedModule(isExpanded ? null : m.id)}
                    className={`border-t border-[#1e1e2e] cursor-pointer hover:bg-white/[0.03] ${i % 2 === 1 ? 'bg-white/[0.02]' : ''}`}
                  >
                    <td className="px-5 py-3 text-gray-500">
                      {isExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                    </td>
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
                  {isExpanded && (
                    <tr className="border-t border-[#1e1e2e]/50">
                      <td colSpan={7} className="px-10 py-4 bg-[#0a0a0f]">
                        <div className="grid grid-cols-2 gap-6">
                          <div>
                            <p className="text-xs text-gray-500 mb-1">Description</p>
                            <p className="text-sm text-gray-300">{m.description || 'No description available'}</p>
                            <p className="text-xs text-gray-500 mt-3 mb-1">Category</p>
                            <p className="text-sm text-gray-300">{m.category || 'general'}</p>
                            <p className="text-xs text-gray-500 mt-3 mb-1">API Key Required</p>
                            <p className="text-sm text-gray-300">
                              {m.requires_key ? (
                                <span className="text-[#ffcc00]">Yes — {m.key_name || 'API key'}</span>
                              ) : (
                                <span className="text-[#00ff88]">No — free</span>
                              )}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500 mb-1">Statistics</p>
                            <p className="text-sm text-gray-300">Total findings: <span className="font-mono">{m.findings_count}</span></p>
                            <p className="text-sm text-gray-300">Success rate: <span className="font-mono">{m.success_rate || 'N/A'}</span></p>
                            <p className="text-sm text-gray-300">Avg response: <span className="font-mono">{m.avg_response_ms ? `${m.avg_response_ms}ms` : 'N/A'}</span></p>
                            <div className="mt-4">
                              <button
                                onClick={(e) => { e.stopPropagation(); handleToggle(m) }}
                                className={`text-xs px-3 py-1.5 rounded-lg font-medium ${
                                  m.enabled
                                    ? 'bg-[#ff2244]/15 text-[#ff2244] hover:bg-[#ff2244]/25'
                                    : 'bg-[#00ff88]/15 text-[#00ff88] hover:bg-[#00ff88]/25'
                                } transition-colors`}
                              >
                                {m.enabled ? 'Disable Module' : 'Enable Module'}
                              </button>
                            </div>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
