import { Link } from 'react-router-dom'
import { Shield, Check, X, Minus, ArrowRight } from 'lucide-react'
import { SOURCE_COUNT } from '../components/landing/constants'
import PublicNav from '../components/landing/PublicNav'
import PublicFooter from '../components/landing/PublicFooter'

// ─── Comparison data ─────────────────────────────────────────────────

// S244 — Peer-reviewed research that maps onto BFP axes. Each card links to
// the paper so readers can verify the claim themselves.
const RESEARCH = [
  { stat: '95%', color: '#00ff88',
    finding: 'Just 4 location points uniquely identify a person — out of 1.5 million.',
    source: 'de Montjoye et al., 2013 · Scientific Reports',
    maps: 'geo axis', url: 'https://www.nature.com/articles/srep01376' },
  { stat: '88%', color: '#3388ff',
    finding: 'Facebook likes alone predict orientation, politics and personality traits.',
    source: 'Kosinski, Stillwell & Graepel, 2013 · PNAS',
    maps: 'digital footprint', url: 'https://www.pnas.org/doi/10.1073/pnas.1218772110' },
  { stat: 'ID', color: '#aa66ff',
    finding: 'Your daily activity rhythm fingerprints you — a measurable "walking signature".',
    source: 'Koffman, Muschelli & Crainiceanu · Johns Hopkins (NHANES)',
    maps: 'activity rhythm', url: 'https://arxiv.org/abs/2506.17160' },
  { stat: '92%', color: '#ffaa00',
    finding: 'How you type identifies you — keystroke rhythm alone, no extra hardware.',
    source: 'Monrose & Rubin, 2000 · Future Generation Computer Systems',
    maps: 'behavioral signature', url: 'https://doi.org/10.1016/S0167-739X(99)00059-X' },
]

const SEGMENTS = [
  {
    id: 'osint',
    title: 'vs OSINT pros',
    subtitle: 'Maltego · SpiderFoot · Recorded Future',
    pitch: 'Same depth of OSINT reconnaissance — consumer-grade UX, accessible pricing, open-source core (AGPL-3.0).',
    competitors: ['Maltego', 'SpiderFoot', 'Recorded Future'],
    rows: [
      [`${SOURCE_COUNT} OSINT sources`, 'yes', 'yes', 'yes', 'yes'],
      ['Consumer-grade UX', 'yes', 'no', 'no', 'partial'],
      ['11-axis behavioral fingerprint', 'yes', 'no', 'no', 'no'],
      ['Verified provenance per finding', 'yes', 'partial', 'no', 'partial'],
      ['Open-source core', { text: 'AGPL-3.0' }, 'no', { text: 'CE' }, 'no'],
      ['Starting price',
        { text: '€0' },
        { text: 'from ~$5K/yr', url: 'https://www.maltego.com/pricing/' },
        { text: 'free CE / paid', url: 'https://www.spiderfoot.net/' },
        { text: 'enterprise', url: 'https://www.recordedfuture.com/' }],
    ],
  },
  {
    id: 'consumer',
    title: 'vs Consumer protection',
    subtitle: 'Aura · Coveron (ex-NordProtect) · LifeLock',
    pitch: "Same self-service onboarding — but transparent: you see the identity graph, every source, every finding's provenance. Not a black box that just says 'we're monitoring'.",
    competitors: ['Aura', 'Coveron', 'LifeLock'],
    rows: [
      ['Free tier with real intel', 'yes', 'no (trial)', 'no (trial)', 'no'],
      ['Show data sources used', 'yes', 'no', 'no', 'no'],
      ['Per-finding provenance', 'yes', 'no', 'no', 'no'],
      ['11-axis behavioral fingerprint', 'yes', 'no', 'no', 'no'],
      ['Open-source core', 'yes', 'no', 'no', 'no'],
      ['Identity theft insurance', 'no',
        { text: 'up to $5M', url: 'https://www.aura.com/learn/aura-vs-lifelock' },
        { text: 'up to $1M', url: 'https://nordprotect.com/features/identity-theft-recovery/' },
        { text: 'up to $3M', url: 'https://lifelock.norton.com/learn/identity-theft-resources/aura-vs-lifelock' }],
    ],
  },
  {
    id: 'removal',
    title: 'vs Data removal',
    subtitle: 'Incogni · DeleteMe · Optery',
    pitch: 'Mapping over removal — we show your complete exposure (accounts, breaches, legal records, behavioral fingerprint) rather than only delisting from data brokers.',
    competitors: ['Incogni', 'DeleteMe', 'Optery'],
    rows: [
      ['Data broker delisting', 'no',
        { text: '420+', url: 'https://cyberinsider.com/data-removal/optery-vs-incogni/' },
        { text: '750+ claimed', url: 'https://cybernews.com/privacy-tools/optery-vs-deleteme-vs-incogni/' },
        { text: '~640+', url: 'https://cybernews.com/privacy-tools/optery-vs-deleteme-vs-incogni/' }],
      ['Full digital footprint mapping', 'yes', 'no', 'no', 'partial'],
      ['Breach intelligence', 'yes', 'no', 'no', 'yes'],
      ['Sanctions & PEP screening', 'yes', 'no', 'no', 'no'],
      ['11-axis behavioral fingerprint', 'yes', 'no', 'no', 'no'],
      ['Open-source core', 'yes', 'no', 'no', 'no'],
    ],
  },
]

// ─── Quadrant data ───────────────────────────────────────────────────
// x = ease of use (0..1, left=low, right=high)
// y = depth (0..1, bottom=low, top=high)

const QUADRANT_POINTS = [
  { name: 'Maltego', x: 0.18, y: 0.92, color: '#888' },
  { name: 'SpiderFoot', x: 0.22, y: 0.78, color: '#888' },
  { name: 'Recorded Future', x: 0.38, y: 0.88, color: '#888' },
  { name: 'Aura', x: 0.86, y: 0.28, color: '#666' },
  { name: 'Coveron', x: 0.84, y: 0.22, color: '#666' },
  { name: 'Incogni', x: 0.74, y: 0.18, color: '#666' },
  { name: 'xposeTIP', x: 0.78, y: 0.86, color: '#00ff88' },
]

// ─── Cell renderer ───────────────────────────────────────────────────

function Cell({ value, isUs }) {
  if (value === 'yes') return <Check className={`w-4 h-4 ${isUs ? 'text-[#00ff88]' : 'text-gray-500'}`} />
  if (value === 'no') return <X className="w-4 h-4 text-gray-700" />
  if (value === 'partial') return <Minus className="w-4 h-4 text-[#ffcc00]" />
  if (value && typeof value === 'object') {
    const cls = `text-xs font-mono ${isUs ? 'text-[#00ff88]' : 'text-gray-500'}`
    return value.url
      ? <a href={value.url} target="_blank" rel="noopener noreferrer"
           className={`${cls} underline decoration-dotted underline-offset-2 hover:opacity-80`}>{value.text}</a>
      : <span className={cls}>{value.text}</span>
  }
  return <span className={`text-xs font-mono ${isUs ? 'text-[#00ff88]' : 'text-gray-500'}`}>{value}</span>
}

// ─── Page ────────────────────────────────────────────────────────────

export default function Compare() {
  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white">
      <PublicNav />

      <div className="max-w-5xl mx-auto px-6 pt-28 pb-20">
        {/* Hero */}
        <section className="mb-20 text-center">
          <div className="inline-flex items-center gap-2 text-xs font-mono text-[#00ff88]/70 mb-6">
            <span className="w-1.5 h-1.5 bg-[#00ff88] rounded-full animate-pulse" />
            Positioning · Identity Threat Intelligence
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-4 font-['Instrument_Sans',sans-serif] leading-tight">
            A category of one.
          </h1>
          <p className="text-lg text-gray-400 max-w-2xl mx-auto leading-relaxed">
            Three industries already read your identity — OSINT tools for analysts, protection apps for insurers,
            removal services for a delete queue. None give the reading back to you. xposeTIP does.
          </p>
        </section>

        {/* S244 — Research band: behavior = identity. Each card cites a paper. */}
        <section className="mb-24">
          <h2 className="text-xs uppercase tracking-wider text-gray-500 mb-2 text-center font-mono">The science is settled</h2>
          <p className="text-center text-xl md:text-2xl font-bold text-white mb-2 max-w-2xl mx-auto font-['Instrument_Sans',sans-serif]">
            Behavior is identity. Researchers proved it a decade ago.
          </p>
          <p className="text-center text-sm text-gray-500 mb-10 max-w-lg mx-auto">
            A behavioral identity layer isn't speculative — it formalizes what peer-reviewed research has shown for years.
          </p>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {RESEARCH.map((r) => (
              <div key={r.source} className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5 flex flex-col">
                <div className="text-3xl font-mono font-bold mb-3" style={{ color: r.color }}>{r.stat}</div>
                <div className="text-sm text-gray-300 leading-relaxed mb-4 flex-1">{r.finding}</div>
                <div className="text-[11px] text-gray-600 font-mono leading-relaxed">{r.source}</div>
                <div className="text-[10px] font-mono mt-2" style={{ color: r.color, opacity: 0.7 }}>→ {r.maps}</div>
                <a href={r.url} target="_blank" rel="noopener noreferrer"
                   className="text-[10px] font-mono text-gray-600 hover:text-gray-300 mt-2">read the paper →</a>
              </div>
            ))}
          </div>
          <p className="text-center text-base text-gray-400 max-w-2xl mx-auto mt-10 leading-relaxed">
            Everyone can already read your behavior. <span className="text-[#00ff88]">Except you.</span>{' '}
            BFP returns that reading to its subject — the category no one else is in.
          </p>
        </section>

        {/* Quadrant */}
        <section className="mb-24">
          <h2 className="text-xs uppercase tracking-wider text-gray-500 mb-2 text-center font-mono">The positioning quadrant</h2>
          <p className="text-center text-sm text-gray-400 mb-8 max-w-md mx-auto">
            Depth of intelligence vs ease of use. We're in the top-right corner — and nobody else is.
          </p>

          <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-6">
            <svg viewBox="0 0 800 500" className="w-full h-auto" preserveAspectRatio="xMidYMid meet">
              {/* Axes */}
              <line x1="60" y1="40" x2="60" y2="440" stroke="#333" strokeWidth="1" />
              <line x1="60" y1="440" x2="760" y2="440" stroke="#333" strokeWidth="1" />

              {/* Axis labels */}
              <text x="40" y="240" textAnchor="middle" transform="rotate(-90 40 240)" fill="#888" fontSize="11" fontFamily="monospace">
                DEPTH OF INTELLIGENCE
              </text>
              <text x="410" y="475" textAnchor="middle" fill="#888" fontSize="11" fontFamily="monospace">
                EASE OF USE →
              </text>

              {/* Tick marks */}
              <text x="55" y="50" textAnchor="end" fill="#555" fontSize="9" fontFamily="monospace">high</text>
              <text x="55" y="445" textAnchor="end" fill="#555" fontSize="9" fontFamily="monospace">low</text>

              {/* Quadrant grid (subtle) */}
              <line x1="410" y1="40" x2="410" y2="440" stroke="#222" strokeDasharray="2,4" />
              <line x1="60" y1="240" x2="760" y2="240" stroke="#222" strokeDasharray="2,4" />

              {/* Quadrant labels */}
              <text x="235" y="35" textAnchor="middle" fill="#444" fontSize="9" fontFamily="monospace">EXPERT-ONLY</text>
              <text x="585" y="35" textAnchor="middle" fill="#444" fontSize="9" fontFamily="monospace">SWEET SPOT</text>
              <text x="235" y="465" textAnchor="middle" fill="#444" fontSize="9" fontFamily="monospace">NICHE</text>
              <text x="585" y="465" textAnchor="middle" fill="#444" fontSize="9" fontFamily="monospace">SHALLOW BUT EASY</text>

              {/* Plot points */}
              {QUADRANT_POINTS.map((p) => {
                const cx = 60 + p.x * 700
                const cy = 440 - p.y * 400
                const isUs = p.name === 'xposeTIP'
                return (
                  <g key={p.name}>
                    <circle
                      cx={cx}
                      cy={cy}
                      r={isUs ? 10 : 5}
                      fill={p.color}
                      opacity={isUs ? 1 : 0.6}
                    />
                    {isUs && (
                      <circle cx={cx} cy={cy} r="16" fill="none" stroke={p.color} strokeWidth="1" opacity="0.4">
                        <animate attributeName="r" from="10" to="20" dur="2s" repeatCount="indefinite" />
                        <animate attributeName="opacity" from="0.6" to="0" dur="2s" repeatCount="indefinite" />
                      </circle>
                    )}
                    <text
                      x={cx + (isUs ? 18 : 10)}
                      y={cy + 4}
                      fill={isUs ? '#00ff88' : '#999'}
                      fontSize={isUs ? 13 : 11}
                      fontWeight={isUs ? 'bold' : 'normal'}
                      fontFamily="system-ui"
                    >
                      {p.name}
                    </text>
                  </g>
                )
              })}
            </svg>
          </div>
        </section>

        {/* Three segments */}
        {SEGMENTS.map((seg) => (
          <section key={seg.id} className="mb-20">
            <div className="flex items-baseline justify-between mb-2">
              <h2 className="text-2xl font-bold font-['Instrument_Sans',sans-serif]">{seg.title}</h2>
              <span className="text-xs font-mono text-gray-600 hidden md:inline">{seg.subtitle}</span>
            </div>
            <p className="text-sm text-gray-400 leading-relaxed mb-6 max-w-3xl">
              {seg.pitch}
            </p>

            <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-[#1e1e2e] bg-[#0a0a0f]">
                      <th className="text-left py-3 px-4 text-xs font-semibold uppercase tracking-wider text-gray-500">Capability</th>
                      <th className="text-center py-3 px-3 text-xs font-semibold uppercase tracking-wider text-[#00ff88]">xposeTIP</th>
                      {seg.competitors.map((c) => (
                        <th key={c} className="text-center py-3 px-3 text-xs font-semibold uppercase tracking-wider text-gray-500">{c}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {seg.rows.map((row, i) => (
                      <tr key={i} className="border-b border-[#1e1e2e] last:border-0 hover:bg-[#0a0a0f]/50">
                        <td className="py-2.5 px-4 text-gray-300">{row[0]}</td>
                        <td className="py-2.5 px-3">
                          <div className="flex justify-center">
                            <Cell value={row[1]} isUs />
                          </div>
                        </td>
                        {row.slice(2).map((cell, j) => (
                          <td key={j} className="py-2.5 px-3">
                            <div className="flex justify-center">
                              <Cell value={cell} />
                            </div>
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </section>
        ))}

        {/* Bottom CTA */}
        <section className="border-t border-[#1e1e2e] pt-16 text-center">
          <h2 className="text-2xl font-bold mb-4 font-['Instrument_Sans',sans-serif]">
            See what we find on you
          </h2>
          <p className="text-gray-400 mb-8 max-w-md mx-auto">
            One email in. Full identity portrait out. Free, no signup needed to start.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              to="/welcome"
              className="inline-flex items-center justify-center gap-2 text-sm font-semibold bg-[#00ff88] text-black hover:bg-[#00ff88]/90 rounded-lg px-6 py-3 transition-colors"
            >
              Try free
              <ArrowRight className="w-4 h-4" />
            </Link>
            <a
              href="mailto:contact@redbird.co.com?subject=xposeTIP%20consulting%20inquiry"
              className="inline-flex items-center justify-center gap-2 text-sm font-semibold bg-[#aa66ff]/15 text-[#aa66ff] border border-[#aa66ff]/40 hover:bg-[#aa66ff]/25 rounded-lg px-6 py-3 transition-colors"
            >
              Talk to us — consulting
            </a>
          </div>
        </section>

        {/* Footer note */}
        <p className="text-center text-[10px] text-gray-700 font-mono mt-20">
          Comparison data verified against public sources, June 2026 — every figure links to its source.
          Categorizations are positional; competitor products evolve.
        </p>
      </div>
      <PublicFooter />
    </div>
  )
}
