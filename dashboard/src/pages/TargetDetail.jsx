import { useEffect, useState, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { Radar, ChevronDown, ChevronRight, ExternalLink } from 'lucide-react'
import { getTarget, getFindings, getScans, createScan, getModules } from '../lib/api'

const severityColors = {
  critical: '#ff2244', high: '#ff8800', medium: '#ffcc00', low: '#3388ff', info: '#666688',
}

const scoreColor = (score) => {
  if (score == null) return '#666688'
  if (score >= 80) return '#ff2244'
  if (score >= 60) return '#ff8800'
  if (score >= 40) return '#ffcc00'
  if (score >= 20) return '#3388ff'
  return '#00ff88'
}

export default function TargetDetail() {
  const { id } = useParams()
  const [target, setTarget] = useState(null)
  const [findings, setFindings] = useState([])
  const [scans, setScans] = useState([])
  const [modules, setModules] = useState([])
  const [expanded, setExpanded] = useState(null)
  const [showScanModal, setShowScanModal] = useState(false)
  const [selectedModules, setSelectedModules] = useState([])
  const [scanning, setScanning] = useState(false)
  const [activeTab, setActiveTab] = useState('findings')

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

  // Poll while scanning
  useEffect(() => {
    const running = scans.some(s => s.status === 'running' || s.status === 'queued')
    if (!running) return
    const interval = setInterval(load, 2000)
    return () => clearInterval(interval)
  }, [scans, load])

  useEffect(() => {
    getModules().then(m => {
      setModules(m.filter(mod => mod.enabled))
      setSelectedModules(m.filter(mod => mod.enabled && mod.layer === 1).map(mod => mod.id))
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

  if (!target) return <div className="text-gray-500">Loading...</div>

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
        <div className="flex items-center gap-3">
          {/* Score donut */}
          <div className="relative w-16 h-16">
            <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
              <circle cx="18" cy="18" r="15.5" fill="none" stroke="#1e1e2e" strokeWidth="3" />
              <circle cx="18" cy="18" r="15.5" fill="none"
                stroke={scoreColor(target.exposure_score)}
                strokeWidth="3"
                strokeDasharray={`${(target.exposure_score || 0)} 100`}
                strokeLinecap="round" />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-sm font-mono font-bold" style={{ color: scoreColor(target.exposure_score) }}>
                {target.exposure_score ?? '-'}
              </span>
            </div>
          </div>
          <button onClick={() => setShowScanModal(true)}
            className="flex items-center gap-2 bg-[#00ff88] text-black font-semibold rounded-lg px-4 py-2 text-sm hover:bg-[#00ff88]/90">
            <Radar className="w-4 h-4" /> New Scan
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-[#1e1e2e]">
        {['findings', 'scans'].map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm capitalize transition-colors ${activeTab === tab ? 'text-[#00ff88] border-b-2 border-[#00ff88]' : 'text-gray-400 hover:text-white'}`}>
            {tab} {tab === 'findings' ? `(${findings.length})` : `(${scans.length})`}
          </button>
        ))}
      </div>

      {/* Findings Tab */}
      {activeTab === 'findings' && (
        <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-gray-500 uppercase tracking-wider border-b border-[#1e1e2e]">
                <th className="w-8"></th>
                <th className="text-left px-4 py-3">Severity</th>
                <th className="text-left px-4 py-3">Module</th>
                <th className="text-left px-4 py-3">Title</th>
                <th className="text-left px-4 py-3">Category</th>
                <th className="text-left px-4 py-3">URL</th>
                <th className="text-left px-4 py-3">Date</th>
              </tr>
            </thead>
            <tbody>
              {findings.map((f, i) => (
                <>
                  <tr key={f.id}
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
                      {f.url && <a href={f.url} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()} className="text-[#3388ff] hover:underline inline-flex items-center gap-1 text-xs">
                        Link <ExternalLink className="w-3 h-3" />
                      </a>}
                    </td>
                    <td className="px-4 py-3 text-gray-400 text-xs">{f.first_seen ? new Date(f.first_seen).toLocaleDateString() : '-'}</td>
                  </tr>
                  {expanded === f.id && (
                    <tr key={f.id + '-detail'} className="bg-[#0a0a0f]">
                      <td colSpan={7} className="px-6 py-4">
                        <p className="text-sm text-gray-300 mb-3">{f.description}</p>
                        {f.data && (
                          <pre className="text-xs font-mono text-gray-400 bg-[#12121a] rounded-lg p-3 overflow-x-auto max-h-60">
                            {JSON.stringify(f.data, null, 2)}
                          </pre>
                        )}
                      </td>
                    </tr>
                  )}
                </>
              ))}
              {findings.length === 0 && (
                <tr><td colSpan={7} className="px-5 py-8 text-center text-gray-500">No findings yet. Launch a scan to discover exposure.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Scans Tab */}
      {activeTab === 'scans' && (
        <div className="space-y-3">
          {scans.map(scan => (
            <div key={scan.id} className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <span className="inline-flex items-center gap-1.5 text-xs font-medium px-2 py-0.5 rounded-full"
                    style={{ backgroundColor: (scan.status === 'completed' ? '#00ff88' : scan.status === 'running' ? '#ffcc00' : '#666688') + '26',
                             color: scan.status === 'completed' ? '#00ff88' : scan.status === 'running' ? '#ffcc00' : '#666688' }}>
                    {scan.status}
                  </span>
                  <span className="text-xs text-gray-400">{scan.created_at ? new Date(scan.created_at).toLocaleString() : ''}</span>
                </div>
                <div className="text-xs text-gray-400">
                  {scan.findings_count} findings {scan.duration_ms ? `| ${(scan.duration_ms / 1000).toFixed(1)}s` : ''}
                </div>
              </div>
              {/* Module progress */}
              <div className="flex flex-wrap gap-2">
                {Object.entries(scan.module_progress || {}).map(([mod, status]) => (
                  <span key={mod} className="text-xs font-mono px-2 py-1 rounded bg-[#0a0a0f] border border-[#1e1e2e]">
                    {mod}: <span style={{ color: status === 'completed' ? '#00ff88' : status === 'running' ? '#ffcc00' : status === 'failed' ? '#ff2244' : '#666688' }}>{status}</span>
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
            <div className="space-y-2 mb-4 max-h-60 overflow-y-auto">
              {modules.map(mod => (
                <label key={mod.id} className="flex items-center gap-3 p-2 rounded-lg hover:bg-white/5 cursor-pointer">
                  <input type="checkbox" checked={selectedModules.includes(mod.id)}
                    onChange={(e) => {
                      if (e.target.checked) setSelectedModules([...selectedModules, mod.id])
                      else setSelectedModules(selectedModules.filter(m => m !== mod.id))
                    }}
                    className="accent-[#00ff88]" />
                  <div>
                    <div className="text-sm">{mod.display_name}</div>
                    <div className="text-xs text-gray-500">Layer {mod.layer} | {mod.category}</div>
                  </div>
                </label>
              ))}
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
