import React from 'react'
import { Radar, Lock, CheckCircle, XCircle } from 'lucide-react'
import { getLogs, cancelScan } from '../../lib/api'

const SCAN_TIMES = {
  email_validator: '~5s', holehe: '~2min', hibp: '~5s', sherlock: '~60s',
  whois_lookup: '~10s', maxmind_geo: '~3s', geoip: '~10s',
  gravatar: '~3s', social_enricher: '~5s', google_profile: '~5s',
  emailrep: '~3s', epieos: '~5s', fullcontact: '~3s', github_deep: '~10s',
  username_hunter: '~30s', leaked_domains: '~5s', dns_deep: '~8s',
  virustotal: '~10s', shodan: '~15s', intelx: '~15s', hunter: '~10s', dehashed: '~8s',
  reverse_image: '~15s', google_audit: '~10s', microsoft_audit: '~10s',
}

export default function ScansTab({ scans, modules, load, showScanModal, setShowScanModal, selectedModules, setSelectedModules, scanning, handleScan }) {
  const implementedModules = modules.filter(m => m.enabled && m.implemented)
  const layers = [...new Set(implementedModules.map(m => m.layer))].sort()

  return (
    <>
      <div className="space-y-3">
        {scans.map(scan => {
          const startedAt = scan.created_at ? new Date(scan.created_at) : null
          const completedAt = scan.completed_at ? new Date(scan.completed_at) : null
          const durationMs = scan.duration_ms || (startedAt && completedAt ? completedAt - startedAt : null)
          const formatDuration = (ms) => {
            if (!ms) return '-'
            const secs = Math.floor(ms / 1000)
            if (secs < 60) return `${secs}s`
            return `${Math.floor(secs / 60)}m ${secs % 60}s`
          }
          const moduleCount = Object.keys(scan.module_progress || {}).length || (scan.modules || []).length
          const scanStatusColor = scan.status === 'completed' ? '#00ff88' : scan.status === 'running' ? '#ffcc00' : scan.status === 'failed' ? '#ff2244' : '#666688'
          return (
            <div key={scan.id} className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <span className="inline-flex items-center gap-1.5 text-xs font-medium px-2 py-0.5 rounded-full"
                    style={{ backgroundColor: scanStatusColor + '26', color: scanStatusColor }}>
                    {scan.status}
                  </span>
                  <span className="text-xs text-gray-400">
                    {startedAt ? startedAt.toLocaleString() : ''}
                    {completedAt ? ` → ${completedAt.toLocaleTimeString()}` : ''}
                  </span>
                </div>
                <div className="flex items-center gap-3 text-xs text-gray-400">
                  <span className="font-mono">{moduleCount} modules</span>
                  <span className="font-mono">{scan.findings_count} findings</span>
                  <span className="font-mono">{formatDuration(durationMs)}</span>
                  <button
                    onClick={async (e) => {
                      e.stopPropagation()
                      try {
                        const data = await getLogs(`scan_id=${scan.id}&limit=500`)
                        const blob = new Blob([JSON.stringify(data.logs || [], null, 2)], { type: 'application/json' })
                        const url = URL.createObjectURL(blob)
                        const a = document.createElement('a')
                        a.href = url
                        a.download = `scan-${scan.id.slice(0, 8)}-logs.json`
                        a.click()
                        URL.revokeObjectURL(url)
                      } catch { alert('No logs available for this scan') }
                    }}
                    className="text-[10px] text-gray-400 hover:text-[#3388ff]"
                    title="Download scan logs"
                  >
                    Download Logs
                  </button>
                  {(scan.status === 'running' || scan.status === 'queued') && (
                    <button
                      onClick={async (e) => {
                        e.stopPropagation()
                        if (window.confirm('Cancel this scan?')) {
                          try { await cancelScan(scan.id); load() } catch (err) { console.error('Failed to cancel:', err) }
                        }
                      }}
                      className="text-xs px-2 py-1 rounded bg-[#ff2244]/10 text-[#ff2244] hover:bg-[#ff2244]/20 transition-colors"
                    >
                      Cancel
                    </button>
                  )}
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                {Object.entries(scan.module_progress || {}).map(([mod, status]) => (
                  <span key={mod} className="text-xs font-mono px-2 py-1 rounded bg-[#0a0a0f] border border-[#1e1e2e]">
                    {mod}: <span style={{ color: status === 'completed' ? '#00ff88' : status === 'running' ? '#ffcc00' : status === 'failed' ? '#ff2244' : status === 'skipped' ? '#666688' : '#666688' }}>{status}</span>
                  </span>
                ))}
              </div>
            </div>
          )
        })}
        {scans.length === 0 && <div className="text-center py-8 text-gray-500">No scans yet</div>}
      </div>

      {/* Scan Modal */}
      {showScanModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={() => setShowScanModal(false)}>
          <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
            <h2 className="text-lg font-semibold mb-4">Launch Scan</h2>
            <div className="space-y-4 mb-4 max-h-80 overflow-y-auto">
              {layers.map(layer => {
                const layerModules = implementedModules.filter(m => m.layer === layer)
                return (
                  <div key={layer}>
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500">Layer {layer}</h3>
                      <button
                        onClick={() => {
                          const layerIds = layerModules.map(m => m.id)
                          const allSelected = layerIds.every(id => selectedModules.includes(id))
                          if (allSelected) {
                            setSelectedModules(selectedModules.filter(id => !layerIds.includes(id)))
                          } else {
                            setSelectedModules([...new Set([...selectedModules, ...layerIds])])
                          }
                        }}
                        className="text-xs text-[#00ff88] hover:underline">
                        {layerModules.every(m => selectedModules.includes(m.id)) ? 'Deselect all' : 'Select all'}
                      </button>
                    </div>
                    <div className="space-y-1">
                      {layerModules.map(mod => (
                        <label key={mod.id} className="flex items-center gap-3 p-2 rounded-lg hover:bg-white/5 cursor-pointer">
                          <input type="checkbox" checked={selectedModules.includes(mod.id)}
                            onChange={(e) => {
                              if (e.target.checked) setSelectedModules([...selectedModules, mod.id])
                              else setSelectedModules(selectedModules.filter(m => m !== mod.id))
                            }}
                            className="accent-[#00ff88]" />
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <span className="text-sm">{mod.display_name}</span>
                              {mod.requires_auth && (
                                <span className="inline-flex items-center gap-1 text-xs px-1.5 py-0.5 rounded bg-[#ff8800]/10 text-[#ff8800]">
                                  <Lock className="w-3 h-3" /> Auth
                                </span>
                              )}
                            </div>
                            <div className="text-xs text-gray-500 flex items-center gap-2">
                              <span>{mod.category}</span>
                              {SCAN_TIMES[mod.id] && <span className="text-gray-600">{SCAN_TIMES[mod.id]}</span>}
                            </div>
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>
                )
              })}
            </div>
            <div className="flex gap-3 justify-end">
              <button onClick={() => setShowScanModal(false)} className="px-4 py-2 text-sm text-gray-400 hover:text-white">Cancel</button>
              <button onClick={handleScan} disabled={scanning || selectedModules.length === 0}
                className="bg-[#00ff88] text-black font-semibold rounded-lg px-6 py-2 text-sm hover:bg-[#00ff88]/90 disabled:opacity-50">
                {scanning ? 'Launching...' : `Scan (${selectedModules.length} modules)`}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
