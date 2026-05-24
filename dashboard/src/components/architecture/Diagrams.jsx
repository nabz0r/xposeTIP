// S206 step 1/3 — Visual language unify per BFPLayer S205 standards.
// Palette: #00ff88 (identity/active) / #3388ff (data flow / connection) /
//          #ff5588 (risk / extraction / breach) / #888 (neutral / labels).
// viewBox 0 0 600 400 across all 8 diagrams. fontSize ≥11. strokeWidth 1.5.
// All elements wrapped in motion.* with whileInView once-only.

import { motion } from 'framer-motion'

// Shared motion presets to keep sequencing consistent across diagrams
const fadeIn = (delay = 0, dur = 0.5) => ({
  initial: { opacity: 0 },
  whileInView: { opacity: 1 },
  viewport: { once: true, amount: 0.3 },
  transition: { duration: dur, delay },
})

const popIn = (delay = 0, dur = 0.5) => ({
  initial: { opacity: 0, scale: 0.85 },
  whileInView: { opacity: 1, scale: 1 },
  viewport: { once: true, amount: 0.3 },
  transition: { duration: dur, delay },
})

const drawLine = (delay = 0, dur = 0.6) => ({
  initial: { pathLength: 0, opacity: 0 },
  whileInView: { pathLength: 1, opacity: 1 },
  viewport: { once: true, amount: 0.3 },
  transition: { duration: dur, delay },
})

// =====================================================================
export function CollectDiagram() {
  // 9 source categories arrayed around a central email node.
  // 4-color semantic bucketing:
  //   data flow (#3388ff): Social, People, Identity, Gaming
  //   risk (#ff5588):       Breach, Exposure
  //   neutral (#888):       Metadata, Archive, Other
  const categories = [
    { label: 'Social',   angle: 0,   color: '#3388ff', count: 70 },
    { label: 'Metadata', angle: 40,  color: '#888',    count: 19 },
    { label: 'People',   angle: 80,  color: '#3388ff', count: 11 },
    { label: 'Gaming',   angle: 120, color: '#3388ff', count: 10 },
    { label: 'Exposure', angle: 160, color: '#ff5588', count: 15 },
    { label: 'Breach',   angle: 200, color: '#ff5588', count: 9 },
    { label: 'Archive',  angle: 240, color: '#888',    count: 9 },
    { label: 'Identity', angle: 280, color: '#3388ff', count: 8 },
    { label: 'Other',    angle: 320, color: '#888',    count: 19 },
  ]
  const cx = 300, cy = 200, r = 150
  return (
    <svg viewBox="0 0 600 400" className="w-full max-w-md mx-auto h-auto" xmlns="http://www.w3.org/2000/svg">
      {/* Center email node */}
      <motion.g {...popIn(0)}>
        <circle cx={cx} cy={cy} r="34" fill="#00ff8822" stroke="#00ff88" strokeWidth="1.5" />
        <text x={cx} y={cy + 2} textAnchor="middle" dominantBaseline="middle" fill="#00ff88" fontSize="24" fontFamily="monospace">@</text>
      </motion.g>

      {categories.map((cat, i) => {
        const rad = (cat.angle * Math.PI) / 180
        const x = cx + r * Math.cos(rad)
        const y = cy + r * Math.sin(rad)
        return (
          <motion.g key={i} {...fadeIn(0.15 + 0.07 * i, 0.5)}>
            <line x1={cx} y1={cy} x2={x} y2={y} stroke={cat.color} strokeWidth="1.5" opacity="0.3" strokeDasharray="4,4" />
            <circle cx={x} cy={y} r="26" fill={cat.color + '22'} stroke={cat.color} strokeWidth="1.5" />
            <text x={x} y={y - 4} textAnchor="middle" fill={cat.color} fontSize="12" fontFamily="monospace" fontWeight="bold">{cat.count}</text>
            <text x={x} y={y + 12} textAnchor="middle" fill="#888" fontSize="11" fontFamily="monospace">{cat.label}</text>
          </motion.g>
        )
      })}
    </svg>
  )
}

// =====================================================================
export function GraphDiagram() {
  // Identity graph: email anchor → usernames → platforms; breach + name + location.
  // email/name = #00ff88 identity. usernames/platforms = #3388ff data flow.
  // breach = #ff5588 risk. location = #888 neutral.
  const nodes = [
    { id: 'email', x: 300, y: 170, label: 'email',         color: '#00ff88', r: 24 },
    { id: 'u1',    x: 140, y: 100, label: 'stheis',        color: '#3388ff', r: 18 },
    { id: 'u2',    x: 460, y: 100, label: 'steffen_t',     color: '#3388ff', r: 15 },
    { id: 'p1',    x: 90,  y: 240, label: 'GitHub',        color: '#3388ff', r: 18 },
    { id: 'p2',    x: 190, y: 310, label: 'Reddit',        color: '#3388ff', r: 14 },
    { id: 'b1',    x: 420, y: 270, label: 'LinkedIn 2012', color: '#ff5588', r: 16 },
    { id: 'n1',    x: 510, y: 200, label: 'Sam Theis',     color: '#00ff88', r: 16 },
    { id: 'loc',   x: 300, y: 340, label: 'Luxembourg',    color: '#888',    r: 14 },
  ]
  const edges = [
    { from: 'email', to: 'u1',  label: 'same_person' },
    { from: 'email', to: 'u2',  label: 'same_person' },
    { from: 'u1',    to: 'p1',  label: 'registered_with' },
    { from: 'u1',    to: 'p2',  label: 'registered_with' },
    { from: 'email', to: 'b1',  label: 'exposed_in' },
    { from: 'u2',    to: 'n1',  label: 'identified_as' },
    { from: 'email', to: 'loc', label: 'located_in' },
  ]
  const nodeMap = Object.fromEntries(nodes.map(n => [n.id, n]))
  return (
    <svg viewBox="0 0 600 400" className="w-full max-w-md mx-auto h-auto" xmlns="http://www.w3.org/2000/svg">
      {edges.map((e, i) => {
        const from = nodeMap[e.from], to = nodeMap[e.to]
        const mx = (from.x + to.x) / 2, my = (from.y + to.y) / 2
        return (
          <motion.g key={i} {...fadeIn(0.3 + 0.06 * i, 0.4)}>
            <line x1={from.x} y1={from.y} x2={to.x} y2={to.y} stroke="#888" strokeWidth="1.5" opacity="0.4" />
            <text x={mx} y={my - 6} textAnchor="middle" fill="#666" fontSize="11" fontFamily="monospace">{e.label}</text>
          </motion.g>
        )
      })}
      {nodes.map((n, i) => (
        <motion.g key={n.id} {...popIn(0.05 + 0.08 * i, 0.5)}>
          <circle cx={n.x} cy={n.y} r={n.r} fill={n.color + '22'} stroke={n.color} strokeWidth="1.5" />
          <text x={n.x} y={n.y + n.r + 16} textAnchor="middle" fill="#aaa" fontSize="11" fontFamily="monospace">{n.label}</text>
        </motion.g>
      ))}
    </svg>
  )
}

// =====================================================================
export function PropagateDiagram() {
  // Personalized PageRank flowing from email anchor outward. Same palette as Graph.
  const nodes = [
    { x: 300, y: 140, r: 28, color: '#00ff88', label: 'email',     conf: '0.95' },
    { x: 140, y: 80,  r: 22, color: '#3388ff', label: 'stheis',    conf: '0.82' },
    { x: 460, y: 80,  r: 16, color: '#3388ff', label: 'steffen_t', conf: '0.45' },
    { x: 90,  y: 220, r: 20, color: '#3388ff', label: 'GitHub',    conf: '0.78' },
    { x: 200, y: 280, r: 14, color: '#3388ff', label: 'Reddit',    conf: '0.35' },
    { x: 430, y: 240, r: 18, color: '#ff5588', label: 'Breach',    conf: '0.70' },
    { x: 510, y: 180, r: 15, color: '#00ff88', label: 'Name',      conf: '0.52' },
  ]
  const edges = [[0, 1], [0, 2], [1, 3], [1, 4], [0, 5], [2, 6]]
  return (
    <svg viewBox="0 0 600 400" className="w-full max-w-md mx-auto h-auto" xmlns="http://www.w3.org/2000/svg">
      {edges.map(([a, b], i) => (
        <motion.g key={i} {...fadeIn(0.2 + 0.08 * i, 0.4)}>
          <line x1={nodes[a].x} y1={nodes[a].y} x2={nodes[b].x} y2={nodes[b].y} stroke="#888" strokeWidth="1.5" opacity="0.4" />
          {/* Animated confidence flow particle */}
          <circle r="3" fill="#00ff88" opacity="0.7">
            <animateMotion dur={`${2 + i * 0.3}s`} repeatCount="indefinite"
              path={`M${nodes[a].x},${nodes[a].y} L${nodes[b].x},${nodes[b].y}`} />
          </circle>
        </motion.g>
      ))}
      {nodes.map((n, i) => (
        <motion.g key={i} {...popIn(0.1 + 0.07 * i, 0.5)}>
          <circle cx={n.x} cy={n.y} r={n.r} fill={n.color + '22'} stroke={n.color} strokeWidth="1.5" />
          <text x={n.x} y={n.y + n.r + 16} textAnchor="middle" fill="#aaa" fontSize="11" fontFamily="monospace">{n.label}</text>
          <text x={n.x} y={n.y + 4} textAnchor="middle" fill={n.color} fontSize="12" fontWeight="bold" fontFamily="monospace">{n.conf}</text>
        </motion.g>
      ))}
    </svg>
  )
}

// =====================================================================
export function ScoreDiagram() {
  // Dual gauge: exposure (neutral→active) and threat (active→risk).
  return (
    <svg viewBox="0 0 600 400" className="w-full max-w-md mx-auto h-auto" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="exposureGrad" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#00ff88" />
          <stop offset="100%" stopColor="#888" />
        </linearGradient>
        <linearGradient id="threatGrad" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#00ff88" />
          <stop offset="100%" stopColor="#ff5588" />
        </linearGradient>
      </defs>

      {/* Exposure */}
      <motion.g {...fadeIn(0.1, 0.5)}>
        <text x="50" y="80" fill="#aaa" fontSize="14" fontFamily="monospace" fontWeight="bold">EXPOSURE</text>
        <text x="50" y="100" fill="#888" fontSize="11" fontFamily="monospace">How much is public</text>
        <rect x="50" y="115" width="500" height="22" rx="11" fill="#1e1e2e" />
        <motion.rect
          x="50" y="115" height="22" rx="11" fill="url(#exposureGrad)"
          initial={{ width: 0 }}
          whileInView={{ width: 290 }}
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.9, delay: 0.4 }}
        />
        <text x="350" y="131" fill="#fff" fontSize="13" fontFamily="monospace" fontWeight="bold">58</text>
      </motion.g>

      {/* Threat */}
      <motion.g {...fadeIn(0.6, 0.5)}>
        <text x="50" y="220" fill="#aaa" fontSize="14" fontFamily="monospace" fontWeight="bold">THREAT</text>
        <text x="50" y="240" fill="#888" fontSize="11" fontFamily="monospace">How dangerous it is</text>
        <rect x="50" y="255" width="500" height="22" rx="11" fill="#1e1e2e" />
        <motion.rect
          x="50" y="255" height="22" rx="11" fill="url(#threatGrad)"
          initial={{ width: 0 }}
          whileInView={{ width: 185 }}
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.9, delay: 0.9 }}
        />
        <text x="245" y="271" fill="#fff" fontSize="13" fontFamily="monospace" fontWeight="bold">37</text>
      </motion.g>

      {/* Formula */}
      <motion.text
        x="300" y="350" textAnchor="middle"
        fill="#888" fontSize="11" fontFamily="monospace"
        {...fadeIn(1.3, 0.4)}
      >
        weight = severity × source_reliability × graph_confidence
      </motion.text>
    </svg>
  )
}

// =====================================================================
export function GeoMapDiagram() {
  // Self-reported pins (#00ff88) vs mail server pins (#888 neutral).
  return (
    <svg viewBox="0 0 600 400" className="w-full max-w-md mx-auto h-auto" xmlns="http://www.w3.org/2000/svg">
      {/* Continent blobs */}
      <motion.g {...fadeIn(0, 0.6)}>
        <ellipse cx="180" cy="160" rx="90"  ry="70" fill="#1e1e2e" stroke="#888" strokeWidth="1.5" opacity="0.5" />
        <ellipse cx="420" cy="150" rx="115" ry="85" fill="#1e1e2e" stroke="#888" strokeWidth="1.5" opacity="0.5" />
        <ellipse cx="450" cy="290" rx="60"  ry="45" fill="#1e1e2e" stroke="#888" strokeWidth="1.5" opacity="0.5" />
      </motion.g>

      {/* Self-reported pins (active green, pulsing) */}
      <motion.g {...popIn(0.6, 0.5)}>
        <circle cx="250" cy="130" r="8" fill="#00ff88" opacity="0.85">
          <animate attributeName="r" values="8;11;8" dur="2s" repeatCount="indefinite" />
        </circle>
        <text x="250" y="115" textAnchor="middle" fill="#00ff88" fontSize="11" fontFamily="monospace">LU</text>
      </motion.g>

      <motion.g {...popIn(0.8, 0.5)}>
        <circle cx="245" cy="155" r="7" fill="#00ff88" opacity="0.7">
          <animate attributeName="r" values="7;10;7" dur="2.5s" repeatCount="indefinite" />
        </circle>
        <text x="245" y="178" textAnchor="middle" fill="#00ff88" fontSize="11" fontFamily="monospace">DE</text>
      </motion.g>

      {/* Mail server pin (neutral, dim) */}
      <motion.g {...popIn(1.0, 0.5)}>
        <circle cx="140" cy="170" r="6" fill="#888" opacity="0.6" />
        <text x="140" y="155" textAnchor="middle" fill="#888" fontSize="11" fontFamily="monospace" opacity="0.6">SFO</text>
      </motion.g>

      {/* Legend */}
      <motion.g {...fadeIn(1.4, 0.4)}>
        <circle cx="40" cy="370" r="6" fill="#00ff88" />
        <text x="55" y="374" fill="#aaa" fontSize="11" fontFamily="monospace">Self-reported (person)</text>
        <circle cx="280" cy="370" r="6" fill="#888" opacity="0.6" />
        <text x="295" y="374" fill="#888" fontSize="11" fontFamily="monospace">Mail server (network)</text>
      </motion.g>
    </svg>
  )
}

// =====================================================================
export function CascadeDiagram() {
  // 4-state machine + terminal failed path.
  // gathering = #888 (neutral start) · computing = #3388ff (data flow) ·
  // similarity = #3388ff (data flow continuation) · done = #00ff88 (success) ·
  // failed = #ff5588 (risk).
  const states = [
    { x: 30,  y: 140, label: 'gathering',  color: '#888'    },
    { x: 170, y: 140, label: 'computing',  color: '#3388ff' },
    { x: 310, y: 140, label: 'similarity', color: '#3388ff' },
    { x: 450, y: 140, label: 'done',       color: '#00ff88' },
  ]
  return (
    <svg viewBox="0 0 600 400" className="w-full max-w-md mx-auto h-auto" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <marker id="cascade-arrow" markerWidth="10" markerHeight="10" refX="6" refY="3" orient="auto">
          <path d="M0,0 L0,6 L6,3 z" fill="#888" />
        </marker>
        <marker id="cascade-arrow-fail" markerWidth="10" markerHeight="10" refX="6" refY="3" orient="auto">
          <path d="M0,0 L0,6 L6,3 z" fill="#ff5588" />
        </marker>
      </defs>

      <motion.text
        x="300" y="50" textAnchor="middle"
        fill="#aaa" fontSize="13" fontFamily="monospace"
        {...fadeIn(0, 0.4)}
      >
        scans.cascade_state · alembic 014
      </motion.text>

      {states.map((s, i) => (
        <motion.g key={s.label} {...popIn(0.2 + 0.18 * i, 0.5)}>
          <rect x={s.x} y={s.y} width="100" height="52" rx="6"
            fill={s.color + '22'} stroke={s.color} strokeWidth="1.5" />
          <text x={s.x + 50} y={s.y + 22} textAnchor="middle" fill={s.color}
            fontSize="12" fontFamily="monospace" fontWeight="bold">{s.label}</text>
          <text x={s.x + 50} y={s.y + 40} textAnchor="middle" fill="#888"
            fontSize="11" fontFamily="monospace">{i === 0 ? 'enter' : `T+${i * 30}s`}</text>
          {i < states.length - 1 && (
            <motion.line
              x1={s.x + 100} y1={s.y + 26} x2={states[i + 1].x} y2={s.y + 26}
              stroke="#888" strokeWidth="1.5"
              markerEnd="url(#cascade-arrow)"
              {...drawLine(0.4 + 0.18 * i, 0.4)}
            />
          )}
        </motion.g>
      ))}

      {/* Failed terminal branch */}
      <motion.line
        x1="220" y1="192" x2="220" y2="240" stroke="#ff5588" strokeWidth="1.5"
        strokeDasharray="4,3" markerEnd="url(#cascade-arrow-fail)"
        {...drawLine(1.4, 0.5)}
      />
      <motion.g {...popIn(1.8, 0.5)}>
        <rect x="170" y="248" width="100" height="46" rx="6"
          fill="#ff558822" stroke="#ff5588" strokeWidth="1.5" />
        <text x="220" y="270" textAnchor="middle" fill="#ff5588"
          fontSize="12" fontFamily="monospace" fontWeight="bold">failed</text>
        <text x="220" y="285" textAnchor="middle" fill="#888"
          fontSize="11" fontFamily="monospace">terminal</text>
      </motion.g>
    </svg>
  )
}

// =====================================================================
export function SimilarityDiagram() {
  // Central identity + N satellite matches around it.
  // High match (≥90) = #00ff88 (close-kin signal) · mid (70-90) = #3388ff ·
  // low (<70) = #888 (weak similarity).
  const cx = 300, cy = 200
  const R = 130
  const satellites = [
    { angle: -90, score: 95, color: '#00ff88' },
    { angle: -25, score: 94, color: '#00ff88' },
    { angle: 35,  score: 93, color: '#00ff88' },
    { angle: 105, score: 93, color: '#00ff88' },
    { angle: 175, score: 70, color: '#3388ff' },
  ]
  return (
    <svg viewBox="0 0 600 400" className="w-full max-w-md mx-auto h-auto" xmlns="http://www.w3.org/2000/svg">
      {satellites.map((s, i) => {
        const rad = (s.angle * Math.PI) / 180
        const x = cx + R * Math.cos(rad)
        const y = cy + R * Math.sin(rad)
        const strong = s.score >= 90
        return (
          <motion.g key={i} {...popIn(0.4 + 0.12 * i, 0.5)}>
            <line x1={cx} y1={cy} x2={x} y2={y}
              stroke={s.color} strokeWidth={strong ? 2 : 1.5}
              opacity={s.score / 100}
              strokeDasharray={strong ? '0' : '4,3'} />
            <circle cx={x} cy={y} r="20" fill={s.color + '22'} stroke={s.color} strokeWidth="1.5" />
            <text x={x} y={y + 2} textAnchor="middle" dominantBaseline="middle"
              fill={s.color} fontSize="12" fontFamily="monospace" fontWeight="bold">{s.score}%</text>
          </motion.g>
        )
      })}
      <motion.g {...popIn(0, 0.5)}>
        <circle cx={cx} cy={cy} r="30" fill="#00ff8833" stroke="#00ff88" strokeWidth="2" />
        <text x={cx} y={cy + 2} textAnchor="middle" dominantBaseline="middle"
          fill="#00ff88" fontSize="16" fontFamily="monospace" fontWeight="bold">id</text>
      </motion.g>
      <motion.text
        x="300" y="370" textAnchor="middle" fill="#888"
        fontSize="11" fontFamily="monospace"
        {...fadeIn(1.0, 0.4)}
      >
        cosine 11-axis · threshold 0.70 · first_detected preserved
      </motion.text>
    </svg>
  )
}

// =====================================================================
export function DiscoveryDiagram() {
  // 5-step funnel: queries → fetch → extractors → quality gate → leads.
  // Steps 1-4 = #3388ff (process). Step 5 = #00ff88 (outcome).
  const steps = [
    { y: 40,  w: 460, label: 'Fingerprint → dork queries', color: '#3388ff', val: '20 queries' },
    { y: 105, w: 400, label: 'Trafilatura fetch',          color: '#3388ff', val: '50 pages' },
    { y: 170, w: 340, label: '6 extractors',                color: '#3388ff', val: 'rel-me · jsonld · email · …' },
    { y: 235, w: 280, label: 'Quality gate',                color: '#3388ff', val: 'dedup vs findings' },
    { y: 300, w: 220, label: 'discovery_leads',             color: '#00ff88', val: 'operator review' },
  ]
  return (
    <svg viewBox="0 0 600 400" className="w-full max-w-md mx-auto h-auto" xmlns="http://www.w3.org/2000/svg">
      {steps.map((s, i) => (
        <motion.g key={i} {...popIn(0.1 + 0.18 * i, 0.5)}>
          <rect x={(600 - s.w) / 2} y={s.y} width={s.w} height="44" rx="6"
            fill={s.color + '1a'} stroke={s.color} strokeWidth="1.5" />
          <text x="300" y={s.y + 22} textAnchor="middle" fill={s.color}
            fontSize="13" fontFamily="monospace" fontWeight="bold">{s.label}</text>
          <text x="300" y={s.y + 36} textAnchor="middle" fill="#888"
            fontSize="11" fontFamily="monospace">{s.val}</text>
          {i < steps.length - 1 && (
            <motion.path
              d={`M 300 ${s.y + 44} L 300 ${steps[i + 1].y - 1}`}
              stroke="#888" strokeWidth="1.5" fill="none"
              {...drawLine(0.3 + 0.18 * i, 0.3)}
            />
          )}
        </motion.g>
      ))}
      <motion.text
        x="300" y="370" textAnchor="middle" fill="#888"
        fontSize="11" fontFamily="monospace"
        {...fadeIn(1.3, 0.4)}
      >
        budget · 20 queries · 50 pages · 60 seconds
      </motion.text>
    </svg>
  )
}
