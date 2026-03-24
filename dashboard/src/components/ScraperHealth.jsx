import { useEffect, useState, useCallback } from 'react'
import { RefreshCw, ChevronDown, ChevronRight } from 'lucide-react'
import { getScraperHealth } from '../lib/api'

const HOLEHE_BLACKLIST = new Set([
  'soundcloud', 'rocketreach', 'evernote', 'samsung',
  'github', 'deliveroo', 'crevado', 'pinterest', 'snapchat',
])

function healthColor(pct) {
  if (pct === null || pct === undefined) return '#666688'
  if (pct >= 80) return '#00ff88'
  if (pct >= 50) return '#ffcc00'
  return '#ff2244'
}

function healthIcon(pct) {
  if (pct === null || pct === undefined) return '\u26AA'
  if (pct >= 80) return '\uD83D\uDFE2'
  if (pct >= 50) return '\uD83D\uDFE1'
  return '\uD83D\uDD34'
}

export default function ScraperHealth() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [expanded, setExpanded] = useState(new Set())
  const [showDisabled, setShowDisabled] = useState(false)
  const [lastRefresh, setLastRefresh] = useState(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const res = await getScraperHealth()
      setData(res.items || [])
      setLastRefresh(new Date())
    } catch {
      setData([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
    const interval = setInterval(refresh, 30000)
    return () => clearInterval(interval)
  }, [refresh])

  const toggle = (name) => {
    setExpanded(prev => {
      const next = new Set(prev)
      if (next.has(name)) next.delete(name)
      else next.add(name)
      return next
    })
  }

  const totalCalls = data.reduce((sum, d) => sum + (d.calls_24h || 0), 0)
  const totalSuccess = data.reduce((sum, d) => sum + (d.success_24h || 0), 0)
  const overallPct = totalCalls > 0 ? Math.round(totalSuccess / totalCalls * 100) : null

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-400">
            Scraper Health (Last 24h)
          </h3>
          {overallPct !== null && (
            <span className="text-xs font-mono px-2 py-0.5 rounded-full" style={{
              backgroundColor: healthColor(overallPct) + '20',
              color: healthColor(overallPct),
            }}>
              {overallPct}% overall
            </span>
          )}
          <span className="text-[10px] text-gray-600">
            {totalCalls} calls / {data.length} scrapers
          </span>
        </div>
        <div className="flex items-center gap-2">
          <label className="flex items-center gap-1.5 text-[10px] text-gray-500 cursor-pointer">
            <input type="checkbox" checked={showDisabled} onChange={e => setShowDisabled(e.target.checked)}
              className="rounded border-gray-600 bg-transparent text-[#00ff88] focus:ring-0 focus:ring-offset-0 w-3 h-3" />
            Show blacklisted
          </label>
          {lastRefresh && (
            <span className="text-[10px] text-gray-600">{lastRefresh.toLocaleTimeString()}</span>
          )}
          <button onClick={refresh} disabled={loading}
            className="p-1.5 rounded-lg border border-[#1e1e2e] text-gray-400 hover:text-[#00ff88] hover:border-[#00ff88]/30 transition-colors disabled:opacity-50">
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Blacklisted modules */}
      {showDisabled && (
        <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl overflow-hidden divide-y divide-[#1e1e2e]">
          {[...HOLEHE_BLACKLIST].sort().map(name => (
            <div key={name} className="flex items-center justify-between px-5 py-3 opacity-50">
              <div className="flex items-center gap-3">
                <span>{'\uD83D\uDC80'}</span>
                <span className="text-sm font-mono text-gray-400">holehe:{name}</span>
              </div>
              <span className="text-[10px] text-gray-600 bg-[#1e1e2e] px-2 py-0.5 rounded">BLACKLISTED</span>
            </div>
          ))}
        </div>
      )}

      {/* Active scrapers */}
      {data.length === 0 && !loading && (
        <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-8 text-center text-gray-500 text-sm">
          No scraper activity in the last 24 hours. Run a scan to generate health data.
        </div>
      )}

      {data.length > 0 && (
        <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl overflow-hidden divide-y divide-[#1e1e2e]">
          {data.map(d => {
            const isExpanded = expanded.has(d.scraper)
            const pct = d.health_pct
            return (
              <div key={d.scraper}>
                <div className="flex items-center justify-between px-5 py-3 cursor-pointer hover:bg-white/[0.02] transition-colors"
                  onClick={() => toggle(d.scraper)}>
                  <div className="flex items-center gap-3 min-w-0">
                    {isExpanded ? <ChevronDown className="w-3 h-3 text-gray-500 shrink-0" /> : <ChevronRight className="w-3 h-3 text-gray-500 shrink-0" />}
                    <span>{healthIcon(pct)}</span>
                    <span className="text-sm font-mono truncate">{d.scraper}</span>
                  </div>
                  <div className="flex items-center gap-4 shrink-0">
                    {/* Health percentage */}
                    <span className="text-sm font-mono font-semibold" style={{ color: healthColor(pct) }}>
                      {pct !== null ? `${pct}%` : '-'}
                    </span>
                    {/* Success/Total */}
                    <span className="text-xs text-gray-500 font-mono">
                      {d.success_24h}/{d.calls_24h}
                    </span>
                    {/* Status codes inline */}
                    <div className="flex gap-1.5">
                      {Object.entries(d.status_codes || {}).sort().map(([code, count]) => (
                        <span key={code} className="text-[10px] font-mono px-1.5 py-0.5 rounded" style={{
                          backgroundColor: code.startsWith('2') ? '#00ff8815' : code === '404' || code === '410' ? '#66668815' : code.startsWith('4') ? '#ff224415' : '#ffcc0015',
                          color: code.startsWith('2') ? '#00ff88' : code === '404' || code === '410' ? '#666688' : code.startsWith('4') ? '#ff2244' : '#ffcc00',
                        }}>
                          {code}&times;{count}
                        </span>
                      ))}
                    </div>
                    {/* Avg response time */}
                    <span className="text-xs text-gray-500 font-mono w-16 text-right">
                      {d.avg_response_ms > 0 ? `${(d.avg_response_ms / 1000).toFixed(1)}s` : '-'}
                    </span>
                    {/* Cache hits */}
                    {d.cache_hits_24h > 0 && (
                      <span className="text-[10px] text-gray-500 font-mono">
                        cache: {d.cache_hits_24h}
                      </span>
                    )}
                  </div>
                </div>
                {/* Expanded detail */}
                {isExpanded && (
                  <div className="px-5 pb-3 pt-0 ml-9 text-xs text-gray-400 space-y-1">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      <div><span className="text-gray-600">Calls:</span> {d.calls_24h}</div>
                      <div><span className="text-gray-600">Success:</span> <span className="text-[#00ff88]">{d.success_24h}</span></div>
                      <div><span className="text-gray-600">Errors:</span> <span className="text-[#ff2244]">{d.errors_24h}</span></div>
                      <div><span className="text-gray-600">Cache hits:</span> {d.cache_hits_24h}</div>
                      <div><span className="text-gray-600">Avg response:</span> {d.avg_response_ms}ms</div>
                      <div><span className="text-gray-600">Last call:</span> {d.last_call ? new Date(d.last_call).toLocaleTimeString() : '-'}</div>
                      <div><span className="text-gray-600">Last success:</span> {d.last_success ? new Date(d.last_success).toLocaleTimeString() : '-'}</div>
                    </div>
                    {/* Status code breakdown */}
                    <div className="flex flex-wrap gap-2 mt-2">
                      {Object.entries(d.status_codes || {}).sort().map(([code, count]) => (
                        <div key={code} className="flex items-center gap-1.5 px-2 py-1 rounded bg-[#0a0a0f]">
                          <span className="font-mono font-semibold" style={{
                            color: code.startsWith('2') ? '#00ff88' : code === '404' || code === '410' ? '#666688' : code.startsWith('4') ? '#ff2244' : '#ffcc00',
                          }}>{code}</span>
                          {(code === '404' || code === '410') && (
                            <span className="text-[9px] text-gray-600">(not found)</span>
                          )}
                          <span className="text-gray-500">&times; {count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
