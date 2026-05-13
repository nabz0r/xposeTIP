import { useState, useEffect, useCallback } from 'react'
import { Search, Loader2, ExternalLink, ChevronDown, ChevronRight, X } from 'lucide-react'
import { launchDiscovery, getDiscovery, updateDiscoveryLead } from '../../lib/api'

const TYPE_COLORS = {
  email: 'bg-cyan-500/10 text-cyan-400',
  username: 'bg-purple-500/10 text-purple-400',
  url: 'bg-blue-500/10 text-blue-400',
  name: 'bg-amber-500/10 text-amber-400',
  document: 'bg-orange-500/10 text-orange-400',
  mention: 'bg-gray-500/10 text-gray-400',
}

function truncate(str, max) {
  if (!str) return ''
  return str.length > max ? str.slice(0, max) + '...' : str
}

export default function DiscoveredTab({ targetId, targetStatus }) {
  const [sessions, setSessions] = useState([])
  const [leads, setLeads] = useState([])
  const [loading, setLoading] = useState(true)
  const [launching, setLaunching] = useState(false)
  const [statusFilter, setStatusFilter] = useState(null)
  const [toast, setToast] = useState(null)
  const [expandedLead, setExpandedLead] = useState(null)
  const [events, setEvents] = useState([])
  const [showLog, setShowLog] = useState(false)

  const loadDiscovery = useCallback(async () => {
    try {
      const data = await getDiscovery(targetId, statusFilter)
      setSessions(data.sessions || [])
      setLeads(data.leads || [])
      setEvents(data.events || [])
    } catch (e) {
      console.error('Failed to load discovery:', e)
    } finally {
      setLoading(false)
    }
  }, [targetId, statusFilter])

  useEffect(() => { loadDiscovery() }, [loadDiscovery])

  // Poll while running
  useEffect(() => {
    const hasRunning = sessions.some(s => s.status === 'running')
    if (!hasRunning) return
    const interval = setInterval(loadDiscovery, 3000)
    return () => clearInterval(interval)
  }, [sessions, loadDiscovery])

  // Auto-dismiss toast
  useEffect(() => {
    if (!toast) return
    const t = setTimeout(() => setToast(null), 4000)
    return () => clearTimeout(t)
  }, [toast])

  const handleLaunch = async () => {
    setLaunching(true)
    try {
      await launchDiscovery(targetId)
      setToast({ type: 'success', message: 'Discovery launched' })
      await loadDiscovery()
    } catch (e) {
      setToast({ type: 'error', message: e.message || 'Failed to launch discovery' })
    } finally {
      setLaunching(false)
    }
  }

  const handleDismiss = async (leadId) => {
    try {
      await updateDiscoveryLead(targetId, leadId, 'dismissed')
      await loadDiscovery()
    } catch (e) {
      setToast({ type: 'error', message: 'Failed to dismiss lead' })
    }
  }

  const handleUndoDismiss = async (leadId) => {
    try {
      await updateDiscoveryLead(targetId, leadId, 'new')
      await loadDiscovery()
    } catch (e) {
      setToast({ type: 'error', message: 'Failed to undo dismiss' })
    }
  }

  const isRunning = sessions.some(s => s.status === 'running')
  const latestSession = sessions[0]
  const canLaunch = targetStatus === 'completed' && !isRunning && !launching

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48 text-gray-500 text-sm">
        <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading discovery data...
      </div>
    )
  }

  // Empty state
  if (!sessions.length && !leads.length) {
    return (
      <div className="space-y-4">
        {toast && (
          <div className={`p-3 rounded-lg text-sm ${toast.type === 'error' ? 'bg-red-500/10 text-red-400' : 'bg-[#00ff88]/10 text-[#00ff88]'}`}>
            {toast.message}
          </div>
        )}
        <div className="text-center py-16">
          <Search className="w-10 h-10 text-gray-700 mx-auto mb-4" />
          <h3 className="text-gray-400 text-sm mb-2">Web Discovery</h3>
          <p className="text-gray-600 text-xs max-w-md mx-auto mb-6">
            Explore the open web for intelligence not covered by the 124 scrapers.
            Uses behavioral fingerprint to generate targeted search queries.
          </p>
          <button onClick={handleLaunch} disabled={!canLaunch}
            className="px-4 py-2 bg-[#00ff88]/10 text-[#00ff88] rounded-lg text-sm border border-[#00ff88]/30 hover:bg-[#00ff88]/20 disabled:opacity-30 transition-colors">
            {launching ? <Loader2 className="w-4 h-4 animate-spin inline mr-2" /> : <Search className="w-4 h-4 inline mr-2" />}
            Launch Discovery
          </button>
        </div>
      </div>
    )
  }

  // Count by status for filter pills
  const counts = { all: leads.length, new: 0, dismissed: 0, ingested: 0 }
  leads.forEach(l => { counts[l.status] = (counts[l.status] || 0) + 1 })

  return (
    <div className="space-y-4">
      {/* Toast */}
      {toast && (
        <div className={`p-3 rounded-lg text-sm ${toast.type === 'error' ? 'bg-red-500/10 text-red-400' : 'bg-[#00ff88]/10 text-[#00ff88]'}`}>
          {toast.message}
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white">Web Discovery</h3>
        <button onClick={handleLaunch} disabled={!canLaunch}
          className="flex items-center gap-2 px-4 py-2 bg-[#00ff88]/10 text-[#00ff88] rounded-lg text-sm border border-[#00ff88]/30 hover:bg-[#00ff88]/20 disabled:opacity-30 transition-colors">
          {isRunning || launching
            ? <><Loader2 className="w-4 h-4 animate-spin" /> Discovering...</>
            : <><Search className="w-4 h-4" /> Launch Discovery</>}
        </button>
      </div>

      {/* Session stats */}
      {latestSession && (
        <div className="text-xs text-gray-500 flex items-center gap-2">
          {isRunning && <Loader2 className="w-3 h-3 animate-spin text-[#00ff88]" />}
          <span>
            {isRunning ? 'Running...' : 'Latest:'}{' '}
            {latestSession.queries_executed} queries · {latestSession.pages_fetched} pages · {latestSession.leads_found} leads
            {latestSession.status === 'completed' && latestSession.completed_at && (
              <> · {((new Date(latestSession.completed_at) - new Date(latestSession.started_at)) / 1000).toFixed(1)}s</>
            )}
          </span>
          {latestSession.status === 'error' && (
            <span className="text-red-400">Error: {latestSession.error_message}</span>
          )}
        </div>
      )}

      {/* Discovery Log */}
      {events.length > 0 && (
        <div>
          <button onClick={() => setShowLog(!showLog)}
            className="flex items-center gap-1 text-[11px] text-gray-600 hover:text-gray-400 transition-colors">
            {showLog ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
            Discovery Log ({events.length} events)
          </button>
          {(showLog || isRunning) && (
            <div className="mt-2 bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg p-3 max-h-48 overflow-y-auto font-mono text-[11px] text-gray-500 space-y-0.5">
              {events.map(ev => (
                <div key={ev.id}>
                  {ev.event_type === 'query' && <span>🔍 {truncate(ev.payload?.label || ev.payload?.query || '', 80)}</span>}
                  {ev.event_type === 'hit' && <span>📄 {truncate(ev.payload?.label || ev.payload?.title || '', 70)}</span>}
                  {ev.event_type === 'lead' && <span>💡 {ev.payload?.label || `${ev.payload?.type}: ${ev.payload?.value}`}</span>}
                  {!['query', 'hit', 'lead'].includes(ev.event_type) && <span>• {ev.event_type}: {truncate(ev.payload?.label || '', 60)}</span>}
                </div>
              ))}
              {!isRunning && latestSession?.status === 'completed' && (
                <div className="text-[#00ff88]">
                  ✅ Complete — {latestSession.queries_executed} queries · {latestSession.pages_fetched} pages · {latestSession.leads_found} leads
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Filter pills */}
      {leads.length > 0 && (
        <div className="flex gap-2">
          {[
            { key: null, label: 'All', count: counts.all },
            { key: 'new', label: 'New', count: counts.new },
            { key: 'dismissed', label: 'Dismissed', count: counts.dismissed },
            { key: 'ingested', label: 'Ingested', count: counts.ingested },
          ].map(f => (
            <button key={f.label} onClick={() => setStatusFilter(f.key)}
              className={`px-3 py-1 rounded-full text-xs border transition-colors ${
                statusFilter === f.key
                  ? 'bg-[#00ff88]/10 text-[#00ff88] border-[#00ff88]/30'
                  : 'bg-transparent text-gray-500 border-[#1e1e2e] hover:text-gray-300'
              }`}>
              {f.label} ({f.count})
            </button>
          ))}
        </div>
      )}

      {/* Leads */}
      <div className="space-y-2">
        {leads.map(lead => {
          const confColor = lead.confidence >= 0.8 ? 'text-[#00ff88]'
            : lead.confidence >= 0.5 ? 'text-amber-400' : 'text-gray-500'
          const isExpanded = expandedLead === lead.id

          return (
            <div key={lead.id} className={`bg-[#12121a] rounded-lg p-4 border transition-colors ${
              lead.status === 'dismissed' ? 'border-[#1e1e2e] opacity-50' : 'border-[#1e1e2e] hover:border-[#1e1e2e]'
            }`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 min-w-0">
                  <span className={`text-[10px] px-2 py-0.5 rounded font-mono uppercase shrink-0 ${TYPE_COLORS[lead.lead_type] || TYPE_COLORS.mention}`}>
                    {lead.lead_type}
                  </span>
                  <span className="text-sm text-white font-mono truncate">{lead.lead_value}</span>
                  <span className="text-[10px] text-gray-600 shrink-0">{lead.extractor_type}</span>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <span className={`text-xs font-mono ${confColor}`}>
                    {Math.round(lead.confidence * 100)}%
                  </span>
                  {lead.status === 'new' && (
                    <>
                      {/* Sprint H: Enrich / New Target buttons */}
                      <button onClick={() => handleDismiss(lead.id)}
                        className="text-xs text-gray-500 hover:text-red-400 transition-colors">
                        Dismiss
                      </button>
                    </>
                  )}
                  {lead.status === 'dismissed' && (
                    <>
                      <span className="text-xs text-gray-600">Dismissed</span>
                      <button onClick={() => handleUndoDismiss(lead.id)}
                        className="text-xs text-gray-600 hover:text-[#00ff88] transition-colors">
                        Undo
                      </button>
                    </>
                  )}
                  {lead.status === 'ingested' && (
                    <span className="text-xs text-[#00ff88]">Ingested</span>
                  )}
                </div>
              </div>

              {/* Source + chain toggle */}
              <div className="mt-2 flex items-center gap-3 text-[11px] text-gray-600">
                <span>via {lead.extractor_type}</span>
                {lead.source_url && (
                  <a href={lead.source_url} target="_blank" rel="noreferrer"
                    className="hover:text-gray-400 truncate max-w-[300px] inline-flex items-center gap-1">
                    {truncate(lead.source_url, 60)} <ExternalLink className="w-3 h-3 shrink-0" />
                  </a>
                )}
                {lead.discovery_chain?.length > 0 && (
                  <button onClick={() => setExpandedLead(isExpanded ? null : lead.id)}
                    className="text-gray-600 hover:text-gray-400 flex items-center gap-1">
                    {isExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                    {isExpanded ? 'Hide' : 'Show'} chain
                  </button>
                )}
              </div>

              {/* Discovery chain */}
              {isExpanded && lead.discovery_chain && (
                <div className="mt-3 pl-4 border-l border-[#1e1e2e] space-y-1">
                  {lead.discovery_chain.map((step, i) => (
                    <div key={i} className="text-[11px] text-gray-600">
                      {step.step === 'query' && <span>🔍 {truncate(step.value, 80)}</span>}
                      {step.step === 'hit' && <span>📄 {step.title || truncate(step.url, 60)}</span>}
                      {step.step === 'extract' && <span>💡 {step.extractor}: {step.value}</span>}
                      {step.step === 'follow' && <span>↗️ {truncate(step.url, 60)}</span>}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* No leads for current filter */}
      {leads.length === 0 && sessions.length > 0 && !isRunning && (
        <div className="text-center py-8 text-gray-600 text-xs">
          {statusFilter ? `No ${statusFilter} leads.` : 'No leads found in the latest discovery session.'}
        </div>
      )}
    </div>
  )
}
