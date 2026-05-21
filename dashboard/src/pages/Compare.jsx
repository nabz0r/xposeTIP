import { Link } from 'react-router-dom'
import { Shield, Check, X, Minus, ArrowRight } from 'lucide-react'
import PublicNav from '../components/landing/PublicNav'
import PublicFooter from '../components/landing/PublicFooter'

// ─── Comparison data ─────────────────────────────────────────────────

const SEGMENTS = [
  {
    id: 'osint',
    title: 'vs OSINT pros',
    subtitle: 'Maltego · SpiderFoot · Recorded Future',
    pitch: 'Same depth of OSINT reconnaissance. Consumer-grade UX. Accessible pricing. Core engine open source under AGPL-3.0.',
    competitors: ['Maltego', 'SpiderFoot', 'Recorded Future'],
    rows: [
      ['120+ OSINT sources', 'yes', 'yes', 'yes', 'yes'],
      ['Consumer-grade UX', 'yes', 'no', 'no', 'partial'],
      ['9-axis behavioral fingerprint', 'yes', 'no', 'no', 'no'],
      ['Identity graph (interactive)', 'yes', 'yes', 'no', 'yes'],
      ['Verified provenance per finding', 'yes', 'partial', 'no', 'partial'],
      ['Legal records (US · FR · UK)', 'yes', 'partial', 'no', 'partial'],
      ['Self-hostable', 'yes', 'yes (paid tier)', 'yes', 'no'],
      ['Open-source core', 'yes (AGPL-3.0)', 'no', 'yes (CE)', 'no'],
      ['Starting price', '€0', '€1.4K/seat', 'Free CE / paid HX', 'enterprise only'],
    ],
  },
  {
    id: 'consumer',
    title: 'vs Consumer protection',
    subtitle: 'Aura · NordProtect · LifeLock',
    pitch: "Same self-service onboarding. But transparent: you see the identity graph, every data source, every finding's provenance. Not a black box that says 'we're monitoring'.",
    competitors: ['Aura', 'NordProtect', 'LifeLock'],
    rows: [
      ['Self-service signup', 'yes', 'yes', 'yes', 'yes'],
      ['Free tier with real intel', 'yes', 'no (trial)', 'no (trial)', 'no'],
      ['Identity graph (interactive)', 'yes', 'no', 'no', 'no'],
      ['Show data sources used', 'yes', 'no', 'no', 'no'],
      ['Per-finding provenance', 'yes', 'no', 'no', 'no'],
      ['9-axis behavioral fingerprint', 'yes', 'no', 'no', 'no'],
      ['Open-source core', 'yes', 'no', 'no', 'no'],
      ['Self-hostable', 'yes', 'no', 'no', 'no'],
      ['Identity insurance', 'no', 'yes ($5M)', 'yes ($1M)', 'yes ($1M)'],
    ],
  },
  {
    id: 'removal',
    title: 'vs Data removal',
    subtitle: 'Incogni · DeleteMe · Optery',
    pitch: 'Mapping over removal. We show your complete exposure — accounts, breaches, legal records, behavioral fingerprint — rather than just delisting from data brokers.',
    competitors: ['Incogni', 'DeleteMe', 'Optery'],
    rows: [
      ['Data broker delisting', 'no', 'yes (420+ brokers)', 'yes (30+)', 'yes (600+)'],
      ['Full digital footprint mapping', 'yes', 'no', 'no', 'partial'],
      ['Breach intelligence', 'yes', 'no', 'no', 'yes'],
      ['Legal records (US · FR · UK)', 'yes', 'no', 'no', 'no'],
      ['Sanctions & PEP screening', 'yes', 'no', 'no', 'no'],
      ['9-axis behavioral fingerprint', 'yes', 'no', 'no', 'no'],
      ['Identity graph (interactive)', 'yes', 'no', 'no', 'no'],
      ['Self-hostable', 'yes', 'no', 'no', 'no'],
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
  { name: 'NordProtect', x: 0.84, y: 0.22, color: '#666' },
  { name: 'Incogni', x: 0.74, y: 0.18, color: '#666' },
  { name: 'xposeTIP', x: 0.78, y: 0.86, color: '#00ff88' },
]

// ─── Cell renderer ───────────────────────────────────────────────────

function Cell({ value, isUs }) {
  if (value === 'yes') return <Check className={`w-4 h-4 ${isUs ? 'text-[#00ff88]' : 'text-gray-500'}`} />
  if (value === 'no') return <X className="w-4 h-4 text-gray-700" />
  if (value === 'partial') return <Minus className="w-4 h-4 text-[#ffcc00]" />
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
            xposeTIP vs the landscape
          </h1>
          <p className="text-lg text-gray-400 max-w-2xl mx-auto leading-relaxed">
            Three product categories touch identity exposure. None sit where we sit — the intersection
            of deep OSINT reconnaissance and consumer-grade UX, with audit-grade provenance and an open-source core.
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
          Comparison data based on public product pages and documentation as of May 2026.
          Categorizations are positional — competitor products evolve.
        </p>
      </div>
      <PublicFooter />
    </div>
  )
}
