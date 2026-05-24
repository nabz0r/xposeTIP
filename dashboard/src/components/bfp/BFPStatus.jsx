import { useEffect, useState } from 'react'

// Truly static protocol constants — never change per release.
const STATIC_PROTOCOL_CONSTS = [
  { label: 'License', value: 'AGPL-3.0' },
  { label: 'Crypto suite', value: 'NIST 2024 PQC' },
]

// Em-dash fallback for live stats on fetch failure (DB down, network, etc.).
// Public marketing page MUST NOT show error banners — silent degradation.
function formatN(n) {
  if (n === null || n === undefined) return '—'
  return n.toLocaleString()
}

function formatS(s) {
  if (s === null || s === undefined) return '—'
  return s
}

export default function BFPStatus() {
  const [live, setLive] = useState({
    behavioral_hashes_computed: null,
    trust_claims_logged: null,
    merkle_roots_committed: null,
    scrapers_count: null,
    scrapers_active: null,
    scanners_count: null,
    axes_count: null,
    version: null,
  })

  useEffect(() => {
    // Raw fetch — NOT the shared `request()` from lib/api.js, which auto-
    // redirects 401 → /login and would hijack the public marketing page.
    const base = import.meta.env.VITE_API_URL || '/api/v1'
    const ctrl = new AbortController()
    fetch(`${base}/bfp/stats`, { signal: ctrl.signal })
      .then(r => (r.ok ? r.json() : null))
      .then(d => { if (d) setLive(d) })
      .catch(() => {}) // silent fallback to em-dashes
    return () => ctrl.abort()
  }, [])

  const activeScrapers = live.scrapers_active !== null && live.scrapers_count !== null
    ? `${live.scrapers_active} of ${live.scrapers_count}`
    : '—'

  const stats = [
    { label: 'Version',                    value: formatS(live.version) },
    { label: 'Behavioral hashes computed', value: formatN(live.behavioral_hashes_computed) },
    { label: 'Trust claims logged',        value: formatN(live.trust_claims_logged) },
    { label: 'Merkle roots committed',     value: formatN(live.merkle_roots_committed) },
    { label: 'Active scrapers',            value: activeScrapers },
    { label: 'Scanner modules',            value: formatN(live.scanners_count) },
    { label: 'Fingerprint axes',           value: formatN(live.axes_count) },
    ...STATIC_PROTOCOL_CONSTS,
  ]

  return (
    <div className="max-w-5xl mx-auto px-6">
      <div className="text-center mb-12">
        <div className="text-xs font-mono text-[#00ff88]/70 uppercase tracking-wider mb-3">Status</div>
        <h2 className="text-3xl md:text-4xl font-bold mb-4 font-['Instrument_Sans',sans-serif]">
          Reference implementation, live
        </h2>
        <div className="inline-flex items-center gap-2 text-xs font-mono text-gray-400 mb-2">
          <span className="w-1.5 h-1.5 bg-[#00ff88] rounded-full animate-pulse" />
          xposeTIP — reference impl, live counts
        </div>
      </div>

      <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-3 mb-10">
        {stats.map((s) => (
          <div
            key={s.label}
            className="p-5 bg-[#13131c] border border-[#1e1e2e] rounded-lg"
          >
            <div className="text-xs font-mono text-gray-500 uppercase tracking-wider mb-2">
              {s.label}
            </div>
            <div className="text-xl font-bold text-white font-mono">
              {s.value}
            </div>
          </div>
        ))}
      </div>

      <div className="text-center text-sm text-gray-500">
        Reference implementation is open-source.{' '}
        <a
          href="https://github.com/nabz0r/xposeTIP"
          target="_blank"
          rel="noopener noreferrer"
          className="text-[#00ff88] hover:underline"
        >
          View on GitHub →
        </a>
      </div>
    </div>
  )
}
