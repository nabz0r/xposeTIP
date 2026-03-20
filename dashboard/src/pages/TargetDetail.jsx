import React, { useEffect, useState, useCallback, useRef, Fragment } from 'react'
import { useParams } from 'react-router-dom'
import { Radar, ChevronDown, ChevronRight, ExternalLink, Lock, CheckCircle, Filter, Shield, AlertTriangle, Globe } from 'lucide-react'
import { getTarget, getFindings, getScans, createScan, getModules, getScan, getGraph, patchFinding } from '../lib/api'
import IdentityGraph from '../components/IdentityGraph'
import IOCTimeline from '../components/IOCTimeline'
import ProfileHeader from '../components/ProfileHeader'
import LocationMap from '../components/LocationMap'

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
  whois_lookup: '~10s', maxmind_geo: '~3s', geoip: '~10s',
  gravatar: '~3s', social_enricher: '~5s', google_profile: '~5s',
  emailrep: '~3s', epieos: '~5s', fullcontact: '~3s', github_deep: '~10s',
  username_hunter: '~30s', leaked_domains: '~5s', dns_deep: '~8s',
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
  const [activeTab, setActiveTab] = useState('overview')
  const [toast, setToast] = useState(null)
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
          // Auto-refresh findings, target, and score
          const [t, f] = await Promise.all([getTarget(id), getFindings(`target_id=${id}`)])
          setTarget(t)
          const newFindings = f.items || []
          const newCount = newFindings.length - findings.length
          setFindings(newFindings)
          // Show completion toast
          const failed = updated.filter(s => s.status === 'failed')
          if (failed.length > 0) {
            setToast({ type: 'error', message: `Scan failed: ${failed[0].error_log || 'Unknown error'}` })
          } else {
            setToast({ type: 'success', message: `Scan completed — ${newCount > 0 ? newCount : 0} new findings` })
          }
          setTimeout(() => setToast(null), 5000)
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
      // Pre-select all enabled+implemented Layer 1 + recommended Layer 2 modules
      const recommended = ['dns_deep', 'leaked_domains', 'geoip']
      setSelectedModules(m.filter(mod => mod.enabled && mod.implemented && (mod.layer === 1 || recommended.includes(mod.id))).map(mod => mod.id))
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

  if (!target) return (
    <div className="space-y-4">
      <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-6 animate-pulse">
        <div className="flex gap-6">
          <div className="w-20 h-20 rounded-full bg-[#1e1e2e]" />
          <div className="flex-1 space-y-3">
            <div className="h-5 w-48 bg-[#1e1e2e] rounded" />
            <div className="h-4 w-64 bg-[#1e1e2e] rounded" />
            <div className="h-3 w-32 bg-[#1e1e2e] rounded" />
          </div>
        </div>
      </div>
    </div>
  )

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

  // Overview data
  const breachFindings = findings.filter(f => f.category === 'breach')
  const socialFindings = findings.filter(f => f.category === 'social_account')
  const geoFindings = findings.filter(f => f.category === 'geolocation')
  const criticalCount = findings.filter(f => f.severity === 'critical' || f.severity === 'high').length

  return (
    <div className="space-y-6">
      {/* Profile Header */}
      <div className="flex items-start gap-4">
        <div className="flex-1">
          <ProfileHeader target={target} findings={findings} animScore={animScore} />
        </div>
        <button onClick={() => setShowScanModal(true)}
          className="shrink-0 flex items-center gap-2 bg-[#00ff88] text-black font-semibold rounded-lg px-4 py-2.5 text-sm hover:bg-[#00ff88]/90 mt-2">
          <Radar className="w-4 h-4" /> New Scan
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-[#1e1e2e]">
        {['overview', 'findings', 'graph', 'timeline', 'locations', 'scans'].map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm capitalize transition-colors ${activeTab === tab ? 'text-[#00ff88] border-b-2 border-[#00ff88]' : 'text-gray-400 hover:text-white'}`}>
            {tab} {tab === 'findings' ? `(${findings.length})` : tab === 'scans' ? `(${scans.length})` : ''}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-4">
          {/* Critical alerts */}
          {criticalCount > 0 && (
            <div className="bg-[#ff2244]/10 border border-[#ff2244]/30 rounded-xl p-4 flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-[#ff2244] shrink-0 mt-0.5" />
              <div>
                <h3 className="text-sm font-semibold text-[#ff2244]">{criticalCount} Critical/High findings</h3>
                <p className="text-xs text-gray-400 mt-1">This identity has severe exposure requiring immediate attention.</p>
              </div>
            </div>
          )}

          {/* Breach summary cards */}
          {breachFindings.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">Breaches ({breachFindings.length})</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {breachFindings.slice(0, 6).map(f => (
                  <div key={f.id} className="bg-[#12121a] border border-[#1e1e2e] rounded-lg p-3 hover:border-[#ff2244]/30 transition-colors">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="inline-block text-[10px] font-medium px-1.5 py-0.5 rounded-full"
                        style={{ backgroundColor: (severityColors[f.severity] || '#666688') + '26', color: severityColors[f.severity] }}>
                        {f.severity}
                      </span>
                      <span className="text-sm font-medium truncate">{f.title}</span>
                    </div>
                    <p className="text-xs text-gray-400 line-clamp-2">{f.description}</p>
                    {f.data?.DataClasses && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {f.data.DataClasses.slice(0, 4).map(dc => (
                          <span key={dc} className="text-[10px] px-1.5 py-0.5 rounded bg-[#ff2244]/10 text-[#ff8800]">{dc}</span>
                        ))}
                        {f.data.DataClasses.length > 4 && <span className="text-[10px] text-gray-500">+{f.data.DataClasses.length - 4}</span>}
                      </div>
                    )}
                  </div>
                ))}
              </div>
              {breachFindings.length > 6 && (
                <button onClick={() => setActiveTab('findings')} className="text-xs text-[#3388ff] hover:underline mt-2">
                  View all {breachFindings.length} breaches
                </button>
              )}
            </div>
          )}

          {/* Social accounts */}
          {socialFindings.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">Accounts ({socialFindings.length})</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {socialFindings.slice(0, 9).map(f => (
                  <div key={f.id} className="bg-[#12121a] border border-[#1e1e2e] rounded-lg p-3 hover:border-[#3388ff]/30 transition-colors">
                    <div className="flex items-center gap-2">
                      {f.data?.avatar_url && <img src={f.data.avatar_url} alt="" className="w-6 h-6 rounded-full" />}
                      <span className="text-sm font-medium truncate">{f.title}</span>
                    </div>
                    <p className="text-xs text-gray-400 mt-1 line-clamp-1">{f.description}</p>
                    {f.url && (
                      <a href={f.url} target="_blank" rel="noreferrer" className="text-[10px] text-[#3388ff] hover:underline mt-1 inline-flex items-center gap-1">
                        {f.url.replace(/https?:\/\//, '').substring(0, 40)} <ExternalLink className="w-2.5 h-2.5" />
                      </a>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Geo summary */}
          {geoFindings.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">Mail Server Locations</h3>
              <p className="text-[10px] text-gray-600 mb-2">These are mail server locations, not the user's physical location.</p>
              <div className="flex flex-wrap gap-2">
                {geoFindings.map(f => (
                  <span key={f.id} className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg bg-[#12121a] border border-[#1e1e2e]">
                    <Globe className="w-3 h-3 text-[#3388ff]" />
                    {f.data?.city}, {f.data?.country}
                    <span className="text-gray-500">({f.data?.ip})</span>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Empty state */}
          {findings.length === 0 && (
            <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-12 text-center">
              <Shield className="w-12 h-12 text-gray-600 mx-auto mb-3" />
              <h3 className="text-lg font-medium text-gray-300">No intelligence yet</h3>
              <p className="text-sm text-gray-500 mt-1 mb-4">Launch a scan to discover this identity's digital exposure.</p>
              <button onClick={() => setShowScanModal(true)}
                className="inline-flex items-center gap-2 bg-[#00ff88] text-black font-semibold rounded-lg px-6 py-2.5 text-sm hover:bg-[#00ff88]/90">
                <Radar className="w-4 h-4" /> Launch First Scan
              </button>
            </div>
          )}
        </div>
      )}

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
                            {/* Enriched data cards per scanner */}
                            {f.data && <FindingDataCard finding={f} />}
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

      {/* Locations Tab */}
      {activeTab === 'locations' && <LocationMap findings={findings} />}

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

      {/* Toast */}
      {toast && (
        <div className={`fixed bottom-6 right-6 z-50 px-4 py-3 rounded-lg text-sm shadow-lg border ${
          toast.type === 'success' ? 'bg-[#00ff88]/10 border-[#00ff88]/30 text-[#00ff88]' : 'bg-[#ff2244]/10 border-[#ff2244]/30 text-[#ff2244]'
        }`}>
          {toast.message}
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

function FindingDataCard({ finding }) {
  const d = finding.data || {}
  const mod = finding.module

  // Breach findings (HIBP, leaked_domains)
  if (finding.category === 'breach' && (d.Name || d.breach_name)) {
    const name = d.Name || d.breach_name
    const date = d.BreachDate || d.date || ''
    const dataClasses = d.DataClasses || d.data_classes || []
    const count = d.PwnCount || d.records || ''
    return (
      <div className="bg-[#12121a] rounded-lg p-3 border border-[#ff2244]/20">
        <div className="flex items-center gap-2 mb-2">
          <Shield className="w-4 h-4 text-[#ff2244]" />
          <span className="font-semibold text-sm">{name}</span>
          {date && <span className="text-xs text-gray-500">{date}</span>}
        </div>
        {count && <p className="text-xs text-gray-400 mb-2">{typeof count === 'number' ? count.toLocaleString() : count} records exposed</p>}
        {dataClasses.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {dataClasses.slice(0, 10).map(dc => (
              <span key={dc} className="text-[10px] px-1.5 py-0.5 rounded bg-[#ff2244]/10 text-[#ff8800]">{dc}</span>
            ))}
            {dataClasses.length > 10 && <span className="text-[10px] text-gray-500">+{dataClasses.length - 10}</span>}
          </div>
        )}
      </div>
    )
  }

  // Social account findings
  if (finding.category === 'social_account' && (d.platform || d.network || d.service)) {
    const platform = d.platform || d.network || d.service || ''
    const username = d.username || d.handle || d.login || ''
    const url = finding.url || d.url || ''
    return (
      <div className="bg-[#12121a] rounded-lg p-3 border border-[#3388ff]/20 flex items-center gap-3">
        {d.avatar_url && <img src={d.avatar_url} alt="" className="w-8 h-8 rounded-full" />}
        <div>
          <span className="text-sm font-medium">{platform}</span>
          {username && <span className="text-xs text-gray-400 ml-2">@{username}</span>}
          {url && <a href={url} target="_blank" rel="noreferrer" className="block text-[10px] text-[#3388ff] hover:underline mt-0.5">{url.replace(/https?:\/\//, '').substring(0, 50)}</a>}
        </div>
      </div>
    )
  }

  // EmailRep reputation
  if (mod === 'emailrep' && d.reputation) {
    const repColor = d.reputation === 'high' ? '#00ff88' : d.reputation === 'medium' ? '#ffcc00' : '#ff8800'
    return (
      <div className="bg-[#12121a] rounded-lg p-3 border border-[#1e1e2e] grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
        <div><span className="text-gray-500">Reputation</span><div className="font-mono font-semibold" style={{ color: repColor }}>{d.reputation}</div></div>
        <div><span className="text-gray-500">Suspicious</span><div className="font-mono">{d.suspicious ? 'Yes' : 'No'}</div></div>
        {d.first_seen && <div><span className="text-gray-500">First seen</span><div className="font-mono">{d.first_seen}</div></div>}
        {d.domain_age_days != null && <div><span className="text-gray-500">Domain age</span><div className="font-mono">{d.domain_age_days}d</div></div>}
      </div>
    )
  }

  // GitHub deep
  if (mod === 'github_deep' && d.login) {
    return (
      <div className="bg-[#12121a] rounded-lg p-3 border border-[#1e1e2e] flex items-start gap-3">
        {d.avatar_url && <img src={d.avatar_url} alt="" className="w-10 h-10 rounded-full" />}
        <div className="text-xs space-y-1">
          <div className="font-semibold text-sm">{d.name || d.login}</div>
          {d.bio && <p className="text-gray-400 line-clamp-2">{d.bio}</p>}
          <div className="flex gap-3 text-gray-500">
            {d.public_repos != null && <span>{d.public_repos} repos</span>}
            {d.followers != null && <span>{d.followers} followers</span>}
            {d.company && <span>{d.company}</span>}
            {d.location && <span>{d.location}</span>}
          </div>
        </div>
      </div>
    )
  }

  // DNS findings
  if (mod === 'dns_deep' && (d.spf_record !== undefined || d.security_score !== undefined)) {
    if (d.security_score !== undefined) {
      return (
        <div className="bg-[#12121a] rounded-lg p-3 border border-[#1e1e2e] grid grid-cols-3 gap-3 text-xs">
          <div><span className="text-gray-500">SPF</span><div className={d.has_spf ? 'text-[#00ff88]' : 'text-[#ff2244]'}>{d.has_spf ? 'Yes' : 'Missing'}</div></div>
          <div><span className="text-gray-500">DMARC</span><div className={d.has_dmarc ? 'text-[#00ff88]' : 'text-[#ff2244]'}>{d.has_dmarc ? 'Yes' : 'Missing'}</div></div>
          <div><span className="text-gray-500">DKIM</span><div className={d.has_dkim ? 'text-[#00ff88]' : 'text-[#ffcc00]'}>{d.has_dkim ? 'Yes' : 'Not found'}</div></div>
        </div>
      )
    }
  }

  // Geolocation
  if (finding.category === 'geolocation' && (d.lat || d.latitude)) {
    return (
      <div className="bg-[#12121a] rounded-lg p-3 border border-[#1e1e2e] grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
        {d.city && <div><span className="text-gray-500">City</span><div className="font-mono">{d.city}</div></div>}
        {d.country && <div><span className="text-gray-500">Country</span><div className="font-mono">{d.country}</div></div>}
        {d.isp && <div><span className="text-gray-500">ISP</span><div className="font-mono">{d.isp}</div></div>}
        {d.org && <div><span className="text-gray-500">Org</span><div className="font-mono">{d.org}</div></div>}
      </div>
    )
  }

  return null
}

