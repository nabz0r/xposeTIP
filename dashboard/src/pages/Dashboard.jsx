import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Crosshair, Radar, AlertTriangle, ShieldAlert, Search } from 'lucide-react'
import { getTargets, getScans, getFindingsStats, createTarget, createScan } from '../lib/api'

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

export default function Dashboard() {
  const [stats, setStats] = useState({ targets: 0, scans: 0, findings: 0, critical: 0 })
  const [recentScans, setRecentScans] = useState([])
  const [quickEmail, setQuickEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    try {
      const [targetsData, scansData, findingsData] = await Promise.all([
        getTargets(),
        getScans(),
        getFindingsStats(),
      ])
      setStats({
        targets: targetsData.total || 0,
        scans: scansData.items?.length || 0,
        findings: Object.values(findingsData.by_severity || {}).reduce((a, b) => a + b, 0),
        critical: findingsData.by_severity?.critical || 0,
      })
      setRecentScans(scansData.items?.slice(0, 10) || [])
    } catch {}
  }

  async function handleQuickScan(e) {
    e.preventDefault()
    if (!quickEmail) return
    setLoading(true)
    try {
      const target = await createTarget({ email: quickEmail })
      await createScan({ target_id: target.id, modules: ['email_validator', 'holehe'] })
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

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Crosshair} label="Targets" value={stats.targets} color="#00ff88" />
        <StatCard icon={Radar} label="Scans" value={stats.scans} color="#3388ff" />
        <StatCard icon={AlertTriangle} label="Findings" value={stats.findings} color="#ffcc00" />
        <StatCard icon={ShieldAlert} label="Critical" value={stats.critical} color="#ff2244" />
      </div>

      {/* Quick Scan */}
      <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5">
        <h2 className="text-sm font-semibold mb-3">Quick Scan</h2>
        <form onSubmit={handleQuickScan} className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <input
              type="email"
              value={quickEmail}
              onChange={(e) => setQuickEmail(e.target.value)}
              placeholder="Enter email to scan..."
              className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg pl-10 pr-3 py-2.5 text-sm font-mono focus:outline-none focus:border-[#00ff88]/50"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="bg-[#00ff88] text-black font-semibold rounded-lg px-6 py-2.5 text-sm hover:bg-[#00ff88]/90 transition-colors disabled:opacity-50"
          >
            {loading ? 'Scanning...' : 'Scan'}
          </button>
        </form>
      </div>

      {/* Recent Scans */}
      {recentScans.length > 0 && (
        <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl overflow-hidden">
          <div className="px-5 py-4 border-b border-[#1e1e2e]">
            <h2 className="text-sm font-semibold">Recent Scans</h2>
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-gray-500 uppercase tracking-wider">
                <th className="text-left px-5 py-3">Status</th>
                <th className="text-left px-5 py-3">Modules</th>
                <th className="text-left px-5 py-3">Findings</th>
                <th className="text-left px-5 py-3">Duration</th>
                <th className="text-left px-5 py-3">Date</th>
              </tr>
            </thead>
            <tbody>
              {recentScans.map((scan, i) => (
                <tr key={scan.id} className={`border-t border-[#1e1e2e] ${i % 2 === 1 ? 'bg-white/[0.02]' : ''}`}>
                  <td className="px-5 py-3">
                    <span
                      className="inline-flex items-center gap-1.5 text-xs font-medium px-2 py-0.5 rounded-full"
                      style={{ backgroundColor: statusColors[scan.status] + '26', color: statusColors[scan.status] }}
                    >
                      <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: statusColors[scan.status] }} />
                      {scan.status}
                    </span>
                  </td>
                  <td className="px-5 py-3 font-mono text-xs text-gray-400">
                    {(scan.modules || []).join(', ')}
                  </td>
                  <td className="px-5 py-3 font-mono">{scan.findings_count}</td>
                  <td className="px-5 py-3 font-mono text-gray-400">
                    {scan.duration_ms ? `${(scan.duration_ms / 1000).toFixed(1)}s` : '-'}
                  </td>
                  <td className="px-5 py-3 text-gray-400">
                    {scan.created_at ? new Date(scan.created_at).toLocaleDateString() : '-'}
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

function Shield(props) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10" />
    </svg>
  )
}
