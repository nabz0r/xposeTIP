import React, { useEffect, useState, useCallback, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Radar, CheckCircle, AlertTriangle, XCircle, ArrowRightLeft, FileDown } from 'lucide-react'
import { getTarget, getFindings, getScans, createScan, getModules, getScan, getGraph, patchFinding, getTargetSources, getAccounts, startOAuth, auditAccount, disconnectAccount, getFingerprint, getFingerprintHistory, getTargetProfile, cancelScan, getWorkspaces, moveTarget, getScraperProgress } from '../lib/api'
import { applyPreset } from '../lib/findingFilters'
import { normalizeModuleStatus } from '../lib/moduleProgress'
import IdentityGraph from '../components/IdentityGraph'
import LocationMap from '../components/LocationMap'
import ProfileHeader from '../components/ProfileHeader'
import OverviewTab from './tabs/OverviewTab'
import ScansTab from './tabs/ScansTab'
import FindingsHubTab from './tabs/FindingsHubTab'
import GraphHubTab from './tabs/GraphHubTab'
import SourcesHubTab from './tabs/SourcesHubTab'
import SanctionsAlert from '../components/target/SanctionsAlert'

// S149: shared predicate for "scan is still working" — covers both the active
// scrape window (status running/queued) and the cascade window (status completed
// but cascade_state still gathering/computing/similarity). Used by the polling
// effect AND the live progress UI block — both must agree, else the polling
// stops while the cascade UI still claims work-in-progress.
const isScanInProgress = (s) =>
  s.status === 'running' ||
  s.status === 'queued' ||
  (s.status === 'completed' && s.cascade_state && s.cascade_state !== 'done' && s.cascade_state !== 'failed')

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
  const [subTab, setSubTab] = useState({ findings: 'all', graph: 'graph', sources: 'sources' })

  const navigateTo = (tab, sub = null) => {
    setActiveTab(tab)
    if (sub) setSubTab(prev => ({ ...prev, [tab]: sub }))
  }

  const setSubTabFor = (top) => (key) => setSubTab(prev => ({ ...prev, [top]: key }))

  // S157 compatibility shim: maps old flat-tab names (still used by
  // OverviewTab deep-links) to the new {top, sub} structure. Lets
  // OverviewTab stay unchanged.
  const setActiveTabCompat = (oldName) => {
    if (['exposure', 'breaches', 'usernames', 'photos', 'locations', 'discovered'].includes(oldName)) {
      navigateTo('findings', oldName)
    } else if (oldName === 'timeline') {
      navigateTo('graph', 'timeline')
    } else if (oldName === 'accounts') {
      navigateTo('sources', 'accounts')
    } else {
      navigateTo(oldName)
    }
  }
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
  const [presetFilter, setPresetFilter] = useState('all')
  const [findingsLimit, setFindingsLimit] = useState(20)
  // Score animation
  const [animScore, setAnimScore] = useState(0)
  const pollRef = useRef(null)
  // Move target
  const [workspaces, setWorkspaces] = useState([])
  const [showMoveMenu, setShowMoveMenu] = useState(false)
  const [scraperProgress, setScraperProgress] = useState(null)

  const load = useCallback(async () => {
    try {
      const [t, f, s] = await Promise.all([
        getTarget(id),
        getFindings(`target_id=${id}&per_page=200`),
        getScans(`target_id=${id}`),
      ])
      setTarget(t)
      setFindings(f.items || [])
      setScans(s.items || [])
      getTargetProfile(id).then(setProfile).catch(() => setProfile(null))
    } catch {}
  }, [id])

  useEffect(() => { load() }, [load])

  // S192 Bug 8: re-fetch on tab visibility change so findings stay fresh
  // when user returns to a TargetDetail page after the scan finished in
  // the background (load() at mount only ran once, post-scan poll's
  // re-fetch only fires if a scan was running when the page was mounted).
  useEffect(() => {
    const onVisible = () => {
      if (document.visibilityState === 'visible') {
        load()
      }
    }
    document.addEventListener('visibilitychange', onVisible)
    return () => document.removeEventListener('visibilitychange', onVisible)
  }, [load])

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

  // Poll while scanning
  useEffect(() => {
    const runningScans = scans.filter(isScanInProgress)
    if (!runningScans.length) {
      if (pollRef.current) clearInterval(pollRef.current)
      return
    }
    pollRef.current = setInterval(async () => {
      try {
        const updated = await Promise.all(runningScans.map(s => getScan(s.id)))
        const done = updated.every(s => {
          if (s.status === 'running' || s.status === 'queued') return false
          // Status is completed/failed/cancelled. Keep polling if cascade still working.
          // cascade_state === null/undefined means legacy scan (pre-S134) — treat as done.
          return s.cascade_state == null || s.cascade_state === 'done' || s.cascade_state === 'failed'
        })
        setScans(prev => prev.map(s => {
          const u = updated.find(x => x.id === s.id)
          return u || s
        }))
        // Fetch scraper-level progress for richer display
        const runningScanObj = updated.find(s => s.status === 'running')
        if (normalizeModuleStatus(runningScanObj?.module_progress?.scraper_engine) === 'running') {
          try { const sp = await getScraperProgress(runningScanObj.id); setScraperProgress(sp) } catch {}
        } else {
          setScraperProgress(null)
        }
        getFingerprint(id).then(setFingerprint).catch(() => {})

        if (done) {
          clearInterval(pollRef.current)
          const [t, f] = await Promise.all([getTarget(id), getFindings(`target_id=${id}&per_page=200`)])
          setTarget(t)
          const newFindings = f.items || []
          const newCount = newFindings.length - findings.length
          setFindings(newFindings)
          getFingerprint(id).then(setFingerprint).catch(() => {})
          getFingerprintHistory(id).then(d => setFpHistory(d.snapshots || [])).catch(() => {})
          getTargetProfile(id).then(setProfile).catch(() => {})
          getGraph(id).then(setGraphData).catch(() => {})
          const failed = updated.filter(s => s.status === 'failed')
          if (failed.length > 0) {
            setToast({ type: 'error', message: `Scan failed: ${failed[0].error_log || 'Unknown error'}` })
          } else {
            setToast({ type: 'success', message: `Scan completed — ${newCount > 0 ? newCount : 0} new findings` })
          }
          setTimeout(() => setToast(null), 5000)

          // S135 follow-up: cascade can transition gathering -> done in <3s
          // (faster than poll interval). One extra fetch after 2s guarantees
          // we observe the final state even on fast cascades — block hides
          // without requiring page refresh.
          setTimeout(async () => {
            try {
              const finalScans = await Promise.all(runningScans.map(s => getScan(s.id)))
              setScans(prev => prev.map(s => finalScans.find(x => x.id === s.id) || s))
            } catch {
              // Silent — if the second fetch fails, the user can refresh
            }
          }, 2000)
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

  // Load connected accounts — S157: 'accounts' was a top tab pre-S157; now
  // it's a sub-pill under 'sources'. Load when we enter sources (either sub)
  // or overview, since overview also surfaces account hints.
  useEffect(() => {
    if (activeTab === 'sources' || activeTab === 'overview') {
      getAccounts(id).then(d => setAccounts(d.items || [])).catch(() => {})
    }
  }, [activeTab, id])

  useEffect(() => {
    getModules().then(m => {
      setModules(m)
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

  // S120: handle "View all N →" clicks from RiskSignalsBlock
  const handleRiskSignalViewAll = (preset) => {
    setPresetFilter(preset)
    setSevFilter('all')
    setModFilter('all')
    setStatusFilter('all')
    navigateTo('findings', 'all')
  }

  // Filtered findings
  const filteredFindings = applyPreset(findings, presetFilter).filter(f => {
    if (sevFilter !== 'all' && f.severity !== sevFilter) return false
    if (modFilter !== 'all' && f.module !== modFilter) return false
    if (statusFilter !== 'all' && f.status !== statusFilter) return false
    return true
  })

  const uniqueModules = [...new Set(findings.map(f => f.module))]

  // Overview data
  const breachFindings = findings.filter(f => (f.category === 'breach' || f.category === 'breach_risk') && !(f.title || '').toLowerCase().includes('not configured') && !(f.title || '').toLowerCase().includes('api key'))
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
          <ProfileHeader target={target} findings={findings} animScore={animScore} profileData={profile} onTargetUpdate={setTarget} />
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
          <button
            onClick={async () => { const token = localStorage.getItem("xpose_token"); const res = await fetch(`/api/v1/targets/${id}/report/pdf`, { headers: { Authorization: `Bearer ${token}` } }); const blob = await res.blob(); const url = URL.createObjectURL(blob); const a = document.createElement("a"); a.href = url; a.download = `xposeTIP_report.pdf`; a.click(); URL.revokeObjectURL(url); }}
            className="flex items-center gap-1.5 text-xs px-3 py-2.5 border border-[#1e1e2e] rounded-lg text-[#00D4AA] hover:bg-[#00D4AA]/10 transition-colors"
            title="Download PDF Report"
          >
            <FileDown className="w-3.5 h-3.5" /> PDF
          </button>
          <button onClick={() => setShowScanModal(true)}
            className="flex items-center gap-2 bg-[#00ff88] text-black font-semibold rounded-lg px-4 py-2.5 text-sm hover:bg-[#00ff88]/90">
            <Radar className="w-4 h-4" /> New Scan
          </button>
        </div>
      </div>

      {/* Live scan progress — S134 extended to include cascade window, S149 unified predicate */}
      {scans.some(isScanInProgress) && (() => {
        const runningScan = scans.find(isScanInProgress)
        const progress = runningScan?.module_progress || {}
        const total = Object.keys(progress).length
        const completed = Object.values(progress).map(normalizeModuleStatus).filter(s => s === 'completed' || s === 'failed' || s === 'skipped').length
        // Enhanced percentage: interpolate scraper sub-progress
        let pct = total > 0 ? Math.round((completed / total) * 100) : 0
        if (scraperProgress && total > 0 && normalizeModuleStatus(progress.scraper_engine) === 'running') {
          const scraperFrac = (scraperProgress.current || 0) / (scraperProgress.total || 120)
          pct = Math.round(((completed + scraperFrac) / total) * 100)
        }
        // S134: during cascade, scraper modules are done — show cascade-based pct
        if (runningScan?.status === 'completed' && runningScan?.cascade_state) {
          const cascadeMap = { gathering: 75, computing: 85, similarity: 95, done: 100 }
          pct = cascadeMap[runningScan.cascade_state] ?? pct
        }
        return (
          <div className="bg-[#12121a] border border-[#00ff88]/20 rounded-xl p-4 animate-pulse-subtle">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-[#00ff88] animate-pulse" />
                <span className="text-sm font-medium">
                  {runningScan.status === 'completed'
                    ? `Computing intelligence for ${target.email}...`
                    : `Scanning ${target.email}...`}
                </span>
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
            {scraperProgress && normalizeModuleStatus(progress.scraper_engine) === 'running' && (
              <div className="flex items-center gap-2 mb-2 text-xs text-gray-500">
                <span className="font-mono text-[#3388ff]">
                  {scraperProgress.current || 0}/{scraperProgress.total || 120}
                </span>
                <span>scrapers</span>
                {scraperProgress.current_name && (
                  <span className="text-gray-400 truncate">— {scraperProgress.current_name}</span>
                )}
              </div>
            )}
            {runningScan.status === 'completed' && runningScan.cascade_state && runningScan.cascade_state !== 'done' && (
              <div className="mb-3 px-3 py-2 rounded bg-[#0a0a0f] border border-[#1e1e2e]">
                <div className="text-[10px] uppercase tracking-wider text-gray-500 mb-2">Computing intelligence</div>
                <div className="flex items-center gap-2 text-xs">
                  {[
                    { key: 'gathering', label: 'Gather' },
                    { key: 'computing', label: 'Compute' },
                    { key: 'similarity', label: 'Similarity' },
                  ].map(({ key, label }, idx, arr) => {
                    const states = ['gathering', 'computing', 'similarity', 'done']
                    const currentIdx = states.indexOf(runningScan.cascade_state)
                    const stepIdx = states.indexOf(key)
                    const isDone = stepIdx < currentIdx
                    const isActive = stepIdx === currentIdx
                    return (
                      <div key={key} className="flex items-center gap-1.5">
                        {isDone ? <CheckCircle className="w-3 h-3 text-[#00ff88]" /> :
                         isActive ? <Radar className="w-3 h-3 text-[#3388ff] animate-spin" /> :
                         <div className="w-3 h-3 rounded-full border border-gray-600" />}
                        <span className={isDone ? 'text-[#00ff88]' : isActive ? 'text-[#3388ff]' : 'text-gray-600'}>{label}</span>
                        {idx < arr.length - 1 && <span className="text-gray-700">›</span>}
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

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

      {/* Sanctions/PEP Alert Banner */}
      <SanctionsAlert findings={findings} />

      {/* Tabs (S157: 13 → 5 with sub-pill hubs) */}
      <div className="flex gap-1 border-b border-[#1e1e2e] overflow-x-auto">
        {[
          { key: 'overview', label: 'Overview' },
          { key: 'findings', label: 'Findings', count: findings.length },
          { key: 'graph',    label: 'Graph' },
          { key: 'sources',  label: 'Sources' },
          { key: 'scans',    label: 'Scans', count: scans.length },
        ].map(tab => (
          <button key={tab.key} onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 text-sm transition-colors whitespace-nowrap ${
              activeTab === tab.key ? 'text-[#00ff88] border-b-2 border-[#00ff88]' : 'text-gray-400 hover:text-white'
            }`}>
            {tab.label}{tab.count != null ? <span className="ml-1 text-xs font-mono opacity-70">({tab.count})</span> : null}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === 'overview' && (
        <OverviewTab
          target={target} findings={findings} profile={profile}
          fingerprint={fingerprint} fpHistory={fpHistory} sourcesData={sourcesData}
          socialFindings={socialFindings} breachFindings={breachFindings}
          geoFindings={geoFindings} riskAssessment={riskAssessment}
          remediations={remediations} criticalCount={criticalCount}
          setActiveTab={setActiveTabCompat} setShowScanModal={setShowScanModal}
          onRiskSignalViewAll={handleRiskSignalViewAll}
        />
      )}

      {activeTab === 'findings' && (
        <FindingsHubTab
          activeSub={subTab.findings} setActiveSub={setSubTabFor('findings')}
          target={target} findings={findings} filteredFindings={filteredFindings}
          expanded={expanded} setExpanded={setExpanded}
          sevFilter={sevFilter} setSevFilter={setSevFilter}
          modFilter={modFilter} setModFilter={setModFilter}
          statusFilter={statusFilter} setStatusFilter={setStatusFilter}
          presetFilter={presetFilter} setPresetFilter={setPresetFilter}
          findingsLimit={findingsLimit} setFindingsLimit={setFindingsLimit}
          uniqueModules={uniqueModules} load={load} patchFinding={patchFinding}
          targetId={id} profile={profile}
          socialFindings={socialFindings} breachFindings={breachFindings}
          geoFindings={geoFindings} graphData={graphData}
        />
      )}

      {activeTab === 'graph' && (
        <GraphHubTab
          activeSub={subTab.graph} setActiveSub={setSubTabFor('graph')}
          graphData={graphData} profile={profile} findings={findings}
        />
      )}

      {activeTab === 'sources' && (
        <SourcesHubTab
          activeSub={subTab.sources} setActiveSub={setSubTabFor('sources')}
          sourcesData={sourcesData}
          id={id} socialFindings={socialFindings} accounts={accounts}
          setAccounts={setAccounts} auditingAccount={auditingAccount}
          setAuditingAccount={setAuditingAccount} toast={toast} setToast={setToast}
          load={load} startOAuth={startOAuth} auditAccount={auditAccount}
          disconnectAccount={disconnectAccount}
        />
      )}

      {activeTab === 'scans' && (
        <ScansTab
          scans={scans} modules={modules} load={load}
          showScanModal={showScanModal} setShowScanModal={setShowScanModal}
          selectedModules={selectedModules} setSelectedModules={setSelectedModules}
          scanning={scanning} handleScan={handleScan}
        />
      )}

      {/* Toast */}
      {toast && (
        <div className={`fixed bottom-6 right-6 z-50 px-4 py-3 rounded-lg text-sm shadow-lg border ${
          toast.type === 'success' ? 'bg-[#00ff88]/10 border-[#00ff88]/30 text-[#00ff88]' : 'bg-[#ff2244]/10 border-[#ff2244]/30 text-[#ff2244]'
        }`}>
          {toast.message}
        </div>
      )}

      {/* Scan Modal (rendered by ScansTab but needs to be here for non-scans tab access) */}
      {activeTab !== 'scans' && showScanModal && (
        <ScansTab
          scans={[]} modules={modules} load={load}
          showScanModal={showScanModal} setShowScanModal={setShowScanModal}
          selectedModules={selectedModules} setSelectedModules={setSelectedModules}
          scanning={scanning} handleScan={handleScan}
        />
      )}
    </div>
  )
}
