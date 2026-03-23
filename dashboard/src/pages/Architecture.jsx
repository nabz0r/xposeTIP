import { useState, useRef, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Shield, ArrowLeft } from 'lucide-react'
import GenerativeAvatar from '../components/GenerativeAvatar'

function useScrollReveal() {
  const ref = useRef(null)
  const [visible, setVisible] = useState(false)
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) setVisible(true) },
      { threshold: 0.15 }
    )
    if (ref.current) observer.observe(ref.current)
    return () => observer.disconnect()
  }, [])
  return [ref, visible]
}

function Section({ children, className = '' }) {
  const [ref, visible] = useScrollReveal()
  return (
    <section ref={ref} className={`transition-all duration-700 ${
      visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
    } ${className}`}>
      {children}
    </section>
  )
}

// Inline SVG diagrams
function CollectDiagram() {
  const categories = [
    { label: 'Social', angle: 0, color: '#3388ff', count: 35 },
    { label: 'Breach', angle: 45, color: '#ff2244', count: 9 },
    { label: 'Metadata', angle: 90, color: '#aa55ff', count: 8 },
    { label: 'Archive', angle: 135, color: '#ffcc00', count: 10 },
    { label: 'Gaming', angle: 180, color: '#ff8800', count: 8 },
    { label: 'People', angle: 225, color: '#00ddcc', count: 7 },
    { label: 'Dev', angle: 270, color: '#cc88ff', count: 12 },
    { label: 'LinkedIn', angle: 315, color: '#0077b5', count: 6 },
  ]
  const cx = 200, cy = 160, r = 110
  return (
    <svg viewBox="0 0 400 320" className="w-full max-w-md mx-auto">
      {/* Center email node */}
      <circle cx={cx} cy={cy} r="28" fill="#00ff8822" stroke="#00ff88" strokeWidth="2" />
      <text x={cx} y={cy + 1} textAnchor="middle" dominantBaseline="middle" fill="#00ff88" fontSize="20" fontFamily="monospace">@</text>

      {categories.map((cat, i) => {
        const rad = (cat.angle * Math.PI) / 180
        const x = cx + r * Math.cos(rad)
        const y = cy + r * Math.sin(rad)
        return (
          <g key={i}>
            <line x1={cx} y1={cy} x2={x} y2={y} stroke={cat.color} strokeWidth="1" opacity="0.3" strokeDasharray="4,4" />
            <circle cx={x} cy={y} r="22" fill={cat.color + '22'} stroke={cat.color} strokeWidth="1.5" />
            <text x={x} y={y - 5} textAnchor="middle" fill={cat.color} fontSize="9" fontFamily="monospace" fontWeight="bold">{cat.count}</text>
            <text x={x} y={y + 8} textAnchor="middle" fill="#888" fontSize="8" fontFamily="sans-serif">{cat.label}</text>
          </g>
        )
      })}
    </svg>
  )
}

function GraphDiagram() {
  const nodes = [
    { id: 'email', x: 200, y: 120, label: 'email', color: '#00ff88', r: 20 },
    { id: 'u1', x: 90, y: 70, label: 'stheis', color: '#ff8800', r: 14 },
    { id: 'u2', x: 310, y: 70, label: 'steffen_t', color: '#ff8800', r: 12 },
    { id: 'p1', x: 60, y: 170, label: 'GitHub', color: '#3388ff', r: 14 },
    { id: 'p2', x: 130, y: 220, label: 'Reddit', color: '#3388ff', r: 11 },
    { id: 'b1', x: 280, y: 190, label: 'LinkedIn 2012', color: '#ff2244', r: 13 },
    { id: 'n1', x: 340, y: 140, label: 'Sam Theis', color: '#00ddcc', r: 13 },
    { id: 'loc', x: 200, y: 240, label: 'Luxembourg', color: '#cc88ff', r: 11 },
  ]
  const edges = [
    { from: 'email', to: 'u1', label: 'same_person' },
    { from: 'email', to: 'u2', label: 'same_person' },
    { from: 'u1', to: 'p1', label: 'registered_with' },
    { from: 'u1', to: 'p2', label: 'registered_with' },
    { from: 'email', to: 'b1', label: 'exposed_in' },
    { from: 'u2', to: 'n1', label: 'identified_as' },
    { from: 'email', to: 'loc', label: 'located_in' },
  ]
  const nodeMap = Object.fromEntries(nodes.map(n => [n.id, n]))
  return (
    <svg viewBox="0 0 400 280" className="w-full max-w-md mx-auto">
      {edges.map((e, i) => {
        const from = nodeMap[e.from], to = nodeMap[e.to]
        const mx = (from.x + to.x) / 2, my = (from.y + to.y) / 2
        return (
          <g key={i}>
            <line x1={from.x} y1={from.y} x2={to.x} y2={to.y} stroke="#1e1e2e" strokeWidth="1.5" />
            <text x={mx} y={my - 4} textAnchor="middle" fill="#444" fontSize="7" fontFamily="monospace">{e.label}</text>
          </g>
        )
      })}
      {nodes.map(n => (
        <g key={n.id}>
          <circle cx={n.x} cy={n.y} r={n.r} fill={n.color + '22'} stroke={n.color} strokeWidth="1.5" />
          <text x={n.x} y={n.y + n.r + 12} textAnchor="middle" fill="#888" fontSize="8" fontFamily="monospace">{n.label}</text>
        </g>
      ))}
    </svg>
  )
}

function PropagateDiagram() {
  const nodes = [
    { x: 200, y: 100, r: 24, color: '#00ff88', label: 'email', conf: '0.95' },
    { x: 100, y: 60, r: 18, color: '#ff8800', label: 'stheis', conf: '0.82' },
    { x: 300, y: 60, r: 12, color: '#ff8800', label: 'steffen_t', conf: '0.45' },
    { x: 60, y: 150, r: 16, color: '#3388ff', label: 'GitHub', conf: '0.78' },
    { x: 140, y: 180, r: 10, color: '#3388ff', label: 'Reddit', conf: '0.35' },
    { x: 280, y: 160, r: 14, color: '#ff2244', label: 'Breach', conf: '0.70' },
    { x: 340, y: 120, r: 11, color: '#00ddcc', label: 'Name', conf: '0.52' },
  ]
  const edges = [
    [0, 1], [0, 2], [1, 3], [1, 4], [0, 5], [2, 6],
  ]
  return (
    <svg viewBox="0 0 400 220" className="w-full max-w-md mx-auto">
      {edges.map(([a, b], i) => (
        <g key={i}>
          <line x1={nodes[a].x} y1={nodes[a].y} x2={nodes[b].x} y2={nodes[b].y} stroke="#1e1e2e" strokeWidth="1.5" />
          {/* Animated flow arrow */}
          <circle r="3" fill="#00ff88" opacity="0.6">
            <animateMotion dur={`${2 + i * 0.3}s`} repeatCount="indefinite"
              path={`M${nodes[a].x},${nodes[a].y} L${nodes[b].x},${nodes[b].y}`} />
          </circle>
        </g>
      ))}
      {nodes.map((n, i) => (
        <g key={i}>
          <circle cx={n.x} cy={n.y} r={n.r} fill={n.color + '22'} stroke={n.color} strokeWidth="1.5" />
          <text x={n.x} y={n.y + n.r + 12} textAnchor="middle" fill="#666" fontSize="7" fontFamily="monospace">{n.label}</text>
          <text x={n.x} y={n.y + 3} textAnchor="middle" fill={n.color} fontSize="9" fontWeight="bold" fontFamily="monospace">{n.conf}</text>
        </g>
      ))}
    </svg>
  )
}

function ScoreDiagram() {
  return (
    <svg viewBox="0 0 400 140" className="w-full max-w-sm mx-auto">
      {/* Exposure bar */}
      <text x="10" y="25" fill="#888" fontSize="10" fontFamily="sans-serif">EXPOSURE</text>
      <text x="10" y="38" fill="#555" fontSize="7" fontFamily="monospace">How much is public</text>
      <rect x="10" y="46" width="380" height="16" rx="8" fill="#1e1e2e" />
      <rect x="10" y="46" width="220" height="16" rx="8" fill="url(#exposureGrad)" />
      <text x="240" y="58" fill="#fff" fontSize="10" fontFamily="monospace" fontWeight="bold">58</text>

      {/* Threat bar */}
      <text x="10" y="90" fill="#888" fontSize="10" fontFamily="sans-serif">THREAT</text>
      <text x="10" y="103" fill="#555" fontSize="7" fontFamily="monospace">How dangerous it is</text>
      <rect x="10" y="110" width="380" height="16" rx="8" fill="#1e1e2e" />
      <rect x="10" y="110" width="140" height="16" rx="8" fill="url(#threatGrad)" />
      <text x="160" y="122" fill="#fff" fontSize="10" fontFamily="monospace" fontWeight="bold">37</text>

      <defs>
        <linearGradient id="exposureGrad" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#00ff88" />
          <stop offset="100%" stopColor="#ff8800" />
        </linearGradient>
        <linearGradient id="threatGrad" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#00ff88" />
          <stop offset="100%" stopColor="#ff2244" />
        </linearGradient>
      </defs>
    </svg>
  )
}

function GeoMapDiagram() {
  return (
    <svg viewBox="0 0 400 250" className="w-full max-w-md mx-auto">
      {/* Continents as simple blobs */}
      <ellipse cx="120" cy="100" rx="60" ry="50" fill="#1e1e2e" stroke="#333" strokeWidth="0.5" />
      <ellipse cx="280" cy="90" rx="80" ry="60" fill="#1e1e2e" stroke="#333" strokeWidth="0.5" />
      <ellipse cx="300" cy="190" rx="40" ry="30" fill="#1e1e2e" stroke="#333" strokeWidth="0.5" />

      {/* Self-reported pins (green, pulsing) */}
      <circle cx="170" cy="80" r="6" fill="#00ff88" opacity="0.8">
        <animate attributeName="r" values="6;8;6" dur="2s" repeatCount="indefinite" />
      </circle>
      <text x="170" y="72" textAnchor="middle" fill="#00ff88" fontSize="8" fontFamily="monospace">LU</text>

      <circle cx="165" cy="90" r="5" fill="#00ff88" opacity="0.6">
        <animate attributeName="r" values="5;7;5" dur="2.5s" repeatCount="indefinite" />
      </circle>
      <text x="165" y="102" textAnchor="middle" fill="#00ff88" fontSize="8" fontFamily="monospace">DE</text>

      {/* Server pins (blue, dim) */}
      <circle cx="100" cy="95" r="4" fill="#3388ff" opacity="0.3" />
      <text x="100" y="88" textAnchor="middle" fill="#3388ff" fontSize="7" fontFamily="monospace" opacity="0.4">SFO</text>

      {/* Legend */}
      <circle cx="20" cy="230" r="4" fill="#00ff88" />
      <text x="30" y="233" fill="#888" fontSize="8">Self-reported</text>
      <circle cx="120" cy="230" r="4" fill="#3388ff" opacity="0.3" />
      <text x="130" y="233" fill="#666" fontSize="8">Mail server</text>
    </svg>
  )
}

export default function Architecture() {
  const demoSeed = {
    num_points: 7, rotation: 142, inner_radius: 0.48,
    hue: 158, saturation: 65, lightness: 52,
    eigenvalues: [1.2, 0.8, 0.5, 0.3, 0.1], complexity: 4, email_hash: 4217,
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white">
      {/* Nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#0a0a0f]/90 backdrop-blur border-b border-[#1e1e2e]">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/welcome" className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors">
            <ArrowLeft className="w-4 h-4" />
            <Shield className="w-5 h-5 text-[#00ff88]" />
            <span className="font-bold font-['Instrument_Sans',sans-serif]">xpose</span>
          </Link>
          <span className="text-xs text-gray-600 font-mono">Architecture</span>
        </div>
      </nav>

      <div className="pt-24 pb-20">
        {/* Hero */}
        <Section className="py-20">
          <div className="max-w-3xl mx-auto px-6 text-center">
            <h1 className="text-4xl md:text-5xl font-bold mb-4 font-['Instrument_Sans',sans-serif]">
              How <span className="text-[#00ff88]">xpose</span> works
            </h1>
            <p className="text-lg text-gray-400 max-w-xl mx-auto">
              From a single email address to a complete identity intelligence report.
              Five stages, 99 sources, one graph.
            </p>
          </div>
        </Section>

        {/* Stage 1: Collect */}
        <Section className="py-20">
          <div className="max-w-4xl mx-auto px-6">
            <div className="grid md:grid-cols-2 gap-12 items-center">
              <div>
                <div className="text-6xl font-mono font-bold text-[#00ff88]/15 mb-2">01</div>
                <h2 className="text-2xl font-bold mb-3 font-['Instrument_Sans',sans-serif]">Collect</h2>
                <p className="text-gray-400 mb-4">
                  Your email is scanned across <span className="text-white font-semibold">99 sources</span> in parallel.
                  Social networks, breach databases, archives, gaming platforms, developer registries, LinkedIn intelligence.
                </p>
                <p className="text-sm text-gray-500">
                  Each source is weighted by reliability. A GitHub profile (<span className="text-[#00ff88] font-mono">0.85</span>)
                  carries more weight than an anonymous scraper (<span className="text-gray-400 font-mono">0.60</span>).
                </p>
              </div>
              <CollectDiagram />
            </div>
          </div>
        </Section>

        {/* Stage 2: Graph */}
        <Section className="py-20 bg-[#12121a]/50">
          <div className="max-w-4xl mx-auto px-6">
            <div className="grid md:grid-cols-2 gap-12 items-center">
              <GraphDiagram />
              <div>
                <div className="text-6xl font-mono font-bold text-[#3388ff]/15 mb-2">02</div>
                <h2 className="text-2xl font-bold mb-3 font-['Instrument_Sans',sans-serif]">Graph</h2>
                <p className="text-gray-400 mb-4">
                  Every data point becomes a <span className="text-white font-semibold">node</span>.
                  Every relationship becomes an <span className="text-white font-semibold">edge</span>.
                </p>
                <div className="space-y-2 text-sm font-mono text-gray-500">
                  <div><span className="text-[#00ff88]">email</span> → <span className="text-[#ff8800]">username</span> → <span className="text-[#3388ff]">platform</span></div>
                  <div><span className="text-[#00ff88]">email</span> → <span className="text-[#ff2244]">breach</span> → <span className="text-gray-400">data_classes</span></div>
                  <div><span className="text-[#ff8800]">username</span> → <span className="text-[#00ddcc]">name</span> <span className="text-gray-600">(identified_as)</span></div>
                </div>
                <p className="text-sm text-gray-500 mt-4">
                  This is your identity graph — a map of how your digital identity is connected across the internet.
                </p>
              </div>
            </div>
          </div>
        </Section>

        {/* Stage 3: Propagate */}
        <Section className="py-20">
          <div className="max-w-4xl mx-auto px-6">
            <div className="grid md:grid-cols-2 gap-12 items-center">
              <div>
                <div className="text-6xl font-mono font-bold text-[#ffcc00]/15 mb-2">03</div>
                <h2 className="text-2xl font-bold mb-3 font-['Instrument_Sans',sans-serif]">Propagate</h2>
                <p className="text-gray-400 mb-4">
                  <span className="text-white font-semibold">Personalized PageRank</span> walks the graph.
                  The email anchor always stays the highest-confidence node —
                  confidence propagates outward through edges weighted by source reliability.
                </p>
                <p className="text-sm text-gray-500 mb-3">
                  A name confirmed by 3 independent sources through different paths accumulates
                  more confidence than a name from a single source.
                </p>
                <p className="text-sm text-gray-500">
                  Teleport probability always returns to the seed email — this is <span className="text-[#ffcc00]">Personalized PageRank</span>,
                  not standard PageRank. The anchor never loses its authority.
                </p>
              </div>
              <PropagateDiagram />
            </div>
          </div>
        </Section>

        {/* Stage 4: Score */}
        <Section className="py-20 bg-[#12121a]/50">
          <div className="max-w-4xl mx-auto px-6">
            <div className="grid md:grid-cols-2 gap-12 items-center">
              <ScoreDiagram />
              <div>
                <div className="text-6xl font-mono font-bold text-[#ff8800]/15 mb-2">04</div>
                <h2 className="text-2xl font-bold mb-3 font-['Instrument_Sans',sans-serif]">Score</h2>
                <p className="text-gray-400 mb-4">
                  Two scores, one identity.
                </p>
                <div className="space-y-3 mb-4">
                  <div className="bg-[#0a0a0f] rounded-lg p-3">
                    <div className="text-sm font-semibold text-[#00ff88]">EXPOSURE</div>
                    <div className="text-xs text-gray-500">How much of you is publicly visible</div>
                  </div>
                  <div className="bg-[#0a0a0f] rounded-lg p-3">
                    <div className="text-sm font-semibold text-[#ff2244]">THREAT</div>
                    <div className="text-xs text-gray-500">How dangerous that exposure is</div>
                  </div>
                </div>
                <p className="text-xs text-gray-500 font-mono">
                  finding weight = severity × source_reliability × graph_confidence
                </p>
              </div>
            </div>
          </div>
        </Section>

        {/* Stage 5: Identify */}
        <Section className="py-20">
          <div className="max-w-4xl mx-auto px-6">
            <div className="grid md:grid-cols-2 gap-12 items-center">
              <div>
                <div className="text-6xl font-mono font-bold text-[#ff2244]/15 mb-2">05</div>
                <h2 className="text-2xl font-bold mb-3 font-['Instrument_Sans',sans-serif]">Identify</h2>
                <p className="text-gray-400 mb-4">
                  Every identity gets a unique <span className="text-white font-semibold">pixel avatar</span>,
                  an 8-axis <span className="text-white font-semibold">digital fingerprint</span>,
                  clustered <span className="text-white font-semibold">personas</span> with aliases,
                  <span className="text-white font-semibold">profile photos</span> collected across platforms,
                  a <span className="text-white font-semibold">geographic exposure map</span>,
                  and a <span className="text-white font-semibold">life timeline</span>.
                </p>
                <p className="text-sm text-gray-500 mb-3">
                  Persona names are resolved through family name consensus — if 3 sources say "Theis",
                  a single outlier won't override the majority. Email-verified sources take priority
                  over username-guessed matches.
                </p>
                <p className="text-sm text-gray-500">
                  The avatar is generated from your graph topology — ~5.4 billion unique combinations.
                  Green face = low risk. Red glitched face = high threat.
                </p>
              </div>
              <div className="flex flex-col items-center gap-6">
                <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-6 flex flex-col items-center gap-3">
                  <GenerativeAvatar seed={demoSeed} size={64} score={42} />
                  <span className="text-[10px] text-gray-600 font-mono">identity glyph · score 42</span>
                </div>
                <div className="grid grid-cols-4 gap-3">
                  {[12, 37, 58, 85].map(score => (
                    <div key={score} className="flex flex-col items-center gap-1">
                      <GenerativeAvatar
                        seed={{ ...demoSeed, email_hash: demoSeed.email_hash + score * 100 }}
                        size={32}
                        score={score}
                      />
                      <span className="text-[9px] text-gray-600 font-mono">{score}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </Section>

        {/* Stage 6: Locate */}
        <Section className="py-20 bg-[#12121a]/50">
          <div className="max-w-4xl mx-auto px-6">
            <div className="grid md:grid-cols-2 gap-12 items-center">
              <GeoMapDiagram />
              <div>
                <div className="text-6xl font-mono font-bold text-[#00ddcc]/15 mb-2">06</div>
                <h2 className="text-2xl font-bold mb-3 font-['Instrument_Sans',sans-serif]">Locate</h2>
                <p className="text-gray-400 mb-4">
                  Self-reported locations from profiles are <span className="text-white font-semibold">geocoded</span> and
                  separated from mail server IP locations. 30+ countries, 20+ cities — zero API calls.
                </p>
                <p className="text-sm text-gray-500 mb-3">
                  GeoIP tells you where Google's servers are. xpose tells you where the <span className="text-[#00ddcc]">person</span> is.
                </p>
                <p className="text-sm text-gray-500">
                  The workspace-wide geographic map gives CISOs instant visibility into their team's
                  global digital exposure.
                </p>
              </div>
            </div>
          </div>
        </Section>

        {/* Roadmap */}
        <Section className="py-20" id="roadmap">
          <div className="max-w-3xl mx-auto px-6">
            <h2 className="text-2xl font-bold mb-8 text-center font-['Instrument_Sans',sans-serif]">Roadmap</h2>
            <div className="space-y-8">
              {[
                {
                  version: 'v1.0', date: 'Nexus 2026 (June)', color: '#00ff88',
                  items: [
                    { done: true, text: '99 scrapers across 8 categories (social, breach, dev, archive, gaming, people, metadata, LinkedIn)' },
                    { done: true, text: 'Personalized PageRank / Markov chain confidence engine' },
                    { done: true, text: '32x32 pixel art identity avatars (~5.4B unique combinations)' },
                    { done: true, text: '8-axis digital fingerprint radar' },
                    { done: true, text: 'Digital personas with display names, aliases, platform badges' },
                    { done: true, text: 'Profile photos tab (cross-platform collection)' },
                    { done: true, text: 'Geographic exposure map (self-reported + server locations)' },
                    { done: true, text: 'Workspace-wide geo map on Dashboard' },
                    { done: true, text: 'Name resolution: family consensus + source method penalty' },
                    { done: true, text: 'Life timeline with breach/account/archive events' },
                    { done: true, text: 'Freemium quick scan with upsell' },
                    { done: true, text: 'Plans (Free/Consultant \u20ac49/Enterprise \u20ac199)' },
                    { done: false, text: 'PDF report export' },
                    { done: false, text: 'Admin scoring tuning sliders' },
                  ],
                },
                {
                  version: 'v1.1', date: 'Post-Nexus (Jul-Aug)', color: '#3388ff',
                  items: [
                    { done: false, text: 'Corporate scrapers (O365, Azure AD, GitHub org)' },
                    { done: false, text: 'Domain-wide scan' },
                    { done: false, text: 'Timezone inference from GitHub commit patterns' },
                    { done: false, text: 'EXIF metadata extraction from profile photos' },
                    { done: false, text: 'Public API + webhook notifications' },
                  ],
                },
                {
                  version: 'v1.2', date: 'Enterprise (Q4 2026)', color: '#ff8800',
                  items: [
                    { done: false, text: 'OAuth audit (Google/Microsoft)' },
                    { done: false, text: 'Scheduled recurring scans' },
                    { done: false, text: 'Compliance reports (NIS2, DORA)' },
                    { done: false, text: 'Multi-language (FR, DE, LU)' },
                  ],
                },
                {
                  version: 'v2.0', date: 'Platform (2027)', color: '#ff2244',
                  items: [
                    { done: false, text: 'Community scraper marketplace' },
                    { done: false, text: 'Plugin API for custom integrations' },
                    { done: false, text: 'Mobile app (iOS/Android)' },
                  ],
                },
              ].map(phase => (
                <div key={phase.version} className="relative pl-8 border-l-2" style={{ borderColor: phase.color + '44' }}>
                  <div className="absolute left-[-7px] top-0 w-3 h-3 rounded-full" style={{ backgroundColor: phase.color }} />
                  <div className="flex items-baseline gap-3 mb-3">
                    <span className="text-lg font-bold font-mono" style={{ color: phase.color }}>{phase.version}</span>
                    <span className="text-sm text-gray-500">{phase.date}</span>
                  </div>
                  <div className="space-y-1.5">
                    {phase.items.map((item, i) => (
                      <div key={i} className="flex items-center gap-2 text-sm">
                        {item.done ? (
                          <span className="text-[#00ff88] text-xs">&#10003;</span>
                        ) : (
                          <span className="text-gray-600 text-xs">&#9675;</span>
                        )}
                        <span className={item.done ? 'text-gray-300' : 'text-gray-500'}>{item.text}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Section>

        {/* CTA */}
        <Section className="py-20">
          <div className="max-w-3xl mx-auto px-6 text-center">
            <h2 className="text-2xl font-bold mb-3 font-['Instrument_Sans',sans-serif]">
              See what the internet knows about you
            </h2>
            <p className="text-gray-500 mb-6">Free scan. No signup required. 30 seconds.</p>
            <Link
              to="/welcome"
              className="inline-flex items-center gap-2 bg-[#00ff88] text-black font-semibold rounded-lg px-6 py-3 text-sm hover:bg-[#00ff88]/90 transition-colors"
            >
              Try it now
            </Link>
          </div>
        </Section>
      </div>

      {/* Footer */}
      <footer className="border-t border-[#1e1e2e] py-8">
        <div className="max-w-5xl mx-auto px-6 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-[#00ff88]" />
            <span className="font-bold text-sm font-['Instrument_Sans',sans-serif]">xpose</span>
            <span className="text-xs text-gray-600 font-mono ml-2">v0.57.0</span>
          </div>
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <Link to="/welcome" className="hover:text-white transition-colors">Home</Link>
            <a href="https://github.com/nabz0r/xposeTIP" className="hover:text-white transition-colors">GitHub</a>
          </div>
        </div>
      </footer>
    </div>
  )
}
