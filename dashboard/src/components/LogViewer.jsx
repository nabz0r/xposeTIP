import { useEffect, useState, useRef } from 'react'
import { RefreshCw, Trash2, Pause, Play, Filter } from 'lucide-react'
import { getLogs, clearLogs } from '../lib/api'

const LEVEL_COLORS = {
  DEBUG: '#666688',
  INFO: '#3388ff',
  WARNING: '#ffcc00',
  ERROR: '#ff8800',
  CRITICAL: '#ff2244',
}

const CONTAINER_COLORS = {
  api: '#00ff88',
  worker: '#3388ff',
  beat: '#ffcc00',
}

export default function LogViewer() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [filterLevel, setFilterLevel] = useState('')
  const [filterContainer, setFilterContainer] = useState('')
  const [limit, setLimit] = useState(200)
  const bottomRef = useRef(null)
  const intervalRef = useRef(null)

  async function fetchLogs() {
    try {
      const params = new URLSearchParams()
      params.set('limit', limit)
      if (filterLevel) params.set('level', filterLevel)
      if (filterContainer) params.set('container', filterContainer)
      const data = await getLogs(params.toString())
      setLogs(data.logs || [])
    } catch (err) {
      console.error('Failed to fetch logs:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLogs()
  }, [filterLevel, filterContainer, limit])

  useEffect(() => {
    if (autoRefresh) {
      intervalRef.current = setInterval(fetchLogs, 3000)
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [autoRefresh, filterLevel, filterContainer, limit])

  async function handleClear() {
    if (!confirm('Clear all logs from the buffer?')) return
    try {
      await clearLogs()
      setLogs([])
    } catch (err) {
      alert('Failed to clear logs: ' + err.message)
    }
  }

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <select value={filterLevel} onChange={e => setFilterLevel(e.target.value)}
            className="bg-[#1e1e2e] border border-[#2a2a3e] rounded-lg px-3 py-1.5 text-xs text-gray-300 focus:outline-none focus:border-[#00ff88]/50">
            <option value="">All Levels</option>
            {['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'].map(l => (
              <option key={l} value={l}>{l}</option>
            ))}
          </select>
          <select value={filterContainer} onChange={e => setFilterContainer(e.target.value)}
            className="bg-[#1e1e2e] border border-[#2a2a3e] rounded-lg px-3 py-1.5 text-xs text-gray-300 focus:outline-none focus:border-[#00ff88]/50">
            <option value="">All Containers</option>
            {['api', 'worker', 'beat'].map(c => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
          <select value={limit} onChange={e => setLimit(Number(e.target.value))}
            className="bg-[#1e1e2e] border border-[#2a2a3e] rounded-lg px-3 py-1.5 text-xs text-gray-300 focus:outline-none focus:border-[#00ff88]/50">
            {[50, 100, 200, 500, 1000].map(n => (
              <option key={n} value={n}>Last {n}</option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">{logs.length} entries</span>
          <button onClick={() => setAutoRefresh(!autoRefresh)}
            className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border transition-colors ${
              autoRefresh
                ? 'border-[#00ff88]/30 text-[#00ff88] bg-[#00ff88]/10'
                : 'border-[#1e1e2e] text-gray-400 hover:text-white'
            }`}>
            {autoRefresh ? <Pause className="w-3 h-3" /> : <Play className="w-3 h-3" />}
            {autoRefresh ? 'Live' : 'Paused'}
          </button>
          <button onClick={fetchLogs}
            className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-white border border-[#1e1e2e] rounded-lg px-3 py-1.5">
            <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} /> Refresh
          </button>
          <button onClick={handleClear}
            className="flex items-center gap-1.5 text-xs text-[#ff2244] hover:text-[#ff4466] border border-[#1e1e2e] rounded-lg px-3 py-1.5">
            <Trash2 className="w-3 h-3" /> Clear
          </button>
        </div>
      </div>

      {/* Log entries */}
      <div className="bg-[#0a0a0f] border border-[#1e1e2e] rounded-xl overflow-hidden">
        <div className="max-h-[600px] overflow-y-auto font-mono text-xs leading-relaxed p-1">
          {logs.length === 0 && (
            <div className="text-center text-gray-500 py-12">
              {loading ? 'Loading logs...' : (
                <>
                  <span className="text-lg">No logs yet</span>
                  <p className="text-xs mt-1">Run a scan to generate log entries. Logs appear in real-time.</p>
                </>
              )}
            </div>
          )}
          {[...logs].reverse().map((entry, i) => (
            <div key={i} className="flex gap-2 px-3 py-0.5 hover:bg-white/[0.02] group">
              {/* Timestamp */}
              <span className="text-gray-600 shrink-0 w-[190px]">
                {entry.ts ? new Date(entry.ts).toLocaleString(undefined, {
                  hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit',
                  fractionalSecondDigits: 3, year: 'numeric', month: '2-digit', day: '2-digit',
                }) : ''}
              </span>
              {/* Container badge */}
              <span className="shrink-0 w-[52px] text-center rounded px-1"
                style={{ color: CONTAINER_COLORS[entry.container] || '#666688' }}>
                {entry.container || '?'}
              </span>
              {/* Level badge */}
              <span className="shrink-0 w-[70px] text-center rounded px-1 font-semibold"
                style={{ color: LEVEL_COLORS[entry.level] || '#666688' }}>
                {entry.level || '?'}
              </span>
              {/* Logger */}
              <span className="text-gray-500 shrink-0 max-w-[180px] truncate">
                {entry.logger || ''}
              </span>
              {/* Message */}
              <span className="text-gray-300 break-all">{entry.message}</span>
              {/* Task/module extras */}
              {(entry.task_id || entry.module) && (
                <span className="text-gray-600 shrink-0 ml-auto">
                  {entry.module && <span className="text-[#00ff88]/50">[{entry.module}]</span>}
                  {entry.task_id && <span className="text-[#3388ff]/50 ml-1">{entry.task_id.slice(0, 8)}</span>}
                </span>
              )}
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
      </div>
    </div>
  )
}
