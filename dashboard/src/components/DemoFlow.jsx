import { motion, AnimatePresence } from 'framer-motion'

// S249 — Timeline-driven fork of HeroDiagram (S207).
// Same viewBox 800×600, same box geometry, same palette, same markers.
// Only diff: layer reveal is driven by the `activeLayer` prop coming from
// the Demo timeline, not by scroll-into-view. Each act lights one layer.

const LAYERS = ['inputs', 'osint', 'graph', 'reports', 'bfp']

// Activation order: each layer stays "on" once activated, so by Act 4 all
// the lower layers are still lit + the BFP highlight pulses.
function isOn(layer, active) {
  if (!active) return false
  const aIdx = LAYERS.indexOf(active)
  const lIdx = LAYERS.indexOf(layer)
  return lIdx <= aIdx
}

const dim = { opacity: 0.18 }
const lit = { opacity: 1 }

export default function DemoFlow({ activeLayer = null, sources = 179, scanners = 28 }) {
  const inputsOn = isOn('inputs', activeLayer)
  const osintOn = isOn('osint', activeLayer)
  const graphOn = isOn('graph', activeLayer)
  const reportsOn = isOn('reports', activeLayer)
  const bfpOn = isOn('bfp', activeLayer)

  return (
    <div className="relative w-full h-full">
      {/* Same grid as HeroDiagram */}
      <div
        className="absolute inset-0 opacity-[0.02] pointer-events-none"
        style={{
          backgroundImage:
            'linear-gradient(#00ff88 1px, transparent 1px), linear-gradient(90deg, #00ff88 1px, transparent 1px)',
          backgroundSize: '60px 60px',
        }}
      />
      <svg
        viewBox="0 0 800 600"
        className="w-full h-full"
        xmlns="http://www.w3.org/2000/svg"
        preserveAspectRatio="xMidYMid meet"
      >
        <defs>
          <marker id="arr-demo-neutral" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <polygon points="0 0, 6 3, 0 6" fill="#888" />
          </marker>
          <marker id="arr-demo-bfp" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <polygon points="0 0, 6 3, 0 6" fill="#00ff88" />
          </marker>
        </defs>

        {/* Inputs */}
        <motion.g animate={inputsOn ? lit : dim} transition={{ duration: 0.5 }}>
          <rect x={260} y={30} width={280} height={56} rx={6} fill="#1e1e2e" stroke="#888" strokeWidth="1.5" />
          <text x={400} y={57} textAnchor="middle" fill="#aaa" fontSize="13" fontFamily="monospace">Inputs</text>
          <text x={400} y={74} textAnchor="middle" fill="#666" fontSize="11" fontFamily="monospace">email · domain · name · hash</text>
        </motion.g>

        <motion.line
          x1={400} y1={86} x2={400} y2={130}
          stroke="#888" strokeWidth="1.5"
          markerEnd="url(#arr-demo-neutral)"
          animate={osintOn ? lit : dim}
          transition={{ duration: 0.4 }}
        />

        {/* OSINT pipeline */}
        <motion.g animate={osintOn ? lit : dim} transition={{ duration: 0.5 }}>
          <rect x={120} y={134} width={560} height={92} rx={6} fill="#1e1e2e" stroke="#3388ff" strokeWidth="2" />
          <text x={400} y={163} textAnchor="middle" fill="#3388ff" fontSize="15" fontFamily="monospace" fontWeight="bold">OSINT pipeline</text>
          <text x={400} y={183} textAnchor="middle" fill="#aaa" fontSize="11" fontFamily="monospace">{sources} sources · {scanners} scanners · 9 L4 analyzers</text>
          <text x={400} y={201} textAnchor="middle" fill="#888" fontSize="11" fontFamily="monospace">discover · connect · propagate · score · identify</text>
          <text x={400} y={217} textAnchor="middle" fill="#666" fontSize="11" fontFamily="monospace">enrich · fingerprint · locate · cascade · similarity · discovery</text>
        </motion.g>

        <motion.line
          x1={400} y1={226} x2={400} y2={272}
          stroke="#888" strokeWidth="1.5"
          markerEnd="url(#arr-demo-neutral)"
          animate={graphOn ? lit : dim}
          transition={{ duration: 0.4 }}
        />

        {/* Identity graph */}
        <motion.g animate={graphOn ? lit : dim} transition={{ duration: 0.5 }}>
          <rect x={180} y={276} width={440} height={76} rx={6} fill="#1e1e2e" stroke="#888" strokeWidth="1.5" />
          <text x={400} y={302} textAnchor="middle" fill="#aaa" fontSize="13" fontFamily="monospace">Identity graph</text>
          <text x={400} y={321} textAnchor="middle" fill="#888" fontSize="11" fontFamily="monospace">multi-tenant Postgres · pgvector</text>
          <text x={400} y={338} textAnchor="middle" fill="#666" fontSize="11" fontFamily="monospace">accounts · breaches · names · relationships</text>
        </motion.g>

        {/* Split — Reports arrow */}
        <motion.path
          d="M 280 352 L 280 410 L 210 410"
          stroke="#888" strokeWidth="1.5" fill="none"
          markerEnd="url(#arr-demo-neutral)"
          animate={reportsOn ? lit : dim}
          transition={{ duration: 0.5 }}
        />
        {/* Split — BFP arrow (always green when active) */}
        <motion.path
          d="M 520 352 L 520 410 L 590 410"
          stroke="#00ff88" strokeWidth="2" fill="none"
          markerEnd="url(#arr-demo-bfp)"
          animate={bfpOn ? lit : dim}
          transition={{ duration: 0.5 }}
        />

        {/* Reports */}
        <motion.g animate={reportsOn ? lit : dim} transition={{ duration: 0.5 }}>
          <rect x={50} y={386} width={160} height={140} rx={6} fill="#13131c" stroke="#888" strokeWidth="1.5" />
          <text x={130} y={414} textAnchor="middle" fill="#aaa" fontSize="13" fontFamily="monospace">Reports</text>
          <text x={130} y={440} textAnchor="middle" fill="#888" fontSize="11" fontFamily="monospace">5-page PDF</text>
          <text x={130} y={460} textAnchor="middle" fill="#888" fontSize="11" fontFamily="monospace">JSON API</text>
          <text x={130} y={480} textAnchor="middle" fill="#888" fontSize="11" fontFamily="monospace">Plays 1 / 2 / 3</text>
          <text x={130} y={500} textAnchor="middle" fill="#666" fontSize="11" fontFamily="monospace">Operator dashboard</text>
        </motion.g>

        {/* BFP layer — pulses while bfpOn */}
        <motion.g animate={bfpOn ? lit : dim} transition={{ duration: 0.5 }}>
          <rect x={590} y={386} width={160} height={140} rx={6} fill="#00ff8810" stroke="#00ff88" strokeWidth="2" />
          <text x={670} y={414} textAnchor="middle" fill="#00ff88" fontSize="14" fontFamily="monospace" fontWeight="bold">BFP layer</text>
          <text x={670} y={440} textAnchor="middle" fill="#aaa" fontSize="11" fontFamily="monospace">11-axis hash</text>
          <text x={670} y={460} textAnchor="middle" fill="#aaa" fontSize="11" fontFamily="monospace">Append-only log</text>
          <text x={670} y={480} textAnchor="middle" fill="#aaa" fontSize="11" fontFamily="monospace">PQC signatures</text>
          <text x={670} y={500} textAnchor="middle" fill="#aaa" fontSize="11" fontFamily="monospace">Merkle audit</text>
        </motion.g>

        <AnimatePresence>
          {bfpOn && (
            <motion.rect
              key="bfp-pulse"
              x={590} y={386} width={160} height={140} rx={6}
              fill="none" stroke="#00ff88" strokeWidth="2"
              initial={{ opacity: 0 }}
              animate={{ opacity: [0, 0.7, 0] }}
              exit={{ opacity: 0 }}
              transition={{ duration: 2, repeat: Infinity }}
            />
          )}
        </AnimatePresence>
      </svg>
    </div>
  )
}
