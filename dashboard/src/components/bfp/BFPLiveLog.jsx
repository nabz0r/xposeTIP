import { useEffect, useState } from 'react'

// Live trust-log widget (S173). Polls /api/v1/bfp/recent_anchors every 60s,
// renders the latest N Merkle root commits as a CT-log-style monospace table.
// Geek-friendly: full 64-char SHA3-256 hash, num_leaves, absolute ISO UTC time.
// No workspace_id field — privacy + visual cleanliness.

const POLL_MS = 60_000
const ROW_LIMIT = 20

export default function BFPLiveLog() {
  const [anchors, setAnchors] = useState([])
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    const base = import.meta.env.VITE_API_URL || '/api/v1'
    const ctrl = new AbortController()
    let cancelled = false

    async function poll() {
      try {
        const res = await fetch(
          `${base}/bfp/recent_anchors?limit=${ROW_LIMIT}`,
          { signal: ctrl.signal }
        )
        if (!res.ok) return
        const data = await res.json()
        if (cancelled) return
        setAnchors(Array.isArray(data.anchors) ? data.anchors : [])
        setLoaded(true)
      } catch {
        // Silent — public marketing page, no error banners.
      }
    }

    poll() // initial fetch on mount
    const interval = setInterval(poll, POLL_MS)
    return () => {
      cancelled = true
      ctrl.abort()
      clearInterval(interval)
    }
  }, [])

  return (
    <div className="max-w-5xl mx-auto px-6">
      <div className="text-center mb-10">
        <div className="text-xs font-mono text-[#00ff88]/70 uppercase tracking-wider mb-3">
          Live trust log
        </div>
        <h2 className="text-3xl md:text-4xl font-bold mb-4 font-['Instrument_Sans',sans-serif]">
          Append-only, in real time
        </h2>
        <p className="text-sm text-gray-500 max-w-2xl mx-auto">
          Merkle root snapshots committed every 5 minutes per workspace. Each row is a
          SHA3-256 tamper-evident anchor over that workspace&apos;s claims at that instant.
        </p>
      </div>

      <div className="bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg p-4 font-mono text-xs overflow-x-auto">
        {!loaded ? (
          <div className="text-gray-600 text-center py-6">Loading recent anchors…</div>
        ) : anchors.length === 0 ? (
          <div className="text-gray-600 text-center py-6">No anchors yet.</div>
        ) : (
          <table className="w-full whitespace-nowrap">
            <thead>
              <tr className="text-gray-600 text-[10px] uppercase tracking-wider border-b border-[#1e1e2e]">
                <th className="text-left py-2 pr-4">root_hash (sha3-256)</th>
                <th className="text-right px-4">leaves</th>
                <th className="text-right pl-4">computed_at (utc)</th>
              </tr>
            </thead>
            <tbody>
              {anchors.map((a) => (
                <tr
                  key={`${a.root_hash}-${a.computed_at}`}
                  className="border-b border-[#13131c] last:border-0 hover:bg-[#0d0d14]"
                >
                  <td className="text-[#00ff88]/80 py-2 pr-4">{a.root_hash}</td>
                  <td className="text-right text-gray-300 px-4">
                    {a.num_leaves.toLocaleString()}
                  </td>
                  <td className="text-right text-gray-500 pl-4">{a.computed_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="text-center text-xs text-gray-600 mt-4">
        Polling every 60s · Reference implementation, all workspaces
      </div>
    </div>
  )
}
