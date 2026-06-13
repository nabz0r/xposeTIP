import { motion } from 'framer-motion'

// S301b — Engine flow diagram. Depicts how one email seed rotates through the
// producer systems and resolves into a scored identity:
//   email → DISPATCH (Celery chord) → MULTI-PASS → SCORING → scored identity.
// Side annotation = infra rotation (key substitution + ddgs backend rotation)
// feeding the DISPATCH box. Style raccord exact with architecture/HeroDiagram.jsx —
// faint #00ff88 grid bg, viewBox, fontSize ≥11, strokeWidth 1.5, framer-motion
// whileInView once-only sequenced reveal. NO proxy-rotation (none exists in code).

const vp = { once: true, amount: 0.3 }

export default function EngineFlowDiagram() {
  return (
    <div className="relative my-12">
      <div
        className="absolute inset-0 opacity-[0.02] pointer-events-none"
        style={{
          backgroundImage:
            'linear-gradient(#00ff88 1px, transparent 1px), linear-gradient(90deg, #00ff88 1px, transparent 1px)',
          backgroundSize: '60px 60px',
        }}
      />
      <svg
        viewBox="0 0 800 640"
        className="w-full max-w-3xl mx-auto h-auto relative z-10"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <marker id="arr-eng-neutral" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <polygon points="0 0, 6 3, 0 6" fill="#888" />
          </marker>
          <marker id="arr-eng-green" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <polygon points="0 0, 6 3, 0 6" fill="#00ff88" />
          </marker>
          <marker id="arr-eng-infra" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <polygon points="0 0, 6 3, 0 6" fill="#aa66ff" />
          </marker>
        </defs>

        {/* email seed */}
        <motion.g initial={{ opacity: 0, y: -10 }} whileInView={{ opacity: 1, y: 0 }} viewport={vp} transition={{ duration: 0.5, delay: 0.2 }}>
          <rect x={300} y={20} width={200} height={46} rx={6} fill="#1e1e2e" stroke="#888" strokeWidth="1.5" />
          <text x={400} y={42} textAnchor="middle" fill="#aaa" fontSize="13" fontFamily="monospace">email seed</text>
          <text x={400} y={59} textAnchor="middle" fill="#666" fontSize="11" fontFamily="monospace">one identifier in</text>
        </motion.g>

        <motion.line x1={400} y1={66} x2={400} y2={100} stroke="#888" strokeWidth="1.5" markerEnd="url(#arr-eng-neutral)"
          initial={{ pathLength: 0 }} whileInView={{ pathLength: 1 }} viewport={vp} transition={{ duration: 0.4, delay: 0.5 }} />

        {/* infra rotation side-annotation (feeds DISPATCH) */}
        <motion.g initial={{ opacity: 0, x: -10 }} whileInView={{ opacity: 1, x: 0 }} viewport={vp} transition={{ duration: 0.5, delay: 1.3 }}>
          <rect x={18} y={108} width={118} height={86} rx={6} fill="#aa66ff0d" stroke="#aa66ff" strokeWidth="1.5" strokeDasharray="3 3" />
          <text x={77} y={130} textAnchor="middle" fill="#aa66ff" fontSize="11" fontFamily="monospace" fontWeight="bold">infra rotation</text>
          <text x={77} y={150} textAnchor="middle" fill="#9a7bd0" fontSize="11" fontFamily="monospace">key subst.</text>
          <text x={77} y={167} textAnchor="middle" fill="#9a7bd0" fontSize="11" fontFamily="monospace">S217 guard</text>
          <text x={77} y={184} textAnchor="middle" fill="#9a7bd0" fontSize="11" fontFamily="monospace">ddgs rotation</text>
        </motion.g>
        <motion.line x1={136} y1={151} x2={158} y2={151} stroke="#aa66ff" strokeWidth="1.5" strokeDasharray="3 3" markerEnd="url(#arr-eng-infra)"
          initial={{ pathLength: 0 }} whileInView={{ pathLength: 1 }} viewport={vp} transition={{ duration: 0.4, delay: 1.6 }} />

        {/* DISPATCH (blue accent) */}
        <motion.g initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={vp} transition={{ duration: 0.5, delay: 0.7 }}>
          <rect x={160} y={104} width={480} height={108} rx={6} fill="#1e1e2e" stroke="#3388ff" strokeWidth="2" />
          <text x={400} y={130} textAnchor="middle" fill="#3388ff" fontSize="15" fontFamily="monospace" fontWeight="bold">DISPATCH</text>
          <text x={400} y={150} textAnchor="middle" fill="#aaa" fontSize="11" fontFamily="monospace">Celery chord — parallel fan-out</text>
          <text x={400} y={170} textAnchor="middle" fill="#888" fontSize="11" fontFamily="monospace">27 scanners · scraper_engine ▶ 174 URL-templates</text>
          <text x={400} y={189} textAnchor="middle" fill="#666" fontSize="11" fontFamily="monospace">12 api-modules → Pass 2</text>
        </motion.g>

        <motion.line x1={400} y1={212} x2={400} y2={246} stroke="#888" strokeWidth="1.5" markerEnd="url(#arr-eng-neutral)"
          initial={{ pathLength: 0 }} whileInView={{ pathLength: 1 }} viewport={vp} transition={{ duration: 0.4, delay: 0.95 }} />

        {/* MULTI-PASS */}
        <motion.g initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={vp} transition={{ duration: 0.5, delay: 1.15 }}>
          <rect x={170} y={250} width={460} height={82} rx={6} fill="#1e1e2e" stroke="#888" strokeWidth="1.5" />
          <text x={400} y={277} textAnchor="middle" fill="#aaa" fontSize="13" fontFamily="monospace">MULTI-PASS</text>
          <text x={400} y={298} textAnchor="middle" fill="#888" fontSize="11" fontFamily="monospace">Pass 1 ▶ Pass 1.5 (derive / re-scan)</text>
          <text x={400} y={316} textAnchor="middle" fill="#666" fontSize="11" fontFamily="monospace">▶ Pass 2 (name-based, after resolution)</text>
        </motion.g>

        <motion.line x1={400} y1={332} x2={400} y2={366} stroke="#888" strokeWidth="1.5" markerEnd="url(#arr-eng-neutral)"
          initial={{ pathLength: 0 }} whileInView={{ pathLength: 1 }} viewport={vp} transition={{ duration: 0.4, delay: 1.85 }} />

        {/* SCORING (green accent) */}
        <motion.g initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={vp} transition={{ duration: 0.5, delay: 2.05 }}>
          <rect x={120} y={370} width={560} height={96} rx={6} fill="#00ff8810" stroke="#00ff88" strokeWidth="2" />
          <text x={400} y={397} textAnchor="middle" fill="#00ff88" fontSize="15" fontFamily="monospace" fontWeight="bold">SCORING</text>
          <text x={400} y={418} textAnchor="middle" fill="#aaa" fontSize="11" fontFamily="monospace">reliability ▶ cross-verify ▶ PageRank(0.85)</text>
          <text x={400} y={437} textAnchor="middle" fill="#888" fontSize="11" fontFamily="monospace">▶ collision-guard ▶ coherence cap</text>
          <text x={400} y={455} textAnchor="middle" fill="#666" fontSize="11" fontFamily="monospace">corroboration is confidence — not volume</text>
        </motion.g>

        <motion.line x1={400} y1={466} x2={400} y2={500} stroke="#00ff88" strokeWidth="2" markerEnd="url(#arr-eng-green)"
          initial={{ pathLength: 0 }} whileInView={{ pathLength: 1 }} viewport={vp} transition={{ duration: 0.4, delay: 2.5 }} />

        {/* scored identity (highlighted, scale-in) */}
        <motion.g initial={{ opacity: 0, scale: 0.92 }} whileInView={{ opacity: 1, scale: 1 }} viewport={vp} transition={{ duration: 0.6, delay: 2.7 }}>
          <rect x={260} y={504} width={280} height={68} rx={6} fill="#00ff8810" stroke="#00ff88" strokeWidth="2" />
          <text x={400} y={531} textAnchor="middle" fill="#00ff88" fontSize="14" fontFamily="monospace" fontWeight="bold">scored identity</text>
          <text x={400} y={551} textAnchor="middle" fill="#aaa" fontSize="11" fontFamily="monospace">exposure + threat</text>
          <text x={400} y={567} textAnchor="middle" fill="#888" fontSize="11" fontFamily="monospace">operator-asserted = 100% ceiling</text>
        </motion.g>

        {/* subtle pulse on the final node */}
        <motion.rect x={260} y={504} width={280} height={68} rx={6} fill="none" stroke="#00ff88" strokeWidth="2"
          initial={{ opacity: 0 }} whileInView={{ opacity: [0, 0.6, 0] }} viewport={vp} transition={{ duration: 2, delay: 3.4, repeat: 1 }} />
      </svg>
    </div>
  )
}
