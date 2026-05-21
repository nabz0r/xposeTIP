export function CollectDiagram() {
  const categories = [
    { label: 'Social', angle: 0, color: '#3388ff', count: 50 },
    { label: 'Metadata', angle: 40, color: '#aa55ff', count: 15 },
    { label: 'People', angle: 80, color: '#00ddcc', count: 11 },
    { label: 'Gaming', angle: 120, color: '#ff8800', count: 10 },
    { label: 'Exposure', angle: 160, color: '#ff5588', count: 10 },
    { label: 'Breach', angle: 200, color: '#ff2244', count: 9 },
    { label: 'Archive', angle: 240, color: '#ffcc00', count: 9 },
    { label: 'Identity', angle: 280, color: '#cc88ff', count: 5 },
    { label: 'Other', angle: 320, color: '#888888', count: 8 },
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

export function GraphDiagram() {
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

export function PropagateDiagram() {
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

export function ScoreDiagram() {
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

export function GeoMapDiagram() {
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

export function CascadeDiagram() {
  const states = [
    { x: 30, y: 90, label: 'gathering', color: '#88aaff' },
    { x: 130, y: 90, label: 'computing', color: '#ff8800' },
    { x: 230, y: 90, label: 'similarity', color: '#cc88ff' },
    { x: 330, y: 90, label: 'done', color: '#00ff88' },
  ]
  return (
    <svg viewBox="0 0 400 220" className="w-full max-w-md mx-auto">
      {states.map((s, i) => (
        <g key={s.label}>
          <rect x={s.x} y={s.y} width="60" height="40" rx="6"
            fill={s.color + '22'} stroke={s.color} strokeWidth="1.5" />
          <text x={s.x + 30} y={s.y + 18} textAnchor="middle" fill={s.color}
            fontSize="9" fontFamily="monospace" fontWeight="bold">{s.label}</text>
          <text x={s.x + 30} y={s.y + 30} textAnchor="middle" fill="#666"
            fontSize="7" fontFamily="monospace">{i === 0 ? 'enter' : `T+${i * 30}s`}</text>
          {i < states.length - 1 && (
            <g>
              <line x1={s.x + 60} y1={s.y + 20} x2={states[i + 1].x} y2={s.y + 20}
                stroke={s.color} strokeWidth="1.5" markerEnd="url(#arrow)" />
            </g>
          )}
        </g>
      ))}
      <defs>
        <marker id="arrow" markerWidth="10" markerHeight="10" refX="6" refY="3" orient="auto">
          <path d="M0,0 L0,6 L6,3 z" fill="#88aaff" />
        </marker>
      </defs>
      <line x1="160" y1="130" x2="160" y2="170" stroke="#ff2244" strokeWidth="1.5"
        strokeDasharray="4,3" />
      <rect x="130" y="170" width="60" height="32" rx="6"
        fill="#ff224422" stroke="#ff2244" strokeWidth="1.5" />
      <text x="160" y="186" textAnchor="middle" fill="#ff2244"
        fontSize="9" fontFamily="monospace" fontWeight="bold">failed</text>
      <text x="160" y="197" textAnchor="middle" fill="#666"
        fontSize="7" fontFamily="monospace">terminal</text>
      <text x="200" y="20" textAnchor="middle" fill="#888"
        fontSize="10" fontFamily="monospace">scans.cascade_state · alembic 014</text>
    </svg>
  )
}

export function SimilarityDiagram() {
  const cx = 200, cy = 140
  const satellites = [
    { angle: -90, score: 95, color: '#ff2244' },
    { angle: -25, score: 94, color: '#ff8800' },
    { angle: 35, score: 93, color: '#ffcc00' },
    { angle: 105, score: 93, color: '#00ddcc' },
    { angle: 175, score: 70, color: '#3388ff' },
  ]
  return (
    <svg viewBox="0 0 400 280" className="w-full max-w-md mx-auto">
      {satellites.map((s, i) => {
        const rad = (s.angle * Math.PI) / 180
        const r = 95
        const x = cx + r * Math.cos(rad)
        const y = cy + r * Math.sin(rad)
        const opacity = s.score / 100
        return (
          <g key={i}>
            <line x1={cx} y1={cy} x2={x} y2={y}
              stroke={s.color} strokeWidth={s.score >= 90 ? 1.5 : 1}
              opacity={opacity} strokeDasharray={s.score >= 90 ? '0' : '3,3'} />
            <circle cx={x} cy={y} r="14" fill={s.color + '22'} stroke={s.color} strokeWidth="1.5" />
            <text x={x} y={y + 1} textAnchor="middle" dominantBaseline="middle"
              fill={s.color} fontSize="9" fontFamily="monospace" fontWeight="bold">{s.score}%</text>
          </g>
        )
      })}
      <circle cx={cx} cy={cy} r="22" fill="#cc88ff33" stroke="#cc88ff" strokeWidth="2" />
      <text x={cx} y={cy + 1} textAnchor="middle" dominantBaseline="middle"
        fill="#cc88ff" fontSize="14" fontFamily="monospace" fontWeight="bold">id</text>
      <text x="200" y="255" textAnchor="middle" fill="#888"
        fontSize="10" fontFamily="monospace">cosine 9-axis · threshold 0.70 · first_detected preserved</text>
    </svg>
  )
}

export function DiscoveryDiagram() {
  const steps = [
    { y: 30, w: 280, label: 'Fingerprint → dork queries', color: '#ffaa55', val: '20' },
    { y: 70, w: 240, label: 'Trafilatura fetch', color: '#ff8800', val: '50 pages' },
    { y: 110, w: 200, label: '6 extractors', color: '#ff5588', val: 'rel-me · jsonld · …' },
    { y: 150, w: 160, label: 'Quality gate', color: '#cc88ff', val: 'dedup vs findings' },
    { y: 190, w: 120, label: 'discovery_leads', color: '#00ff88', val: 'operator review' },
  ]
  return (
    <svg viewBox="0 0 400 240" className="w-full max-w-md mx-auto">
      {steps.map((s, i) => (
        <g key={i}>
          <rect x={(400 - s.w) / 2} y={s.y} width={s.w} height="28" rx="4"
            fill={s.color + '22'} stroke={s.color} strokeWidth="1.5" />
          <text x="200" y={s.y + 13} textAnchor="middle" fill={s.color}
            fontSize="10" fontFamily="monospace" fontWeight="bold">{s.label}</text>
          <text x="200" y={s.y + 23} textAnchor="middle" fill="#888"
            fontSize="8" fontFamily="monospace">{s.val}</text>
          {i < steps.length - 1 && (
            <path d={`M 200 ${s.y + 28} L 200 ${steps[i + 1].y - 1}`}
              stroke="#444" strokeWidth="1" />
          )}
        </g>
      ))}
      <text x="200" y="225" textAnchor="middle" fill="#666"
        fontSize="8" fontFamily="monospace">budget · 20 q / 50 p / 60 s</text>
    </svg>
  )
}
