import { motion } from 'framer-motion'
import { ExternalLink } from 'lucide-react'
import { SOURCE_COUNT } from '../landing/constants'
import Section from '../shared/Section'

// S205 — BFPLayer section on /architecture (Y1/3 progressive refonte).
// Closes the BFP gap : before this sprint, BFP appeared on /architecture
// only as a trailing sentence in StageSimilarity. Now a dedicated section
// inserted between StageDiscovery and ScraperBreakdown — narrative + 1
// system-layers diagram + 4 locked properties + pointage /bfp.
// Style raccord exact Inversion S204 (framer-motion whileInView once-only,
// 4-color palette, viewBox 600×400, fontSize ≥11).

const BFP_PROPERTIES = [
  '11-axis behavioral fingerprint (BFP_v0.2 spec)',
  'Cross-source convergence (≥ N independent scrapers) for trust signals',
  'Append-only claim log with SHA-3 Merkle audit (RFC 6962)',
  'Post-quantum signatures from day one — SPHINCS+ / ML-DSA / ML-KEM',
]

export default function BFPLayer() {
  return (
    <Section className="py-32 bg-[#0d0d14]">
      <div className="max-w-5xl mx-auto px-6">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          {/* === Left — narrative === */}
          <div>
            <div className="inline-block text-[10px] font-mono text-[#00ff88] bg-[#00ff88]/10 px-2 py-0.5 rounded-full mb-3">
              LAYER — PROTOCOL
            </div>
            <h2 className="text-3xl md:text-4xl font-bold mb-4 font-['Instrument_Sans',sans-serif]">
              BFP — the behavioral fingerprint layer
            </h2>
            <p className="text-gray-400 mb-4 leading-relaxed">
              Above the OSINT pipeline runs a second layer. While the pipeline
              collects what is <span className="text-white">visible</span>, BFP
              measures <span className="text-white">who someone is</span> —
              across 11 axes, forgery-resistant, append-only.
            </p>
            <p className="text-gray-500 text-sm mb-6 leading-relaxed">
              The pipeline answers "what data points exist about this person."
              BFP answers "do these data points converge on a single behavioral
              fingerprint?" — the foundation for cross-scan identity continuity
              and the building block of the long-term protocol layer.
            </p>

            <ul className="space-y-2.5 text-sm text-gray-300 mb-7">
              {BFP_PROPERTIES.map((p, i) => (
                <motion.li
                  key={i}
                  className="flex items-start gap-2.5"
                  initial={{ opacity: 0, x: -10 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true, amount: 0.4 }}
                  transition={{ duration: 0.4, delay: 0.1 * i }}
                >
                  <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-[#00ff88] flex-shrink-0" />
                  <span>{p}</span>
                </motion.li>
              ))}
            </ul>

            <a
              href="/doc/bfp"
              className="inline-flex items-center gap-2 text-[#00ff88] hover:text-[#00ff88]/80 text-sm font-mono transition-colors"
            >
              Read the full BFP protocol spec
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>

          {/* === Right — system layers diagram === */}
          <div>
            <BFPLayerDiagram />
          </div>
        </div>
      </div>
    </Section>
  )
}

function BFPLayerDiagram() {
  return (
    <svg
      viewBox="0 0 600 400"
      className="w-full max-w-md mx-auto h-auto"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <marker id="arr-neutral" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
          <polygon points="0 0, 6 3, 0 6" fill="#888" />
        </marker>
        <marker id="arr-bfp" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
          <polygon points="0 0, 6 3, 0 6" fill="#00ff88" />
        </marker>
      </defs>

      {/* Inputs box (top) */}
      <motion.g
        initial={{ opacity: 0, y: -8 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, amount: 0.3 }}
        transition={{ duration: 0.5 }}
      >
        <rect x={150} y={20} width={300} height={56} rx={6} fill="#1e1e2e" stroke="#888" strokeWidth="1" />
        <text x={300} y={47} textAnchor="middle" fill="#aaa" fontSize="13" fontFamily="monospace">Inputs</text>
        <text x={300} y={64} textAnchor="middle" fill="#666" fontSize="11" fontFamily="monospace">email · domain · name · hash</text>
      </motion.g>

      {/* Arrow Inputs → OSINT */}
      <motion.line
        x1={300} y1={76} x2={300} y2={116}
        stroke="#888" strokeWidth="1.5"
        markerEnd="url(#arr-neutral)"
        initial={{ pathLength: 0 }}
        whileInView={{ pathLength: 1 }}
        viewport={{ once: true, amount: 0.3 }}
        transition={{ duration: 0.5, delay: 0.3 }}
      />

      {/* OSINT pipeline box (middle) */}
      <motion.g
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true, amount: 0.3 }}
        transition={{ duration: 0.5, delay: 0.5 }}
      >
        <rect x={70} y={120} width={460} height={84} rx={6} fill="#1e1e2e" stroke="#3388ff" strokeWidth="1.5" />
        <text x={300} y={148} textAnchor="middle" fill="#3388ff" fontSize="14" fontFamily="monospace" fontWeight="bold">OSINT pipeline</text>
        <text x={300} y={168} textAnchor="middle" fill="#888" fontSize="11" fontFamily="monospace">{`${SOURCE_COUNT} sources · 11 stages · identity graph`}</text>
        <text x={300} y={186} textAnchor="middle" fill="#666" fontSize="11" fontFamily="monospace">discover · connect · identify · score</text>
      </motion.g>

      {/* Arrow OSINT → Reports (neutral, left split) */}
      <motion.path
        d="M 200 204 L 200 250 L 170 250"
        stroke="#888" strokeWidth="1.5" fill="none"
        markerEnd="url(#arr-neutral)"
        initial={{ pathLength: 0 }}
        whileInView={{ pathLength: 1 }}
        viewport={{ once: true, amount: 0.3 }}
        transition={{ duration: 0.6, delay: 0.8 }}
      />

      {/* Arrow OSINT → BFP (highlighted green, right split) */}
      <motion.path
        d="M 400 204 L 400 250 L 430 250"
        stroke="#00ff88" strokeWidth="2" fill="none"
        markerEnd="url(#arr-bfp)"
        initial={{ pathLength: 0 }}
        whileInView={{ pathLength: 1 }}
        viewport={{ once: true, amount: 0.3 }}
        transition={{ duration: 0.6, delay: 1.0 }}
      />

      {/* Reports box (bottom-left, neutral) */}
      <motion.g
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true, amount: 0.3 }}
        transition={{ duration: 0.5, delay: 1.2 }}
      >
        <rect x={50} y={232} width={170} height={114} rx={6} fill="#13131c" stroke="#888" strokeWidth="1" />
        <text x={135} y={260} textAnchor="middle" fill="#aaa" fontSize="13" fontFamily="monospace">Reports</text>
        <text x={135} y={282} textAnchor="middle" fill="#666" fontSize="11" fontFamily="monospace">5-page PDF</text>
        <text x={135} y={302} textAnchor="middle" fill="#666" fontSize="11" fontFamily="monospace">JSON API</text>
        <text x={135} y={322} textAnchor="middle" fill="#666" fontSize="11" fontFamily="monospace">Plays 1 / 2 / 3</text>
      </motion.g>

      {/* BFP Layer box (bottom-right, HIGHLIGHTED) */}
      <motion.g
        initial={{ opacity: 0, scale: 0.92 }}
        whileInView={{ opacity: 1, scale: 1 }}
        viewport={{ once: true, amount: 0.3 }}
        transition={{ duration: 0.6, delay: 1.4 }}
      >
        <rect x={380} y={232} width={170} height={134} rx={6} fill="#00ff8810" stroke="#00ff88" strokeWidth="2" />
        <text x={465} y={260} textAnchor="middle" fill="#00ff88" fontSize="14" fontFamily="monospace" fontWeight="bold">BFP layer</text>
        <text x={465} y={282} textAnchor="middle" fill="#aaa" fontSize="11" fontFamily="monospace">11-axis hash</text>
        <text x={465} y={302} textAnchor="middle" fill="#aaa" fontSize="11" fontFamily="monospace">Append-only log</text>
        <text x={465} y={322} textAnchor="middle" fill="#aaa" fontSize="11" fontFamily="monospace">PQC signatures</text>
        <text x={465} y={342} textAnchor="middle" fill="#aaa" fontSize="11" fontFamily="monospace">Merkle audit</text>
      </motion.g>
    </svg>
  )
}
