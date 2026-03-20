import React, { useEffect, useState, useCallback, useRef, Fragment } from 'react'
import { useParams } from 'react-router-dom'
import { Radar, ChevronDown, ChevronRight, ExternalLink, Lock, CheckCircle, Filter } from 'lucide-react'
import { getTarget, getFindings, getScans, createScan, getModules, getScan, getGraph, patchFinding } from '../lib/api'
import IdentityGraph from '../components/IdentityGraph'
import IOCTimeline from '../components/IOCTimeline'

const severityColors = {
  critical: '#ff2244', high: '#ff8800', medium: '#ffcc00', low: '#3388ff', info: '#666688',
}
const severityOrder = ['critical', 'high', 'medium', 'low', 'info']

const scoreColor = (score) => {
  if (score == null) return '#666688'
  if (score >= 61) return '#ff2244'
  if (score >= 31) return '#ff8800'
  return '#00ff88'
}

const SCAN_TIMES = {
  email_validator: '~5s', holehe: '~2min', hibp: '~5s', sherlock: '~60s',
  whois_lookup: '~10s', maxmind_geo: '~3s',
}

export default function TargetDetail() {
  const { id } = useParams()
  const [target, setTarget] = useState(null)
  const [findings, setFindings] = useState([])
  const [scans, setScans] = useState([])
  const [modules, setModules] = useState([])
  const [graphData, setGraphData] = useState(null)
  const [expanded, setExpanded] = useState(null)
  const [showScanModal, setShowScanModal] = useState(false)
  const [selectedModules, setSelectedModules] = useState([])
  const [scanning, setScanning] = useState(false)
  const [activeTab, setActiveTab] = useState('findings')
  // Filters
  const [sevFilter, setSevFilter] = useState('all')
  const [modFilter, setModFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')
  // Score animation
  const [animScore, setAnimScore] = useState(0)
  const pollRef = useRef(null)

  const load = useCallback(async () => {
    try {
      const [t, f, s] = await Promise.all([
        getTarget(id),
        getFindings(`target_id=${id}`),
        getScans(`target_id=${id}`),
      ])
      setTarget(t)
      setFindings(f.items || [])
      setScans(s.items || [])
    } catch {}
  }, [id])

  useEffect(() => { load() }, [load])

  // Animate score
  useEffect(() => {
    if (target?.exposure_score == null) return
    const targetScore = target.exposure_score
    let current = 0
    const step = Math.max(1, Math.ceil(targetScore / 30))
    const interval = setInterval(() => {
      current = Math.min(current + step, targetScore)
      setAnimScore(current)
      if (current >= targetScore) clearInterval(interval)
    }, 30)
    return () => clearInterval(interval)
  }, [target?.exposure_score])

  // Poll while scanning — poll individual scans every 3s
  useEffect(() => {
    const runningScans = scans.filter(s => s.status === 'running' || s.status === 'queued')
    if (!runningScans.length) {
      if (pollRef.current) clearInterval(pollRef.current)
      return
    }
    pollRef.current = setInterval(async () => {
      try {
        const updated = await Promise.all(runningScans.map(s => getScan(s.id)))
        const done = updated.every(s => s.status !== 'running' && s.status !== 'queued')
        setScans(prev => prev.map(s => {
          const u = updated.find(x => x.id === s.id)
          return u || s
        }))
        if (done) {
          clearInterval(pollRef.current)
          load() // Full refresh when complete
        }
      } catch {}
    }, 3000)
    return () => clearInterval(pollRef.current)
  }, [scans, load])

  // Load graph when switching to graph tab
  useEffect(() => {
    if (activeTab === 'graph') {
      getGraph(id).then(setGraphData).catch(() => {})
    }
  }, [activeTab, id])

  useEffect(() => {
    getModules().then(m => {
      setModules(m)
      setSelectedModules(m.filter(mod => mod.enabled && mod.implemented && mod.layer === 1).map(mod => mod.id))
    }).catch(() => {})
  }, [])

  async function handleScan() {
    if (selectedModules.length === 0) return
    setScanning(true)
    try {
      await createScan({ target_id: id, modules: selectedModules })
      setShowScanModal(false)
      load()
    } catch (err) {
      alert(err.message)
    } finally {
      setScanning(false)
    }
  }

  async function markResolved(findingId) {
    try {
      await patchFinding(findingId, { status: 'resolved' })
      setFindings(prev => prev.map(f => f.id === findingId ? { ...f, status: 'resolved' } : f))
    } catch (err) {
      alert(err.message)
    }
  }

  if (!target) return <div className="text-gray-500">Loading...</div>

  // Filtered findings
  const filteredFindings = findings.filter(f => {
    if (sevFilter !== 'all' && f.severity !== sevFilter) return false
    if (modFilter !== 'all' && f.module !== modFilter) return false
    if (statusFilter !== 'all' && f.status !== statusFilter) return false
    return true
  })

  const uniqueModules = [...new Set(findings.map(f => f.module))]

  // Module groups for selector
  const implementedModules = modules.filter(m => m.enabled && m.implemented)
  const layers = [...new Set(implementedModules.map(m => m.layer))].sort()

  const breakdown = target.score_breakdown || {}

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-mono font-bold">{target.email}</h1>
          <div className="flex items-center gap-4 mt-2 text-sm text-gray-400">
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium"
              style={{ backgroundColor: (target.status === 'completed' ? '#00ff88' : target.status === 'scanning' ? '#ffcc00' : '#666688') + '26',
                       color: target.status === 'completed' ? '#00ff88' : target.status === 'scanning' ? '#ffcc00' : '#666688' }}>
              {target.status}
            </span>
            {target.country_code && <span>{target.country_code}</span>}
            {target.last_scanned && <span>Last scanned: {new Date(target.last_scanned).toLocaleString()}</span>}
          </div>
        </div>
        <div className="flex items-center gap-4">
          {/* Score donut */}
          <div className="flex flex-col items-center gap-1">
            <div className="relative w-20 h-20">
              <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
                <circle cx="18" cy="18" r="15.5" fill="none" stroke="#1e1e2e" strokeWidth="3" />
                <circle cx="18" cy="18" r="15.5" fill="none"
                  stroke={scoreColor(target.exposure_score)}
                  strokeWidth="3"
                  strokeDasharray={`${animScore} 100`}
                  strokeLinecap="round"
                  style={{ transition: 'stroke-dasharray 0.3s ease' }} />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-lg font-mono font-bold" style={{ color: scoreColor(target.exposure_score) }}>
                  {target.exposure_score ?? '-'}
                </span>
              </div>
            </div>
          </div>
          <button onClick={() => setShowScanModal(true)}
            className="flex items-center gap-2 bg-[#00ff88] text-black font-semibold rounded-lg px-4 py-2 text-sm hover:bg-[#00ff88]/90">
            <Radar className="w-4 h-4" /> New Scan
          </button>
        </div>
      </div>

      {/* Score breakdown */}
      {Object.keys(breakdown).length > 0 && (
        <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-4">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">Score Breakdown</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {Object.entries(breakdown).sort((a, b) => b[1] - a[1]).map(([cat, score]) => (
              <div key={cat} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-gray-400">{cat.replace(/_/g, ' ')}</span>
                  <span className="font-mono text-gray-300">{score}</span>
                </div>
                <div className="h-1.5 bg-[#1e1e2e] rounded-full overflow-hidden">
                  <div className="h-full rounded-full transition-all duration-500"
                    style={{ width: `${score}%`, backgroundColor: score >= 60 ? '#ff2244' : score >= 30 ? '#ff8800' : '#00ff88' }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 border-b border-[#1e1e2e]">
        {['findings', 'graph', 'timeline', 'scans'].map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm capitalize transition-colors ${activeTab === tab ? 'text-[#00ff88] border-b-2 border-[#00ff88]' : 'text-gray-400 hover:text-white'}`}>
            {tab} {tab === 'findings' ? `(${findings.length})` : tab === 'scans' ? `(${scans.length})` : ''}
          </button>
        ))}
      </div>

      {/* Findings Tab */}
      {activeTab === 'findings' && (
        <div>
          {/* Filters */}
          <div className="flex gap-3 mb-4">
            <select value={sevFilter} onChange={e => setSevFilter(e.target.value)}
              className="bg-[#12121a] border border-[#1e1e2e] rounded-lg px-3 py-1.5 text-xs text-gray-300 focus:outline-none focus:border-[#00ff88]/50">
              <option value="all">All severities</option>
              {severityOrder.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
            <select value={modFilter} onChange={e => setModFilter(e.target.value)}
              className="bg-[#12121a] border border-[#1e1e2e] rounded-lg px-3 py-1.5 text-xs text-gray-300 focus:outline-none focus:border-[#00ff88]/50">
              <option value="all">All modules</option>
              {uniqueModules.map(m => <option key={m} value={m}>{m}</option>)}
            </select>
            <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}
              className="bg-[#12121a] border border-[#1e1e2e] rounded-lg px-3 py-1.5 text-xs text-gray-300 focus:outline-none focus:border-[#00ff88]/50">
              <option value="all">All statuses</option>
              <option value="active">Active</option>
              <option value="resolved">Resolved</option>
              <option value="false_positive">False positive</option>
            </select>
          </div>

          <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs text-gray-500 uppercase tracking-wider border-b border-[#1e1e2e]">
                  <th className="w-8"></th>
                  <th className="text-left px-4 py-3">Severity</th>
                  <th className="text-left px-4 py-3">Module</th>
                  <th className="text-left px-4 py-3">Title</th>
                  <th className="text-left px-4 py-3">Category</th>
                  <th className="text-left px-4 py-3">Status</th>
                  <th className="text-left px-4 py-3">Date</th>
                </tr>
              </thead>
              <tbody>
                {filteredFindings.map((f, i) => (
                  <Fragment key={f.id}>
                    <tr
                      onClick={() => setExpanded(expanded === f.id ? null : f.id)}
                      className={`border-t border-[#1e1e2e] cursor-pointer hover:bg-white/[0.03] ${i % 2 === 1 ? 'bg-white/[0.02]' : ''}`}>
                      <td className="px-2 text-gray-500">
                        {expanded === f.id ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                      </td>
                      <td className="px-4 py-3">
                        <span className="inline-block text-xs font-medium px-2 py-0.5 rounded-full"
                          style={{ backgroundColor: (severityColors[f.severity] || '#666688') + '26', color: severityColors[f.severity] || '#666688' }}>
                          {f.severity}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-gray-400">{f.module}</td>
                      <td className="px-4 py-3">{f.title}</td>
                      <td className="px-4 py-3 text-gray-400 text-xs">{f.category}</td>
                      <td className="px-4 py-3">
                        <span className={`text-xs ${f.status === 'resolved' ? 'text-[#00ff88]' : f.status === 'false_positive' ? 'text-gray-500' : 'text-gray-400'}`}>
                          {f.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-400 text-xs">{f.first_seen ? new Date(f.first_seen).toLocaleDateString() : '-'}</td>
                    </tr>
                    {expanded === f.id && (
                      <tr className="bg-[#0a0a0f]">
                        <td colSpan={7} className="px-6 py-4">
                          <div className="space-y-3">
                            <p className="text-sm text-gray-300">{f.description}</p>
                            <div className="flex items-center gap-4 text-xs text-gray-400">
                              {f.indicator_value && <span><span className="text-gray-500">Indicator:</span> <span className="font-mono">{f.indicator_value}</span></span>}
                              {f.url && <a href={f.url} target="_blank" rel="noreferrer" className="text-[#3388ff] hover:underline inline-flex items-center gap-1">
                                Open link <ExternalLink className="w-3 h-3" />
                              </a>}
                            </div>
                            {f.data && (
                              <details className="text-xs">
                                <summary className="text-gray-500 cursor-pointer hover:text-gray-300">Raw data</summary>
                                <pre className="font-mono text-gray-400 bg-[#12121a] rounded-lg p-3 overflow-x-auto max-h-60 mt-2">
                                  {JSON.stringify(f.data, null, 2)}
                                </pre>
                              </details>
                            )}
                            {f.status === 'active' && (
                              <button onClick={(e) => { e.stopPropagation(); markResolved(f.id) }}
                                className="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-[#00ff88]/10 text-[#00ff88] hover:bg-[#00ff88]/20 transition-colors">
                                <CheckCircle className="w-3 h-3" /> Mark as resolved
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                ))}
                {filteredFindings.length === 0 && (
                  <tr><td colSpan={7} className="px-5 py-8 text-center text-gray-500">
                    {findings.length === 0 ? 'No findings yet. Launch a scan to discover exposure.' : 'No findings match the current filters.'}
                  </td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Graph Tab */}
      {activeTab === 'graph' && <IdentityGraph data={graphData} />}

      {/* Timeline Tab */}
      {activeTab === 'timeline' && <IOCTimeline findings={findings} />}

      {/* Scans Tab */}
      {activeTab === 'scans' && (
        <div className="space-y-3">
          {scans.map(scan => (
            <div key={scan.id} className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <span className="inline-flex items-center gap-1.5 text-xs font-medium px-2 py-0.5 rounded-full"
                    style={{ backgroundColor: (scan.status === 'completed' ? '#00ff88' : scan.status === 'running' ? '#ffcc00' : scan.status === 'failed' ? '#ff2244' : '#666688') + '26',
                             color: scan.status === 'completed' ? '#00ff88' : scan.status === 'running' ? '#ffcc00' : scan.status === 'failed' ? '#ff2244' : '#666688' }}>
                    {scan.status}
                  </span>
                  <span className="text-xs text-gray-400">{scan.created_at ? new Date(scan.created_at).toLocaleString() : ''}</span>
                </div>
                <div className="text-xs text-gray-400">
                  {scan.findings_count} findings {scan.duration_ms ? `| ${(scan.duration_ms / 1000).toFixed(1)}s` : ''}
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
          ))}
          {scans.length === 0 && <div className="text-center py-8 text-gray-500">No scans yet</div>}
        </div>
      )}

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
    </div>
  )
}

