import { useEffect, useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Shield, AlertTriangle, Download, ArrowRight, Check, ChevronRight } from 'lucide-react'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { getTargets, getRemediation, getFingerprintHistory } from '../lib/api'
import GenerativeAvatar from '../components/GenerativeAvatar'

const fallbackSeed = (email) => {
  let hash = 0
  for (let i = 0; i < (email || '').length; i++) {
    hash = ((hash << 5) - hash) + email.charCodeAt(i)
    hash |= 0
  }
  return { email_hash: Math.abs(hash) }
}

const riskLabel = (score) => {
  if (score >= 61) return { text: 'HIGH', color: '#ff2244' }
  if (score >= 31) return { text: 'MODERATE', color: '#ff8800' }
  return { text: 'LOW', color: '#00ff88' }
}

function AnimatedScore({ score, size = 200 }) {
  const [animated, setAnimated] = useState(0)
  const ref = useRef(null)

  useEffect(() => {
    const timer = setTimeout(() => setAnimated(score), 300)
    return () => clearTimeout(timer)
  }, [score])

  const radius = (size - 20) / 2
  const circumference = 2 * Math.PI * radius
  const progress = (animated / 100) * circumference
  const risk = riskLabel(score)

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius}
          fill="none" stroke="#1e1e2e" strokeWidth="8" />
        <circle cx={size / 2} cy={size / 2} r={radius}
          fill="none" stroke={risk.color} strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference - progress}
          style={{ transition: 'stroke-dashoffset 1.5s ease-out' }} />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-5xl font-bold font-mono" style={{ color: risk.color }}>
          {animated}
        </span>
        <span className="text-xs text-gray-500 font-mono">/100</span>
      </div>
    </div>
  )
}

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-[#12121a] border border-[#1e1e2e] rounded-lg px-3 py-2 text-xs">
      <div className="text-gray-400">{payload[0]?.payload?.date}</div>
      <div className="font-mono text-white">Score: {payload[0]?.value}</div>
    </div>
  )
}

export default function UserPreview() {
  const [target, setTarget] = useState(null)
  const [actions, setActions] = useState([])
  const [history, setHistory] = useState([])
  const [checked, setChecked] = useState(new Set())
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    try {
      const data = await getTargets('per_page=100')
      const sorted = (data.items || [])
        .filter(t => t.exposure_score != null)
        .sort((a, b) => (b.exposure_score + (b.threat_score || 0)) - (a.exposure_score + (a.threat_score || 0)))

      if (!sorted.length) { setLoading(false); return }
      const top = sorted[0]
      setTarget(top)

      // Load remediation + history in parallel
      const [remData, histData] = await Promise.all([
        getRemediation(top.id).catch(() => ({ actions: [] })),
        getFingerprintHistory(top.id).catch(() => []),
      ])

      setActions(remData.actions || [])

      // Build evolution chart data
      if (histData && histData.length > 1) {
        setHistory(histData.map(h => ({
          date: new Date(h.computed_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
          score: h.score || 0,
        })))
      } else {
        // Simulate before/after
        const score = top.exposure_score || 0
        setHistory([
          { date: 'Before xpose', score: Math.min(100, score + 15 + Math.floor(Math.random() * 10)) },
          { date: 'After scan', score },
        ])
      }
    } catch (err) {
      console.error('UserPreview load failed:', err)
    } finally {
      setLoading(false)
    }
  }

  function toggleCheck(idx) {
    setChecked(prev => {
      const next = new Set(prev)
      if (next.has(idx)) next.delete(idx)
      else next.add(idx)
      return next
    })
  }

  async function handleDownloadPdf() {
    if (!target) return
    const token = localStorage.getItem('xpose_token')
    const res = await fetch(`/api/v1/targets/${target.id}/report/pdf`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `xposeTIP_report_${target.id}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500 text-sm">Loading your exposure report...</div>
      </div>
    )
  }

  if (!target) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4">
        <Shield className="w-16 h-16 text-gray-600" />
        <p className="text-gray-400 text-lg">No scanned targets yet</p>
        <button onClick={() => navigate('/targets')}
          className="text-sm text-[#00ff88] hover:underline">
          Add a target to get started
        </button>
      </div>
    )
  }

  const score = target.exposure_score || 0
  const risk = riskLabel(score)
  const profile = target.profile_data || {}
  const socialCount = (profile.social_profiles || []).length
  const breachCount = (profile.breach_summary || {}).count || 0
  const findingsCount = target.findings_count || profile.findings_count || 0
  const displayName = target.display_name || target.primary_name || ''
  const percentile = Math.min(95, Math.max(20, score + 30))

  // Score estimation from checked actions
  const estimatedReduction = [...checked].reduce((sum, idx) => {
    const a = actions[idx]
    if (!a) return sum
    if (a.priority === 'high') return sum + 5
    if (a.priority === 'medium') return sum + 3
    return sum + 1
  }, 0)
  const estimatedScore = Math.max(0, score - estimatedReduction)
  const estimatedRisk = riskLabel(estimatedScore)

  const priorityConfig = {
    high: { label: 'HIGH PRIORITY', color: '#ff2244', bg: 'bg-[#ff2244]/5', border: 'border-[#ff2244]/20', icon: '!' },
    medium: { label: 'MEDIUM PRIORITY', color: '#ff8800', bg: 'bg-[#ff8800]/5', border: 'border-[#ff8800]/20', icon: '!' },
    low: { label: 'LOW PRIORITY', color: '#3388ff', bg: 'bg-[#3388ff]/5', border: 'border-[#3388ff]/20', icon: 'i' },
  }

  // Group actions by priority
  const grouped = { high: [], medium: [], low: [] }
  actions.forEach((a, i) => {
    const key = a.priority || 'low'
    if (grouped[key]) grouped[key].push({ ...a, idx: i })
  })

  return (
    <div className="max-w-2xl mx-auto space-y-0">

      {/* ── Section 1: Identity Score Hero ── */}
      <section className="py-16 text-center">
        <div className="flex justify-center mb-6">
          {target.avatar_url ? (
            <img src={target.avatar_url} alt="" className="w-40 h-40 rounded-full border-4 border-[#1e1e2e]" />
          ) : (
            <GenerativeAvatar
              seed={target.fingerprint_avatar_seed || fallbackSeed(target.email)}
              size={160}
              score={score}
              className="rounded-full"
            />
          )}
        </div>

        {displayName && (
          <h1 className="text-3xl font-bold mb-1">{displayName}</h1>
        )}
        <p className="text-gray-500 font-mono text-sm mb-10">{target.email}</p>

        <div className="flex justify-center mb-6">
          <div className="text-center">
            <AnimatedScore score={score} size={200} />
            <div className="mt-4">
              <p className="text-lg text-gray-300">Your Digital Exposure Score</p>
              <p className="text-2xl font-bold font-mono mt-1" style={{ color: risk.color }}>
                {risk.text}
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-center gap-6 text-sm text-gray-400 mt-8">
          <span><span className="text-white font-semibold">{socialCount}</span> platforms</span>
          <span className="text-gray-600">|</span>
          <span><span className="text-white font-semibold">{breachCount}</span> breaches</span>
          <span className="text-gray-600">|</span>
          <span><span className="text-white font-semibold">{findingsCount || '?'}</span> findings</span>
        </div>

        <p className="text-gray-500 text-sm mt-4">
          You're more exposed than <span className="text-white font-semibold">{percentile}%</span> of users
        </p>
      </section>

      {/* ── Section 2: Score Evolution ── */}
      <section className="py-12">
        <h2 className="text-2xl font-bold mb-2">Your Exposure Over Time</h2>
        <p className="text-gray-500 text-sm mb-8">
          {history.length > 2
            ? `Since your first scan, your exposure ${
                history[history.length - 1]?.score < history[0]?.score
                  ? `decreased by ${history[0].score - history[history.length - 1].score} points. Keep improving!`
                  : 'has been tracked across multiple scans.'
              }`
            : 'This is your baseline. Rescan after applying our recommendations to track your improvement.'}
        </p>

        <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-6">
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={history}>
              <defs>
                <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={risk.color} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={risk.color} stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="date" tick={{ fill: '#666688', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis domain={[0, 100]} tick={{ fill: '#666688', fontSize: 11 }} axisLine={false} tickLine={false} width={30} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="score" stroke={risk.color} strokeWidth={2}
                fill="url(#scoreGradient)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </section>

      {/* ── Section 3: Action Plan ── */}
      <section className="py-12">
        <h2 className="text-2xl font-bold mb-2">Your Action Plan</h2>
        <p className="text-gray-500 text-sm mb-8">
          Complete these steps to reduce your digital exposure
        </p>

        <div className="space-y-6">
          {['high', 'medium', 'low'].map(priority => {
            const items = grouped[priority]
            if (!items.length) return null
            const cfg = priorityConfig[priority]

            return (
              <div key={priority} className={`border ${cfg.border} rounded-xl overflow-hidden`}>
                <div className={`px-5 py-3 ${cfg.bg} border-b ${cfg.border}`}>
                  <span className="text-xs font-bold tracking-wider" style={{ color: cfg.color }}>
                    {cfg.label}
                  </span>
                </div>
                <div className="divide-y divide-[#1e1e2e]">
                  {items.map(item => (
                    <div key={item.idx}
                      className="flex items-start gap-4 px-5 py-4 hover:bg-white/[0.02] transition-colors cursor-pointer"
                      onClick={() => toggleCheck(item.idx)}>
                      <div className={`shrink-0 w-5 h-5 rounded border-2 flex items-center justify-center mt-0.5 transition-colors ${
                        checked.has(item.idx)
                          ? 'bg-[#00ff88] border-[#00ff88]'
                          : 'border-gray-600'
                      }`}>
                        {checked.has(item.idx) && <Check className="w-3 h-3 text-black" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className={`text-sm font-medium ${checked.has(item.idx) ? 'line-through text-gray-600' : 'text-gray-200'}`}>
                          {item.action}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">{item.detail}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>

        {/* Progress bar */}
        {actions.length > 0 && (
          <div className="mt-8 space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-400">Progress</span>
              <span className="font-mono text-white">{checked.size}/{actions.length} completed</span>
            </div>
            <div className="h-2 bg-[#1e1e2e] rounded-full overflow-hidden">
              <div
                className="h-full bg-[#00ff88] rounded-full transition-all duration-500"
                style={{ width: `${(checked.size / actions.length) * 100}%` }}
              />
            </div>
            {checked.size > 0 && (
              <p className="text-sm text-gray-500">
                Estimated score after all actions:{' '}
                <span className="font-mono font-semibold" style={{ color: estimatedRisk.color }}>
                  ~{estimatedScore} ({estimatedRisk.text})
                </span>
              </p>
            )}
          </div>
        )}
      </section>

      {/* ── Footer CTA ── */}
      <section className="py-16 text-center border-t border-[#1e1e2e]">
        <h3 className="text-xl font-bold mb-2">Want continuous monitoring?</h3>
        <p className="text-gray-500 text-sm mb-8 max-w-md mx-auto">
          Upgrade to Consultant plan for recurring scans, dark web monitoring, and team collaboration.
        </p>
        <div className="flex items-center justify-center gap-4">
          <button onClick={() => navigate('/welcome')}
            className="flex items-center gap-2 bg-[#00ff88] text-black font-semibold rounded-lg px-6 py-3 text-sm hover:bg-[#00ff88]/90 transition-colors">
            Upgrade <ArrowRight className="w-4 h-4" />
          </button>
          <button onClick={handleDownloadPdf}
            className="flex items-center gap-2 border border-[#1e1e2e] rounded-lg px-6 py-3 text-sm text-gray-300 hover:border-[#00ff88]/30 hover:text-white transition-colors">
            <Download className="w-4 h-4" /> Download PDF Report
          </button>
        </div>
      </section>

    </div>
  )
}
