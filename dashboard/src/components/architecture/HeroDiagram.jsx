import { motion } from 'framer-motion'
import { SOURCE_COUNT } from '../landing/constants'

// S207 — Hero system diagram (Y3/3 closes /architecture refonte trilogy).
// 5-layer animated reveal of full xposeTIP system at a glance :
//   Inputs → OSINT pipeline → Identity graph → split into Reports + BFP layer.
// Style raccord exact Inversion S204 / BFPLayer S205 / Diagrams.jsx S206 —
// palette 4 colors, viewBox 800×600, fontSize ≥11, strokeWidth 1.5,
// framer-motion whileInView once-only sequenced ~3.5s with subtle BFP pulse.

export default function HeroDiagram() {
  return (
    <div className="relative my-12">
      {/* Subtle background grid raccord avec Hero/Inversion */}
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
        className="w-full max-w-3xl mx-auto h-auto relative z-10"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <marker id="arr-hero-neutral" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <polygon points="0 0, 6 3, 0 6" fill="#888" />
          </marker>
          <marker id="arr-hero-bfp" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <polygon points="0 0, 6 3, 0 6" fill="#00ff88" />
          </marker>
        </defs>

        {/* Layer 1 — Inputs (top, neutral) */}
        <motion.g
          initial={{ opacity: 0, y: -10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <rect x={260} y={30} width={280} height={56} rx={6} fill="#1e1e2e" stroke="#888" strokeWidth="1.5" />
          <text x={400} y={57} textAnchor="middle" fill="#aaa" fontSize="13" fontFamily="monospace">Inputs</text>
          <text x={400} y={74} textAnchor="middle" fill="#666" fontSize="11" fontFamily="monospace">email · domain · name · hash</text>
        </motion.g>

        {/* Arrow Inputs → OSINT */}
        <motion.line
          x1={400} y1={86} x2={400} y2={130}
          stroke="#888" strokeWidth="1.5"
          markerEnd="url(#arr-hero-neutral)"
          initial={{ pathLength: 0 }}
          whileInView={{ pathLength: 1 }}
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.4, delay: 0.5 }}
        />

        {/* Layer 2 — OSINT pipeline (blue accent) */}
        <motion.g
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.5, delay: 0.7 }}
        >
          <rect x={120} y={134} width={560} height={92} rx={6} fill="#1e1e2e" stroke="#3388ff" strokeWidth="2" />
          <text x={400} y={163} textAnchor="middle" fill="#3388ff" fontSize="15" fontFamily="monospace" fontWeight="bold">OSINT pipeline</text>
          <text x={400} y={183} textAnchor="middle" fill="#aaa" fontSize="11" fontFamily="monospace">{`${SOURCE_COUNT} sources · 11 stages · 10 L4 analyzers`}</text>
          <text x={400} y={201} textAnchor="middle" fill="#888" fontSize="11" fontFamily="monospace">discover · connect · propagate · score · identify</text>
          <text x={400} y={217} textAnchor="middle" fill="#666" fontSize="11" fontFamily="monospace">enrich · fingerprint · locate · cascade · similarity · discovery</text>
        </motion.g>

        {/* Arrow OSINT → Identity graph */}
        <motion.line
          x1={400} y1={226} x2={400} y2={272}
          stroke="#888" strokeWidth="1.5"
          markerEnd="url(#arr-hero-neutral)"
          initial={{ pathLength: 0 }}
          whileInView={{ pathLength: 1 }}
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.4, delay: 1.0 }}
        />

        {/* Layer 3 — Identity graph (middle) */}
        <motion.g
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.5, delay: 1.2 }}
        >
          <rect x={180} y={276} width={440} height={76} rx={6} fill="#1e1e2e" stroke="#888" strokeWidth="1.5" />
          <text x={400} y={302} textAnchor="middle" fill="#aaa" fontSize="13" fontFamily="monospace">Identity graph</text>
          <text x={400} y={321} textAnchor="middle" fill="#888" fontSize="11" fontFamily="monospace">multi-tenant Postgres · pgvector</text>
          <text x={400} y={338} textAnchor="middle" fill="#666" fontSize="11" fontFamily="monospace">accounts · breaches · names · relationships</text>
        </motion.g>

        {/* Split arrows : Identity → Reports (left, neutral) + Identity → BFP (right, highlighted) */}
        <motion.path
          d="M 280 352 L 280 410 L 210 410"
          stroke="#888" strokeWidth="1.5" fill="none"
          markerEnd="url(#arr-hero-neutral)"
          initial={{ pathLength: 0 }}
          whileInView={{ pathLength: 1 }}
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.5, delay: 1.5 }}
        />
        <motion.path
          d="M 520 352 L 520 410 L 590 410"
          stroke="#00ff88" strokeWidth="2" fill="none"
          markerEnd="url(#arr-hero-bfp)"
          initial={{ pathLength: 0 }}
          whileInView={{ pathLength: 1 }}
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.5, delay: 1.7 }}
        />

        {/* Layer 4-left — Reports (neutral) */}
        <motion.g
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.5, delay: 1.9 }}
        >
          <rect x={50} y={386} width={160} height={140} rx={6} fill="#13131c" stroke="#888" strokeWidth="1.5" />
          <text x={130} y={414} textAnchor="middle" fill="#aaa" fontSize="13" fontFamily="monospace">Reports</text>
          <text x={130} y={440} textAnchor="middle" fill="#888" fontSize="11" fontFamily="monospace">5-page PDF</text>
          <text x={130} y={460} textAnchor="middle" fill="#888" fontSize="11" fontFamily="monospace">JSON API</text>
          <text x={130} y={480} textAnchor="middle" fill="#888" fontSize="11" fontFamily="monospace">Plays 1 / 2 / 3</text>
          <text x={130} y={500} textAnchor="middle" fill="#666" fontSize="11" fontFamily="monospace">Operator dashboard</text>
        </motion.g>

        {/* Layer 4-right — BFP layer (HIGHLIGHTED, scale-in) */}
        <motion.g
          initial={{ opacity: 0, scale: 0.92 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.6, delay: 2.1 }}
        >
          <rect x={590} y={386} width={160} height={140} rx={6} fill="#00ff8810" stroke="#00ff88" strokeWidth="2" />
          <text x={670} y={414} textAnchor="middle" fill="#00ff88" fontSize="14" fontFamily="monospace" fontWeight="bold">BFP layer</text>
          <text x={670} y={440} textAnchor="middle" fill="#aaa" fontSize="11" fontFamily="monospace">11-axis hash</text>
          <text x={670} y={460} textAnchor="middle" fill="#aaa" fontSize="11" fontFamily="monospace">Append-only log</text>
          <text x={670} y={480} textAnchor="middle" fill="#aaa" fontSize="11" fontFamily="monospace">PQC signatures</text>
          <text x={670} y={500} textAnchor="middle" fill="#aaa" fontSize="11" fontFamily="monospace">Merkle audit</text>
        </motion.g>

        {/* Subtle pulse on BFP after reveal (draws eye) */}
        <motion.rect
          x={590} y={386} width={160} height={140} rx={6}
          fill="none" stroke="#00ff88" strokeWidth="2"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: [0, 0.6, 0] }}
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 2, delay: 2.8, repeat: 1 }}
        />
      </svg>
    </div>
  )
}
