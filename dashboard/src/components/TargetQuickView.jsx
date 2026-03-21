import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { X, ExternalLink, Shield, Radar, AlertTriangle } from 'lucide-react'
import { getTarget, getFindings, getScans, getFingerprint } from '../lib/api'
import FingerprintRadar from './FingerprintRadar'

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

function ScoreDonut({ score, size = 80 }) {
  const r = (size - 8) / 2
  const c = 2 * Math.PI * r
  const pct = score != null ? score / 100 : 0
  const color = scoreColor(score)

  return (
    <svg width={size} height={size} className="block">
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#1e1e2e" strokeWidth={6} />
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color} strokeWidth={6}
        strokeDasharray={c} strokeDashoffset={c * (1 - pct)}
        strokeLinecap="round" transform={`rotate(-90 ${size / 2} ${size / 2})`}
        className="transition-all duration-700" />
      <text x={size / 2} y={size / 2} textAnchor="middle" dominantBaseline="central"
        fill={color} fontSize={size * 0.28} fontWeight="bold" fontFamily="monospace">
        {score != null ? score : '-'}
      </text>
    </svg>
  )
}

export default function TargetQuickView({ targetId, onClose }) {
  const [target, setTarget] = useState(null)
  const [findings, setFindings] = useState([])
  const [lastScan, setLastScan] = useState(null)
  const [identityStats, setIdentityStats] = useState({})
  const [fp, setFp] = useState(null)
  const navigate = useNavigate()

  const sevOrder = { critical: 0, high: 1, medium: 2, low: 3, info: 4 }

  useEffect(() => {
    if (!targetId) return
    loadData()
  }, [targetId])

  async function loadData() {
    try {
      const [t, f, s] = await Promise.all([
        getTarget(targetId),
        getFindings(`target_id=${targetId}&per_page=50`),
        getScans(`target_id=${targetId}`),
      ])
      setTarget(t)
      // Sort by severity: critical → high → medium → low → info, show top 5
      const sorted = (f.items || []).sort((a, b) => (sevOrder[a.severity] ?? 5) - (sevOrder[b.severity] ?? 5))
      setFindings(sorted.slice(0, 5))

      const scans = s.items || []
      if (scans.length > 0) {
        setLastScan(scans[0])
      }

      // Load fingerprint
      getFingerprint(targetId).then(setFp).catch(() => {})

      // Compute identity stats from findings
      const allFindings = f.items || []
      const categories = {}
      allFindings.forEach(fi => {
        categories[fi.category] = (categories[fi.category] || 0) + 1
      })
      setIdentityStats(categories)
    } catch {}
  }

  if (!targetId) return null

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/50 z-40" onClick={onClose} />

      {/* Panel */}
      <div className="fixed right-0 top-0 h-full w-[400px] bg-[#0a0a0f] border-l border-[#1e1e2e] z-50 overflow-auto animate-slide-in">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-[#1e1e2e]">
          <h2 className="text-sm font-semibold text-gray-300">Target Quick View</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        {!target ? (
          <div className="p-5 text-center text-gray-500">Loading...</div>
        ) : (
          <div className="p-5 space-y-5">
            {/* Fingerprint */}
            {fp && (
              <div className="flex justify-center">
                <FingerprintRadar fingerprint={fp} size="small" animate={true} />
              </div>
            )}

            {/* Email + Score */}
            <div className="flex items-center gap-4">
              {!fp && <ScoreDonut score={target.exposure_score} />}
              <div className="flex-1 min-w-0">
                <div className="font-mono text-sm truncate">{target.email}</div>
                <div className="text-xs text-gray-500 mt-1">
                  {target.country_code || 'Unknown region'} · {target.status}
                </div>
                {target.last_scanned && (
                  <div className="text-xs text-gray-600 mt-0.5">
                    Last scan: {new Date(target.last_scanned).toLocaleDateString()}
                  </div>
                )}
              </div>
            </div>

            {/* Score Breakdown */}
            {target.score_breakdown && Object.keys(target.score_breakdown).length > 0 && (
              <div className="bg-[#12121a] border border-[#1e1e2e] rounded-lg p-3">
                <div className="text-xs text-gray-400 mb-2 uppercase tracking-wider">Score Breakdown</div>
                <div className="space-y-1.5">
                  {Object.entries(target.score_breakdown)
                    .sort(([, a], [, b]) => b - a)
                    .slice(0, 5)
                    .map(([cat, val]) => (
                      <div key={cat} className="flex items-center gap-2">
                        <span className="text-xs text-gray-500 w-28 truncate">{cat}</span>
                        <div className="flex-1 h-1.5 bg-[#1e1e2e] rounded-full overflow-hidden">
                          <div className="h-full rounded-full bg-[#00ff88]/60" style={{ width: `${Math.min(val, 100)}%` }} />
                        </div>
                        <span className="text-xs font-mono text-gray-400 w-8 text-right">{Math.round(val)}</span>
                      </div>
                    ))}
                </div>
              </div>
            )}

            {/* Top Findings */}
            <div>
              <div className="text-xs text-gray-400 mb-2 uppercase tracking-wider flex items-center gap-1.5">
                <AlertTriangle className="w-3 h-3" /> Most Severe Findings
              </div>
              {findings.length === 0 ? (
                <div className="text-xs text-gray-600">No findings yet</div>
              ) : (
                <div className="space-y-1.5">
                  {findings.map(f => (
                    <div key={f.id} className="bg-[#12121a] border border-[#1e1e2e] rounded-lg px-3 py-2 flex items-start gap-2">
                      <span className="w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0"
                        style={{ backgroundColor: severityColors[f.severity] || '#666688' }} />
                      <div className="min-w-0 flex-1">
                        <div className="text-xs truncate">{f.title}</div>
                        <div className="text-[10px] text-gray-600">{f.module} · {f.severity}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Identity Stats */}
            {Object.keys(identityStats).length > 0 && (
              <div>
                <div className="text-xs text-gray-400 mb-2 uppercase tracking-wider flex items-center gap-1.5">
                  <Shield className="w-3 h-3" /> Identity Categories
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {Object.entries(identityStats).map(([cat, count]) => (
                    <span key={cat} className="text-[10px] bg-[#12121a] border border-[#1e1e2e] rounded-full px-2 py-0.5 text-gray-400">
                      {cat} <span className="font-mono text-white">{count}</span>
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Last Scan */}
            {lastScan && (
              <div>
                <div className="text-xs text-gray-400 mb-2 uppercase tracking-wider flex items-center gap-1.5">
                  <Radar className="w-3 h-3" /> Last Scan
                </div>
                <div className="bg-[#12121a] border border-[#1e1e2e] rounded-lg px-3 py-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Status</span>
                    <span style={{ color: lastScan.status === 'completed' ? '#00ff88' : '#ffcc00' }}>
                      {lastScan.status}
                    </span>
                  </div>
                  <div className="flex justify-between mt-1">
                    <span className="text-gray-500">Modules</span>
                    <span className="font-mono text-gray-400">{(lastScan.modules || []).length}</span>
                  </div>
                  <div className="flex justify-between mt-1">
                    <span className="text-gray-500">Findings</span>
                    <span className="font-mono">{lastScan.findings_count || 0}</span>
                  </div>
                  {lastScan.duration_ms && (
                    <div className="flex justify-between mt-1">
                      <span className="text-gray-500">Duration</span>
                      <span className="font-mono text-gray-400">{(lastScan.duration_ms / 1000).toFixed(1)}s</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-2 pt-2">
              <button
                onClick={() => { onClose(); navigate(`/targets/${targetId}`) }}
                className="flex-1 flex items-center justify-center gap-2 bg-[#00ff88] text-black font-semibold rounded-lg px-4 py-2.5 text-sm hover:bg-[#00ff88]/90"
              >
                <ExternalLink className="w-4 h-4" /> View Details
              </button>
            </div>
          </div>
        )}
      </div>
    </>
  )
}
