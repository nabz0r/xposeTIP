import React, { useEffect, useState, useCallback, useRef, Fragment } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Radar, ChevronDown, ChevronRight, ExternalLink, Lock, CheckCircle, Filter, Shield, AlertTriangle, Globe, Link2, Unlink, XCircle, ArrowRightLeft } from 'lucide-react'
import { getTarget, getFindings, getScans, createScan, getModules, getScan, getGraph, patchFinding, getTargetSources, getAccounts, startOAuth, auditAccount, disconnectAccount, getFingerprint, getFingerprintHistory, getTargetProfile, cancelScan, getLogs, getFindingsStats, getWorkspaces, moveTarget } from '../lib/api'
import IdentityGraph from '../components/IdentityGraph'
import FingerprintRadar, { FingerprintTimeline } from '../components/FingerprintRadar'
import PlatformIcon, { getRemediationLink } from '../components/PlatformIcon'
import IOCTimeline from '../components/IOCTimeline'
import ProfileHeader from '../components/ProfileHeader'
import IdentityCard from '../components/IdentityCard'
import PersonaCard from '../components/PersonaCard'
import LocationMap from '../components/LocationMap'
import GenerativeAvatar from '../components/GenerativeAvatar'
import useSSE from '../hooks/useSSE'

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
  virustotal: '~10s', shodan: '~15s', intelx: '~15s', hunter: '~10s', dehashed: '~8s',
  reverse_image: '~15s', google_audit: '~10s', microsoft_audit: '~10s',
}

export default function TargetDetail() {
  const { id } = useParams()
  const [target, setTarget] = useState(null)
  const [findings, setFindings] = useState([])
  const [scans, setScans] = useState([])
  const [modules, setModules] = useState([])
  const [graphData, setGraphData] = useState(null)
  const [sourcesData, setSourcesData] = useState(null)
  const [expanded, setExpanded] = useState(null)
  const [showScanModal, setShowScanModal] = useState(false)
  const [selectedModules, setSelectedModules] = useState([])
  const [scanning, setScanning] = useState(false)
  const [activeTab, setActiveTab] = useState('overview')
  const [toast, setToast] = useState(null)
  const [accounts, setAccounts] = useState([])
  const [auditingAccount, setAuditingAccount] = useState(null)
  const [fingerprint, setFingerprint] = useState(null)
  const [fpHistory, setFpHistory] = useState([])
  const [profile, setProfile] = useState(null)
  // Filters
  const [sevFilter, setSevFilter] = useState('all')
  const [modFilter, setModFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')
  const [findingsLimit, setFindingsLimit] = useState(20)
  // Score animation
  const [animScore, setAnimScore] = useState(0)
  const pollRef = useRef(null)
  // Move target
  const [workspaces, setWorkspaces] = useState([])
  const [showMoveMenu, setShowMoveMenu] = useState(false)

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
      getTargetProfile(id).then(setProfile).catch(() => setProfile(null))
    } catch {}
  }, [id])

  useEffect(() => { load() }, [load])
  useSSE({
    'scan.completed': (e) => { if (e.target_id === id) load() },
    'target.updated': (e) => { if (e.target_id === id) load() },
  })

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
        // Live fingerprint update during scan
        getFingerprint(id).then(setFingerprint).catch(() => {})

        if (done) {
          clearInterval(pollRef.current)
          // Auto-refresh findings, target, score, and fingerprint
          const [t, f] = await Promise.all([getTarget(id), getFindings(`target_id=${id}`)])
          setTarget(t)
          const newFindings = f.items || []
          const newCount = newFindings.length - findings.length
          setFindings(newFindings)
          // Final fingerprint + history refresh
          getFingerprint(id).then(setFingerprint).catch(() => {})
          getFingerprintHistory(id).then(d => setFpHistory(d.snapshots || [])).catch(() => {})
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

  // Load sources data + fingerprint
  useEffect(() => {
    if (findings.length > 0) {
      getTargetSources(id).then(setSourcesData).catch(() => {})
      getFingerprint(id).then(setFingerprint).catch(() => {})
      getFingerprintHistory(id).then(d => setFpHistory(d.snapshots || [])).catch(() => {})
    }
  }, [findings.length, id])

  // Load connected accounts
  useEffect(() => {
    if (activeTab === 'accounts' || activeTab === 'overview') {
      getAccounts(id).then(d => setAccounts(d.items || [])).catch(() => {})
    }
  }, [activeTab, id])

  useEffect(() => {
    getModules().then(m => {
      setModules(m)
      // Pre-select all enabled+implemented Layer 1 + recommended Layer 2 modules
      const recommended = ['dns_deep', 'leaked_domains', 'geoip']
      setSelectedModules(m.filter(mod => mod.enabled && mod.implemented && (mod.layer === 1 || recommended.includes(mod.id))).map(mod => mod.id))
    }).catch(() => {})
    getWorkspaces().then(ws => setWorkspaces(ws.items || ws || [])).catch(() => {})
  }, [])

  async function handleMoveTarget(destWsId) {
    try {
      await moveTarget(id, destWsId)
      setShowMoveMenu(false)
      alert('Target moved successfully')
      window.location.href = '/targets'
    } catch (err) {
      alert(err.message)
    }
  }

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
  const breachFindings = findings.filter(f => f.category === 'breach' && !(f.title || '').toLowerCase().includes('not configured') && !(f.title || '').toLowerCase().includes('api key'))
  const socialFindings = findings.filter(f => f.category === 'social_account')
  const geoFindings = findings.filter(f => f.category === 'geolocation')
  const intelFindings = findings.filter(f => f.module === 'intelligence')
  const riskAssessment = intelFindings.find(f => f.title?.startsWith('Risk Assessment:'))
  const remediations = riskAssessment?.data?.remediations || []
  const criticalCount = findings.filter(f => f.severity === 'critical' || f.severity === 'high').length

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-xs text-gray-500">
        <Link to="/targets" className="hover:text-[#00ff88] transition-colors">Targets</Link>
        <span>/</span>
        <span className="font-mono text-gray-300">{target.email}</span>
        <span>/</span>
        <span className="text-gray-400 capitalize">{activeTab}</span>
      </nav>

      {/* Profile Header */}
      <div className="flex items-start gap-4">
        <div className="flex-1">
          <ProfileHeader target={target} findings={findings} animScore={animScore} profileData={profile} />
        </div>
        <div className="shrink-0 flex items-center gap-2 mt-2">
          {workspaces.length > 1 && (
            <div className="relative">
              <button onClick={() => setShowMoveMenu(!showMoveMenu)}
                className="flex items-center gap-1.5 text-xs px-3 py-2.5 border border-[#1e1e2e] rounded-lg text-gray-400 hover:text-white transition-colors">
                <ArrowRightLeft className="w-3 h-3" /> Move
              </button>
              {showMoveMenu && (
                <div className="absolute right-0 mt-1 bg-[#12121a] border border-[#1e1e2e] rounded-lg py-1 z-50 min-w-[200px] shadow-xl">
                  {workspaces.filter(ws => ws.id !== target?.workspace_id).map(ws => (
                    <button key={ws.id} onClick={() => handleMoveTarget(ws.id)}
                      className="w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-[#1e1e2e] transition-colors">
                      Move to {ws.name}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
          <button onClick={() => setShowScanModal(true)}
            className="flex items-center gap-2 bg-[#00ff88] text-black font-semibold rounded-lg px-4 py-2.5 text-sm hover:bg-[#00ff88]/90">
            <Radar className="w-4 h-4" /> New Scan
          </button>
        </div>
      </div>

      {/* Live scan progress */}
      {scans.some(s => s.status === 'running' || s.status === 'queued') && (() => {
        const runningScan = scans.find(s => s.status === 'running' || s.status === 'queued')
        const progress = runningScan?.module_progress || {}
        const total = Object.keys(progress).length
        const completed = Object.values(progress).filter(s => s === 'completed' || s === 'failed' || s === 'skipped').length
        const pct = total > 0 ? Math.round((completed / total) * 100) : 0
        return (
          <div className="bg-[#12121a] border border-[#00ff88]/20 rounded-xl p-4 animate-pulse-subtle">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-[#00ff88] animate-pulse" />
                <span className="text-sm font-medium">Scanning {target.email}...</span>
                <span className="text-xs text-gray-500">{completed}/{total} modules</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-xs font-mono text-[#00ff88]">{pct}%</span>
                <button
                  onClick={async (e) => {
                    e.stopPropagation()
                    if (window.confirm('Cancel this scan?')) {
                      try {
                        await cancelScan(runningScan.id)
                        load()
                      } catch (err) {
                        console.error('Failed to cancel scan:', err)
                      }
                    }
                  }}
                  className="flex items-center gap-1 text-xs px-2 py-1 rounded bg-[#ff2244]/10 text-[#ff2244] hover:bg-[#ff2244]/20 transition-colors"
                >
                  <XCircle className="w-3 h-3" /> Stop
                </button>
              </div>
            </div>
            <div className="h-1.5 bg-[#0a0a0f] rounded-full overflow-hidden mb-3">
              <div className="h-full rounded-full bg-[#00ff88] transition-all duration-500" style={{ width: `${pct}%` }} />
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-1.5">
              {Object.entries(progress).map(([mod, st]) => (
                <div key={mod} className="flex items-center gap-1.5 text-xs font-mono px-2 py-1 rounded bg-[#0a0a0f]">
                  {st === 'completed' ? <CheckCircle className="w-3 h-3 text-[#00ff88]" /> :
                   st === 'running' ? <Radar className="w-3 h-3 text-[#3388ff] animate-spin" /> :
                   st === 'failed' ? <AlertTriangle className="w-3 h-3 text-[#ff2244]" /> :
                   st === 'skipped' ? <CheckCircle className="w-3 h-3 text-[#666688]" /> :
                   <div className="w-3 h-3 rounded-full border border-gray-600" />}
                  <span className="truncate text-gray-400">{mod}</span>
                </div>
              ))}
            </div>
          </div>
        )
      })()}

      {/* Tabs */}
      <div className="flex gap-1 border-b border-[#1e1e2e]">
        {['overview', 'findings', 'graph', 'timeline', 'locations', 'accounts', 'scans'].map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm capitalize transition-colors ${activeTab === tab ? 'text-[#00ff88] border-b-2 border-[#00ff88]' : 'text-gray-400 hover:text-white'}`}>
            {tab} {tab === 'findings' ? `(${findings.length})` : tab === 'scans' ? `(${scans.length})` : tab === 'accounts' ? `(${accounts.length})` : ''}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-4">
          {/* Risk Dashboard */}
          {riskAssessment && (
            <div className={`rounded-xl p-5 border ${
              riskAssessment.data?.risk_level === 'CRITICAL' ? 'bg-[#ff2244]/10 border-[#ff2244]/30' :
              riskAssessment.data?.risk_level === 'HIGH' ? 'bg-[#ff8800]/10 border-[#ff8800]/30' :
              riskAssessment.data?.risk_level === 'MODERATE' ? 'bg-[#ffcc00]/10 border-[#ffcc00]/30' :
              'bg-[#00ff88]/10 border-[#00ff88]/30'
            }`}>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <Shield className={`w-6 h-6 ${
                    riskAssessment.data?.risk_level === 'CRITICAL' ? 'text-[#ff2244]' :
                    riskAssessment.data?.risk_level === 'HIGH' ? 'text-[#ff8800]' :
                    riskAssessment.data?.risk_level === 'MODERATE' ? 'text-[#ffcc00]' :
                    'text-[#00ff88]'
                  }`} />
                  <div>
                    <h3 className="text-sm font-semibold">RISK LEVEL: {riskAssessment.data?.risk_level}</h3>
                    <p className="text-xs text-gray-400">{riskAssessment.data?.summary || {
                      CRITICAL: 'This identity is severely compromised. Immediate action required.',
                      HIGH: 'Significant exposure detected. Multiple risks need attention.',
                      MODERATE: 'Some exposure found. Recommended improvements available.',
                      LOW: 'Minimal exposure. Good digital hygiene.',
                    }[riskAssessment.data?.risk_level] || ''}</p>
                  </div>
                </div>
                <div className="flex gap-4 text-right">
                  <div>
                    <div className="text-2xl font-mono font-bold" style={{ color: scoreColor(target.exposure_score) }}>
                      {target.exposure_score ?? '-'}
                    </div>
                    <div className="text-[10px] text-gray-500 uppercase">Exposure</div>
                  </div>
                  <div>
                    <div className="text-2xl font-mono font-bold" style={{ color: (target.threat_score ?? 0) >= 61 ? '#ff2244' : (target.threat_score ?? 0) >= 31 ? '#ff8800' : '#00ff88' }}>
                      {target.threat_score ?? 0}
                    </div>
                    <div className="text-[10px] text-gray-500 uppercase">Threat</div>
                  </div>
                </div>
              </div>
              {/* Progress bar */}
              <div className="h-2 bg-[#0a0a0f] rounded-full overflow-hidden mb-4">
                <div className="h-full rounded-full transition-all duration-1000"
                  style={{ width: `${target.exposure_score || 0}%`, backgroundColor: scoreColor(target.exposure_score) }} />
              </div>
              {/* Stat pills */}
              <div className="flex gap-3 mb-4">
                {[
                  { label: 'Accounts', value: socialFindings.length, color: '#3388ff' },
                  { label: 'Breaches', value: breachFindings.length, color: '#ff2244' },
                  { label: 'Findings', value: findings.length, color: '#ffcc00' },
                  { label: 'Sources', value: sourcesData?.sources?.length || 0, color: '#666688' },
                ].map(s => (
                  <div key={s.label} className="flex-1 bg-[#0a0a0f] rounded-lg p-3 text-center">
                    <div className="text-lg font-mono font-bold" style={{ color: s.color }}>{s.value}</div>
                    <div className="text-[10px] text-gray-500 uppercase">{s.label}</div>
                  </div>
                ))}
              </div>
              {/* Executive Summary */}
              {riskAssessment?.data?.executive_summary && (
                <div className="bg-[#0a0a0f] rounded-lg p-4 mt-4">
                  <h4 className="text-[10px] uppercase tracking-wider text-gray-500 mb-2">Executive Summary</h4>
                  <p className="text-sm text-gray-300 leading-relaxed">{riskAssessment.data.executive_summary}</p>
                </div>
              )}
            </div>
          )}

          {/* Identity Estimation */}
          <IdentityCard profile={profile} />

          {/* Persona Clusters */}
          <PersonaCard personas={profile?.personas} />

          {/* Digital Fingerprint */}
          {fingerprint && (
            <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-4">Digital Fingerprint</h3>
              <div className="flex flex-col lg:flex-row items-center gap-6">
                {/* GenerativeAvatar — identity glyph from graph topology */}
                {fingerprint?.avatar_seed && (
                  <div className="shrink-0 flex flex-col items-center gap-2">
                    <GenerativeAvatar seed={fingerprint.avatar_seed} size={120} score={target?.exposure_score} />
                    <span className="text-[10px] text-gray-600 font-mono">identity glyph</span>
                  </div>
                )}
                <div className="flex-1 flex justify-center">
                  <FingerprintRadar fingerprint={fingerprint} size="large" animate={true} />
                </div>
                <div className="w-full lg:w-64 space-y-2">
                  {Object.entries(fingerprint.axes || {}).map(([key, val]) => {
                    const rawKey = key === 'email_age' ? 'email_age_years' : key === 'security' ? 'security_weak' : key
                    const rawVal = fingerprint.raw_values?.[rawKey] ?? 0
                    return (
                      <div key={key} className="space-y-0.5">
                        <div className="flex justify-between text-[10px]">
                          <span className="text-gray-400">{key.replace(/_/g, ' ')}</span>
                          <span className="font-mono" style={{ color: fingerprint.color }}>{rawVal}</span>
                        </div>
                        <div className="h-1.5 bg-[#0a0a0f] rounded-full overflow-hidden">
                          <div className="h-full rounded-full transition-all duration-700"
                            style={{ width: `${(val * 100).toFixed(0)}%`, backgroundColor: fingerprint.color }} />
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>
          )}

          {/* Fingerprint Evolution */}
          {fpHistory.length > 1 && (
            <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5">
              <FingerprintTimeline snapshots={fpHistory} />
            </div>
          )}

          {/* Remediation Actions */}
          {remediations.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">
                Top Actions Required ({remediations.length})
              </h3>
              <div className="space-y-2">
                {remediations.slice(0, 7).map((r, i) => (
                  <div key={i} className="bg-[#12121a] border border-[#1e1e2e] rounded-lg p-3 hover:border-[#00ff88]/20 transition-colors">
                    <div className="flex items-start gap-3">
                      <span className={`inline-block text-[10px] font-bold px-1.5 py-0.5 rounded-full mt-0.5 ${
                        r.priority === 'critical' ? 'bg-[#ff2244]/20 text-[#ff2244]' :
                        r.priority === 'high' ? 'bg-[#ff8800]/20 text-[#ff8800]' :
                        'bg-[#ffcc00]/20 text-[#ffcc00]'
                      }`}>{i + 1}</span>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium">{r.action}</div>
                        {r.finding && <p className="text-[10px] text-gray-500 mt-0.5">{r.finding}</p>}
                        {r.steps && (
                          <div className="flex flex-wrap gap-1 mt-1.5">
                            {r.steps.slice(0, 3).map((step, j) => (
                              <span key={j} className="text-[10px] px-1.5 py-0.5 rounded bg-[#1e1e2e] text-gray-400">{step}</span>
                            ))}
                          </div>
                        )}
                      </div>
                      {r.link && (
                        <a href={r.link} target="_blank" rel="noreferrer"
                           className="text-[10px] px-2 py-1 rounded bg-[#00ff88]/10 text-[#00ff88] hover:bg-[#00ff88]/20 shrink-0">
                          Secure
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Critical alerts (fallback when no risk assessment yet) */}
          {!riskAssessment && criticalCount > 0 && (
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

          {/* Social accounts with PlatformIcon */}
          {socialFindings.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">Accounts ({socialFindings.length})</h3>
              <div className="flex flex-wrap gap-2">
                {socialFindings.slice(0, 15).map(f => {
                  const platform = f.data?.platform || f.data?.network || f.data?.service || f.title?.split(' on ')?.[1] || f.module
                  const username = f.data?.username || f.data?.handle || f.data?.login || ''
                  return (
                    <PlatformIcon key={f.id} platform={platform} username={username} url={f.url} />
                  )
                })}
                {socialFindings.length > 15 && (
                  <button onClick={() => setActiveTab('findings')} className="text-xs text-gray-500 self-center ml-1">
                    +{socialFindings.length - 15} more
                  </button>
                )}
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

          {/* Source reliability */}
          {sourcesData?.sources?.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">
                Sources ({sourcesData.sources.length})
                {sourcesData.overall_confidence > 0 && (
                  <span className="ml-2 text-[10px] font-normal normal-case text-gray-600">
                    Overall confidence: {Math.round(sourcesData.overall_confidence * 100)}%
                    {sourcesData.cross_verified_count > 0 && ` | ${sourcesData.cross_verified_count} cross-verified`}
                  </span>
                )}
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                {sourcesData.sources.map(s => {
                  const relColor = s.reliability >= 0.8 ? '#00ff88' : s.reliability >= 0.6 ? '#ffcc00' : '#ff8800'
                  const pct = Math.round(s.reliability * 100)
                  return (
                    <div key={s.module} className="bg-[#12121a] border border-[#1e1e2e] rounded-lg p-3 flex items-center gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-mono font-medium truncate">{s.module}</span>
                          <span className="text-[10px] px-1.5 py-0.5 rounded-full font-mono"
                            style={{ backgroundColor: relColor + '20', color: relColor }}>
                            {pct}%
                          </span>
                        </div>
                        <div className="mt-1.5 h-1.5 rounded-full bg-[#0a0a0f] overflow-hidden">
                          <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, backgroundColor: relColor }} />
                        </div>
                        <div className="flex gap-3 mt-1 text-[10px] text-gray-500">
                          <span>{s.findings_count} findings</span>
                          <span>{s.verified_count} verified</span>
                          <span>avg {Math.round(s.avg_confidence * 100)}%</span>
                        </div>
                      </div>
                    </div>
                  )
                })}
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
          {/* Remediation progress bar */}
          {(() => {
            const actionable = findings.filter(f => ['critical', 'high', 'medium'].includes(f.severity))
            const resolved = actionable.filter(f => ['resolved', 'dismissed', 'false_positive'].includes(f.status))
            const pct = actionable.length > 0 ? Math.round(resolved.length / actionable.length * 100) : 100
            const barColor = pct >= 80 ? '#00ff88' : pct >= 50 ? '#ffcc00' : '#ff8800'
            return actionable.length > 0 ? (
              <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-4 mb-4">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs text-gray-400">Remediation Progress</span>
                  <span className="text-xs font-mono" style={{ color: barColor }}>{resolved.length}/{actionable.length} resolved ({pct}%)</span>
                </div>
                <div className="h-2 bg-[#0a0a0f] rounded-full overflow-hidden">
                  <div className="h-full rounded-full transition-all duration-500" style={{ width: `${pct}%`, backgroundColor: barColor }} />
                </div>
              </div>
            ) : null
          })()}

          {/* Filters + CSV export */}
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
              <option value="dismissed">Dismissed</option>
              <option value="false_positive">False positive</option>
              <option value="monitoring">Monitoring</option>
            </select>
            <button
              onClick={() => {
                const rows = [['Severity','Module','Title','Category','Status','Confidence','Indicator','Date','Description'].join(',')]
                filteredFindings.forEach(f => {
                  const esc = (v) => `"${String(v || '').replace(/"/g, '""')}"`
                  rows.push([
                    esc(f.severity), esc(f.module), esc(f.title), esc(f.category),
                    esc(f.status), f.confidence != null ? Math.round(f.confidence * 100) + '%' : '',
                    esc(f.indicator_value), f.first_seen ? new Date(f.first_seen).toISOString() : '',
                    esc(f.description),
                  ].join(','))
                })
                const blob = new Blob([rows.join('\n')], { type: 'text/csv' })
                const url = URL.createObjectURL(blob)
                const a = document.createElement('a')
                a.href = url
                a.download = `xpose-findings-${target.email}-${new Date().toISOString().slice(0,10)}.csv`
                a.click()
                URL.revokeObjectURL(url)
              }}
              className="ml-auto text-xs text-gray-400 hover:text-[#00ff88] border border-[#1e1e2e] rounded-lg px-3 py-1.5 hover:border-[#00ff88]/30 transition-colors"
            >
              Export CSV
            </button>
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
                  <th className="text-left px-4 py-3">Confidence</th>
                  <th className="text-left px-4 py-3">Status</th>
                  <th className="text-left px-4 py-3">Date</th>
                </tr>
              </thead>
              <tbody>
                {filteredFindings.slice(0, findingsLimit).map((f, i) => (
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
                        {f.confidence != null && (
                          <span className="inline-block text-[10px] font-mono px-1.5 py-0.5 rounded"
                            style={{
                              backgroundColor: (f.confidence >= 0.8 ? '#00ff88' : f.confidence >= 0.6 ? '#ffcc00' : '#ff8800') + '20',
                              color: f.confidence >= 0.8 ? '#00ff88' : f.confidence >= 0.6 ? '#ffcc00' : '#ff8800',
                            }}>
                            {Math.round(f.confidence * 100)}%
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`text-xs ${f.status === 'resolved' ? 'text-[#00ff88]' : f.status === 'false_positive' ? 'text-gray-500' : 'text-gray-400'}`}>
                          {f.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-400 text-xs">{f.first_seen ? new Date(f.first_seen).toLocaleDateString() : '-'}</td>
                    </tr>
                    {expanded === f.id && (
                      <tr className="bg-[#0a0a0f]">
                        <td colSpan={8} className="px-6 py-4">
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
                            <div className="flex items-center gap-2">
                              <span className="text-[10px] text-gray-500">Status:</span>
                              <select
                                value={f.status || 'active'}
                                onClick={e => e.stopPropagation()}
                                onChange={async (e) => {
                                  e.stopPropagation()
                                  try {
                                    await patchFinding(f.id, { status: e.target.value })
                                    load()
                                  } catch (err) { alert(err.message) }
                                }}
                                className="bg-[#0a0a0f] border border-[#1e1e2e] rounded px-2 py-1 text-xs focus:outline-none focus:border-[#00ff88]/50"
                              >
                                <option value="active">Active</option>
                                <option value="resolved">Resolved</option>
                                <option value="dismissed">Dismissed</option>
                                <option value="false_positive">False positive</option>
                                <option value="monitoring">Monitoring</option>
                              </select>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                ))}
                {filteredFindings.length === 0 && (
                  <tr><td colSpan={8} className="px-5 py-8 text-center text-gray-500">
                    {findings.length === 0 ? 'No findings yet. Launch a scan to discover exposure.' : 'No findings match the current filters.'}
                  </td></tr>
                )}
              </tbody>
            </table>
          </div>
          {filteredFindings.length > findingsLimit && (
            <button onClick={() => setFindingsLimit(prev => prev + 20)}
              className="w-full mt-3 py-2.5 text-sm text-gray-400 hover:text-[#00ff88] bg-[#12121a] border border-[#1e1e2e] rounded-lg hover:border-[#00ff88]/30 transition-colors">
              Show more ({filteredFindings.length - findingsLimit} remaining)
            </button>
          )}
        </div>
      )}

      {/* Graph Tab */}
      {activeTab === 'graph' && <IdentityGraph data={graphData} personas={profile?.personas || []} />}

      {/* Timeline Tab */}
      {activeTab === 'timeline' && <IOCTimeline findings={findings} />}

      {/* Locations Tab */}
      {activeTab === 'locations' && <LocationMap findings={findings} />}

      {/* Accounts Tab */}
      {activeTab === 'accounts' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-300">Connected Accounts</h3>
            <div className="flex gap-2">
              {['google', 'microsoft'].map(provider => (
                <button
                  key={provider}
                  onClick={async () => {
                    try {
                      const redirectUri = `${window.location.origin}/oauth/callback`
                      const res = await startOAuth({ provider, target_id: id, redirect_uri: redirectUri })
                      window.open(res.auth_url, '_blank', 'width=500,height=600')
                    } catch (err) {
                      setToast({ type: 'error', message: err.message })
                      setTimeout(() => setToast(null), 5000)
                    }
                  }}
                  className="inline-flex items-center gap-2 text-xs px-3 py-1.5 rounded-lg bg-[#12121a] border border-[#1e1e2e] hover:border-[#00ff88]/30 text-gray-300 hover:text-white transition-colors"
                >
                  <Link2 className="w-3 h-3" />
                  Connect {provider.charAt(0).toUpperCase() + provider.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {accounts.length === 0 ? (
            <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-12 text-center">
              <Link2 className="w-12 h-12 text-gray-600 mx-auto mb-3" />
              <h3 className="text-lg font-medium text-gray-300">No connected accounts</h3>
              <p className="text-sm text-gray-500 mt-1 mb-4">
                Connect Google or Microsoft accounts to audit third-party app access, login devices, and permissions.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {accounts.map(acc => (
                <div key={acc.id} className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-4 hover:border-[#00ff88]/20 transition-colors">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold capitalize">{acc.provider}</span>
                      {acc.email && <span className="text-xs text-gray-400 font-mono">{acc.email}</span>}
                    </div>
                    <button
                      onClick={async () => {
                        if (confirm('Disconnect this account?')) {
                          await disconnectAccount(acc.id)
                          setAccounts(prev => prev.filter(a => a.id !== acc.id))
                        }
                      }}
                      className="text-gray-500 hover:text-[#ff2244] transition-colors"
                    >
                      <Unlink className="w-3.5 h-3.5" />
                    </button>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-gray-500 mb-3">
                    {acc.scopes?.length > 0 && <span>{acc.scopes.length} scopes</span>}
                    {acc.last_audited && <span>Last audit: {new Date(acc.last_audited).toLocaleDateString()}</span>}
                    <span>Connected: {new Date(acc.created_at).toLocaleDateString()}</span>
                  </div>
                  <button
                    onClick={async () => {
                      setAuditingAccount(acc.id)
                      try {
                        const res = await auditAccount(acc.id)
                        setToast({ type: 'success', message: `Audit completed — ${res.findings_count} findings` })
                        setTimeout(() => setToast(null), 5000)
                        load()
                      } catch (err) {
                        setToast({ type: 'error', message: err.message })
                        setTimeout(() => setToast(null), 5000)
                      } finally {
                        setAuditingAccount(null)
                      }
                    }}
                    disabled={auditingAccount === acc.id}
                    className="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-[#00ff88]/10 text-[#00ff88] hover:bg-[#00ff88]/20 transition-colors disabled:opacity-50"
                  >
                    <Radar className="w-3 h-3" />
                    {auditingAccount === acc.id ? 'Auditing...' : 'Run Audit'}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Scans Tab */}
      {activeTab === 'scans' && (
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

const SECURITY_URLS = {
  spotify: 'https://www.spotify.com/account/security/',
  twitter: 'https://twitter.com/settings/security',
  facebook: 'https://www.facebook.com/settings?tab=security',
  instagram: 'https://www.instagram.com/accounts/privacy_and_security/',
  github: 'https://github.com/settings/security',
  google: 'https://myaccount.google.com/security',
  reddit: 'https://www.reddit.com/prefs/update/',
  steam: 'https://store.steampowered.com/account/',
  linkedin: 'https://www.linkedin.com/psettings/',
  discord: 'https://discord.com/channels/@me',
  twitch: 'https://www.twitch.tv/settings/security',
  medium: 'https://medium.com/me/settings/security',
  gitlab: 'https://gitlab.com/-/profile/account',
}

const DATA_CLASS_COLORS = {
  'Passwords': '#ff2244',
  'Email addresses': '#ff8800',
  'Phone numbers': '#ffcc00',
  'IP addresses': '#ff8800',
  'Credit cards': '#ff2244',
  'Physical addresses': '#ff8800',
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
    const hasPasswords = dataClasses.some(dc => dc.toLowerCase().includes('password'))
    return (
      <div className="bg-[#12121a] rounded-lg p-4 border border-[#ff2244]/20">
        <div className="flex items-center gap-2 mb-2">
          <Shield className="w-4 h-4 text-[#ff2244]" />
          <span className="font-semibold text-sm">{name}</span>
          {date && <span className="text-xs text-gray-500">{date}</span>}
        </div>
        {count && <p className="text-xs text-gray-400 mb-2">{typeof count === 'number' ? count.toLocaleString() : count} records exposed</p>}
        {dataClasses.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {dataClasses.slice(0, 12).map(dc => (
              <span key={dc} className="text-[10px] px-1.5 py-0.5 rounded font-mono"
                style={{ backgroundColor: (DATA_CLASS_COLORS[dc] || '#666688') + '15', color: DATA_CLASS_COLORS[dc] || '#ff8800' }}>
                {dc}
              </span>
            ))}
            {dataClasses.length > 12 && <span className="text-[10px] text-gray-500">+{dataClasses.length - 12}</span>}
          </div>
        )}
        {hasPasswords && (
          <div className="text-xs text-[#ff2244] bg-[#ff2244]/10 rounded px-2 py-1.5">
            ⚠ Passwords were exposed in this breach — change your password immediately
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
    const secUrl = SECURITY_URLS[platform.toLowerCase()] || null
    return (
      <div className="bg-[#12121a] rounded-lg p-4 border border-[#3388ff]/20">
        <div className="flex items-center gap-3">
          {d.avatar_url && <img src={d.avatar_url} alt="" className="w-8 h-8 rounded-full" />}
          <div className="flex-1 min-w-0">
            <span className="text-sm font-medium">{platform}</span>
            {username && <span className="text-xs text-gray-400 ml-2">@{username}</span>}
            {url && <a href={url} target="_blank" rel="noreferrer" className="block text-[10px] text-[#3388ff] hover:underline mt-0.5">{url.replace(/https?:\/\//, '').substring(0, 50)}</a>}
          </div>
          {secUrl && (
            <a href={secUrl} target="_blank" rel="noreferrer"
               className="text-[10px] px-2 py-1 rounded bg-[#00ff88]/10 text-[#00ff88] hover:bg-[#00ff88]/20 whitespace-nowrap">
              Secure this account →
            </a>
          )}
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
  // Managed domain (from domain_analyzer)
  if (d.analyzer === 'domain_analyzer' && d.managed) {
    return (
      <div className="bg-[#12121a] rounded-lg p-3 border border-[#3388ff]/20">
        <div className="flex items-center gap-2">
          <Globe className="w-4 h-4 text-[#3388ff]" />
          <span className="text-sm font-medium text-[#3388ff]">Managed Domain</span>
        </div>
        <p className="text-xs text-gray-400 mt-1">{d.domain} is a SaaS email provider. DNS records are managed by the provider — no user action needed.</p>
      </div>
    )
  }

  if (mod === 'dns_deep' && (d.spf_record !== undefined || d.security_score !== undefined)) {
    if (d.security_score !== undefined) {
      return (
        <div className="bg-[#12121a] rounded-lg p-3 border border-[#1e1e2e]">
          <div className="grid grid-cols-3 gap-3 text-xs mb-2">
            <div><span className="text-gray-500">SPF</span><div className={d.has_spf ? 'text-[#00ff88]' : 'text-[#ff2244]'}>{d.has_spf ? '✓ Configured' : '✗ Missing'}</div></div>
            <div><span className="text-gray-500">DMARC</span><div className={d.has_dmarc ? 'text-[#00ff88]' : 'text-[#ff2244]'}>{d.has_dmarc ? '✓ Configured' : '✗ Missing'}</div></div>
            <div><span className="text-gray-500">DKIM</span><div className={d.has_dkim ? 'text-[#00ff88]' : 'text-[#ffcc00]'}>{d.has_dkim ? '✓ Configured' : '⚠ Not found'}</div></div>
          </div>
          {d.spf_record && <div className="text-[10px] font-mono text-gray-500 bg-[#0a0a0f] p-2 rounded mt-2 break-all">{d.spf_record}</div>}
          {d.dmarc_record && <div className="text-[10px] font-mono text-gray-500 bg-[#0a0a0f] p-2 rounded mt-1 break-all">{d.dmarc_record}</div>}
        </div>
      )
    }
  }

  // Intelligence findings
  if (mod === 'intelligence' && d.risk_level) {
    return (
      <div className="bg-[#12121a] rounded-lg p-3 border border-[#1e1e2e]">
        {d.summary && <p className="text-xs text-gray-300 mb-2">{d.summary}</p>}
        {d.correlations?.length > 0 && (
          <div className="space-y-1 mb-2">
            {d.correlations.slice(0, 5).map((c, i) => (
              <div key={i} className="text-[10px] text-gray-400 flex items-center gap-1">
                <span className="text-[#3388ff]">→</span> {c}
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  // Scraper engine findings
  if (mod === 'scraper_engine' && d.scraper_name) {
    return (
      <div className="bg-[#12121a] rounded-lg p-3 border border-[#1e1e2e]">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-mono text-gray-400">Source: {d.scraper_name}</span>
        </div>
        {d.extracted && Object.keys(d.extracted).length > 0 && (
          <div className="grid grid-cols-2 gap-2 text-xs">
            {Object.entries(d.extracted).map(([k, v]) => (
              <div key={k}><span className="text-gray-500">{k}</span><div className="font-mono text-gray-300 truncate">{String(v)}</div></div>
            ))}
          </div>
        )}
      </div>
    )
  }

  // Geolocation
  if (finding.category === 'geolocation' && (d.lat || d.latitude)) {
    return (
      <div className="bg-[#12121a] rounded-lg p-3 border border-[#1e1e2e]">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs mb-2">
          {d.city && <div><span className="text-gray-500">City</span><div className="font-mono">{d.city}</div></div>}
          {d.country && <div><span className="text-gray-500">Country</span><div className="font-mono">{d.country}</div></div>}
          {d.isp && <div><span className="text-gray-500">ISP</span><div className="font-mono">{d.isp}</div></div>}
          {(d.as || d.org) && <div><span className="text-gray-500">ASN</span><div className="font-mono truncate">{d.as || d.org}</div></div>}
        </div>
        <div className="text-[10px] text-gray-600 italic">This is the mail server location, not the user's physical location.</div>
      </div>
    )
  }

  return null
}

