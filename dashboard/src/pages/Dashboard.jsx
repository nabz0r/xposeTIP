import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Crosshair, Radar, AlertTriangle, ShieldAlert, Search } from 'lucide-react'
import { getTargets, getScans, getFindingsStats, getFindings, createTarget, createScan, getDefaults, getFingerprint, cancelScan } from '../lib/api'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, AreaChart, Area } from 'recharts'
import WorldHeatmap from '../components/WorldHeatmap'
import FingerprintRadar from '../components/FingerprintRadar'
import useSSE from '../hooks/useSSE'

const severityColors = {
  critical: '#ff2244', high: '#ff8800', medium: '#ffcc00', low: '#3388ff', info: '#666688',
}

function StatCard({ icon: Icon, label, value, color }) {
  return (
    <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5 hover:shadow-[0_0_20px_rgba(0,255,136,0.05)] transition-shadow">
      <div className="flex items-center gap-3 mb-3">
        <Icon className="w-5 h-5" style={{ color }} />
        <span className="text-xs text-gray-400 uppercase tracking-wider">{label}</span>
      </div>
      <div className="text-3xl font-bold font-mono">{value}</div>
    </div>
  )
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-[#12121a] border border-[#1e1e2e] rounded-lg px-3 py-2 text-xs">
      <div className="text-gray-400">{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color }} className="font-mono">{p.value}</div>
      ))}
    </div>
  )
}

export default function Dashboard() {
  const [stats, setStats] = useState({ targets: 0, scans: 0, findings: 0, critical: 0, high: 0 })
  const [recentScans, setRecentScans] = useState([])
  const [severityData, setSeverityData] = useState([])
  const [moduleData, setModuleData] = useState([])
  const [geoFindings, setGeoFindings] = useState([])
  const [topTarget, setTopTarget] = useState(null)
  const [topTargets, setTopTargets] = useState([])
  const [topFingerprint, setTopFingerprint] = useState(null)
  const [quickEmail, setQuickEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [defaultModules, setDefaultModules] = useState(['email_validator', 'holehe', 'emailrep', 'gravatar', 'epieos', 'github_deep', 'dns_deep'])
  const navigate = useNavigate()

  useEffect(() => { loadData(); loadDefaults() }, [])
  useSSE({ 'scan.completed': () => loadData(), 'target.updated': () => loadData() })

  async function loadDefaults() {
    try {
      const defs = await getDefaults()
      if (defs.default_modules?.length) setDefaultModules(defs.default_modules)
    } catch {}
  }

  async function loadData() {
    try {
      const [targetsData, scansData, findingsData] = await Promise.all([
        getTargets(),
        getScans(),
        getFindingsStats(),
      ])

      const bySev = findingsData.by_severity || {}
      const byMod = findingsData.by_module || {}

      setStats({
        targets: targetsData.total || 0,
        scans: scansData.items?.length || 0,
        findings: Object.values(bySev).reduce((a, b) => a + b, 0),
        critical: bySev.critical || 0,
        high: bySev.high || 0,
      })

      // Find most exposed targets
      const sortedTargets = (targetsData.items || []).filter(t => t.exposure_score != null).sort((a, b) => (b.exposure_score + (b.threat_score || 0)) - (a.exposure_score + (a.threat_score || 0)))
      if (sortedTargets.length > 0) {
        setTopTarget(sortedTargets[0])
        setTopTargets(sortedTargets.slice(0, 5))
        getFingerprint(sortedTargets[0].id).then(setTopFingerprint).catch(() => {})
      }
      setRecentScans(scansData.items?.slice(0, 10) || [])

      // Severity chart data
      setSeverityData(
        ['critical', 'high', 'medium', 'low', 'info']
          .map(s => ({ name: s, count: bySev[s] || 0, fill: severityColors[s] }))
          .filter(d => d.count > 0)
      )

      // Module chart data
      const moduleColors = ['#00ff88', '#3388ff', '#ff8800', '#ffcc00', '#aa55ff', '#ff2244', '#666688']
      setModuleData(
        Object.entries(byMod)
          .map(([name, count], i) => ({ name, value: count, fill: moduleColors[i % moduleColors.length] }))
          .filter(d => d.value > 0)
      )

      // Geo findings
      try {
        const allFindings = await getFindings('category=geolocation')
        setGeoFindings(allFindings.items || [])
      } catch {}
    } catch {}
  }

  async function handleQuickScan(e) {
    e.preventDefault()
    if (!quickEmail) return
    setLoading(true)
    try {
      const target = await createTarget({ email: quickEmail })
      await createScan({ target_id: target.id, modules: defaultModules })
      navigate(`/targets/${target.id}`)
    } catch (err) {
      alert(err.message)
    } finally {
      setLoading(false)
    }
  }

  const statusColors = {
    queued: '#666688', running: '#ffcc00', completed: '#00ff88', failed: '#ff2244', cancelled: '#666688',
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        <StatCard icon={Crosshair} label="Targets" value={stats.targets} color="#00ff88" />
        <StatCard icon={Radar} label="Scans" value={stats.scans} color="#3388ff" />
        <StatCard icon={AlertTriangle} label="Findings" value={stats.findings} color="#ffcc00" />
        <StatCard icon={ShieldAlert} label="Critical" value={stats.critical} color="#ff2244" />
        <StatCard icon={ShieldAlert} label="High" value={stats.high} color="#ff8800" />
      </div>

      {/* Most exposed target */}
      {topTarget && (
        <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-4 cursor-pointer hover:border-[#ff2244]/30 transition-colors"
             onClick={() => navigate(`/targets/${topTarget.id}`)}>
          <div className="flex items-center justify-between">
            <div>
              <span className="text-xs text-gray-500 uppercase tracking-wider">Most Exposed Target</span>
              <div className="flex items-center gap-3 mt-1">
                <span className="font-mono text-sm">{topTarget.email}</span>
                {topTarget.display_name && <span className="text-xs text-gray-400">({topTarget.display_name})</span>}
              </div>
            </div>
            <div className="flex items-center gap-3">
              {topFingerprint ? (
                <FingerprintRadar fingerprint={topFingerprint} size="small" animate={true} />
              ) : (
                <ScoreRing score={topTarget.exposure_score} size={60} />
              )}
            </div>
          </div>
        </div>
      )}

      {/* Quick Scan */}
      <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5">
        <h2 className="text-sm font-semibold mb-3">Quick Scan</h2>
        <form onSubmit={handleQuickScan} className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <input type="email" value={quickEmail} onChange={(e) => setQuickEmail(e.target.value)}
              placeholder="Enter email to scan..."
              className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg pl-10 pr-3 py-2.5 text-sm font-mono focus:outline-none focus:border-[#00ff88]/50" />
          </div>
          <button type="submit" disabled={loading}
            className="bg-[#00ff88] text-black font-semibold rounded-lg px-6 py-2.5 text-sm hover:bg-[#00ff88]/90 transition-colors disabled:opacity-50">
            {loading ? 'Scanning...' : 'Scan'}
          </button>
        </form>
      </div>

      {/* Charts */}
      {stats.findings > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Severity bar chart */}
          {severityData.length > 0 && (
            <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5">
              <h3 className="text-sm font-semibold mb-4">Findings by Severity</h3>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={severityData} layout="vertical">
                  <XAxis type="number" tick={{ fill: '#666688', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis type="category" dataKey="name" tick={{ fill: '#999', fontSize: 11 }} axisLine={false} tickLine={false} width={60} />
                  <Tooltip content={<CustomTooltip />} cursor={false} />
                  <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                    {severityData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Module donut */}
          {moduleData.length > 0 && (
            <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5">
              <h3 className="text-sm font-semibold mb-4">Findings by Module</h3>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie data={moduleData} cx="50%" cy="50%" innerRadius={50} outerRadius={80}
                    dataKey="value" nameKey="name" stroke="none">
                    {moduleData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex flex-wrap gap-3 mt-2 justify-center">
                {moduleData.map(d => (
                  <div key={d.name} className="flex items-center gap-1.5 text-xs text-gray-400">
                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: d.fill }} />
                    {d.name} ({d.value})
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Target Exposure Leaderboard */}
      {topTargets.length > 0 && (
        <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl overflow-hidden">
          <div className="px-5 py-4 border-b border-[#1e1e2e]">
            <h2 className="text-sm font-semibold">Most Exposed Targets</h2>
          </div>
          <div className="divide-y divide-[#1e1e2e]">
            {topTargets.map(t => {
              const expColor = t.exposure_score >= 60 ? '#ff2244' : t.exposure_score >= 30 ? '#ff8800' : '#00ff88'
              const thrColor = (t.threat_score || 0) >= 60 ? '#ff2244' : (t.threat_score || 0) >= 30 ? '#ff8800' : '#00ff88'
              return (
                <div key={t.id} onClick={() => navigate(`/targets/${t.id}`)}
                  className="flex items-center justify-between px-5 py-3 cursor-pointer hover:bg-white/[0.03] transition-colors">
                  <div className="flex items-center gap-3 min-w-0">
                    {t.avatar_url ? (
                      <img src={t.avatar_url} alt="" className="w-7 h-7 rounded-full border border-[#1e1e2e] shrink-0" />
                    ) : (
                      <div className="w-7 h-7 rounded-full bg-[#1e1e2e] flex items-center justify-center text-[10px] font-bold text-gray-500 shrink-0">
                        {(t.email || '?')[0].toUpperCase()}
                      </div>
                    )}
                    <span className="font-mono text-xs text-gray-300 truncate">{t.primary_name || t.display_name || t.email}</span>
                  </div>
                  <div className="flex items-center gap-4 text-xs font-mono shrink-0">
                    <span style={{ color: expColor }}>Exp: {t.exposure_score}</span>
                    <span style={{ color: thrColor }}>Threat: {t.threat_score ?? '-'}</span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* World Heatmap */}
      <WorldHeatmap key={geoFindings.length} findings={geoFindings} />

      {/* Recent Scans */}
      {recentScans.length > 0 && (
        <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl overflow-hidden">
          <div className="px-5 py-4 border-b border-[#1e1e2e]">
            <h2 className="text-sm font-semibold">Recent Scans</h2>
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-gray-500 uppercase tracking-wider">
                <th className="text-left px-5 py-3">Target</th>
                <th className="text-left px-5 py-3">Status</th>
                <th className="text-left px-5 py-3">Modules</th>
                <th className="text-left px-5 py-3">Findings</th>
                <th className="text-left px-5 py-3">Duration</th>
                <th className="text-left px-5 py-3">Date</th>
                <th className="text-right px-5 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {recentScans.map((scan, i) => (
                <tr key={scan.id} onClick={() => scan.target_id && navigate(`/targets/${scan.target_id}`)}
                  className={`border-t border-[#1e1e2e] cursor-pointer hover:bg-white/[0.03] ${i % 2 === 1 ? 'bg-white/[0.02]' : ''}`}>
                  <td className="px-5 py-3 font-mono text-xs text-gray-300 truncate max-w-[200px]">{scan.target_email || '-'}</td>
                  <td className="px-5 py-3">
                    <span className="inline-flex items-center gap-1.5 text-xs font-medium px-2 py-0.5 rounded-full"
                      style={{ backgroundColor: statusColors[scan.status] + '26', color: statusColors[scan.status] }}>
                      <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: statusColors[scan.status] }} />
                      {scan.status}
                    </span>
                  </td>
                  <td className="px-5 py-3 font-mono text-xs text-gray-400">{(scan.modules || []).join(', ')}</td>
                  <td className="px-5 py-3 font-mono">{scan.findings_count}</td>
                  <td className="px-5 py-3 font-mono text-gray-400">{scan.duration_ms ? `${(scan.duration_ms / 1000).toFixed(1)}s` : '-'}</td>
                  <td className="px-5 py-3 text-gray-400 text-xs font-mono">{scan.created_at ? new Date(scan.created_at).toLocaleString() : '-'}</td>
                  <td className="px-5 py-3 text-right">
                    {(scan.status === 'running' || scan.status === 'queued') && (
                      <button
                        onClick={async (e) => {
                          e.stopPropagation()
                          if (window.confirm('Cancel this scan?')) {
                            try { await cancelScan(scan.id); loadData() } catch (err) { console.error('Failed to cancel:', err) }
                          }
                        }}
                        className="text-xs px-2 py-1 rounded bg-[#ff2244]/10 text-[#ff2244] hover:bg-[#ff2244]/20 transition-colors"
                      >
                        Cancel
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {stats.targets === 0 && (
        <div className="text-center py-16 text-gray-500">
          <Shield className="w-12 h-12 mx-auto mb-4 text-[#00ff88]/30" />
          <p className="text-lg mb-1">Welcome to xpose</p>
          <p className="text-sm">Add your first target to start scanning.</p>
        </div>
      )}
    </div>
  )
}

function ScoreRing({ score, size = 60 }) {
  const color = score >= 61 ? '#ff2244' : score >= 31 ? '#ff8800' : '#00ff88'
  const r = 26
  const circumference = 2 * Math.PI * r
  return (
    <svg width={size} height={size} viewBox="0 0 60 60">
      <circle cx="30" cy="30" r={r} fill="none" stroke="#333" strokeWidth="3" opacity="0.2" />
      <circle cx="30" cy="30" r={r} fill="none" stroke={color} strokeWidth="3"
        strokeDasharray={`${(score || 0) / 100 * circumference} ${circumference}`}
        strokeLinecap="round" transform="rotate(-90 30 30)"
        className="transition-all duration-700" />
      <text x="30" y="34" textAnchor="middle" fill={color} fontSize="18" fontWeight="500" fontFamily="monospace">
        {score ?? '-'}
      </text>
    </svg>
  )
}

function Shield(props) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10" />
    </svg>
  )
}
