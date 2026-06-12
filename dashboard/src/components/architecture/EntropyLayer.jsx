import { motion } from 'framer-motion'
import Section from '../shared/Section'

// S276 — EntropyLayer section on /architecture, inserted between BFPLayer and
// VisualizationLayer. Surfaces the entropy layer (S265-S272) that was invisible
// on the page: narrative + the bits ledger diagram + the 5 governors.
// Copy source of truth: api/services/layer4/entropy_engine.py docstring (l.3-25).
// Style raccord exact BFPLayer (S205): Section py-32 (default bg for alternation),
// max-w-5xl, grid md:grid-cols-2, badge pill, framer-motion whileInView once-only,
// viewBox 600×400, fontSize ≥ 11. Diagram is 100% illustrative — no live/API data.

const GOVERNORS = [
  'Bits per axis = −log2(p) — prevalence of the observed value, from public priors',
  'Distinct axes only — correlated signals are pick-one or discounted, never double-counted',
  'Conservative priors — uncertainty rounds toward common; unknown axis = 0 bits, never a guess',
  'Hard cap — OSINT-only tops out at ~20 bits (anonymity set ~1M); global uniqueness is never asserted',
  'Descriptive, not punitive — bits inform the ledger; the risk score is computed independently',
]

export default function EntropyLayer() {
  return (
    <Section className="py-32">
      <div className="max-w-5xl mx-auto px-6">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          {/* === Left — narrative === */}
          <div>
            <div className="inline-block text-[10px] font-mono text-[#3388ff] bg-[#3388ff]/10 px-2 py-0.5 rounded-full mb-3">
              LAYER — MEASUREMENT
            </div>
            <h2 className="text-3xl md:text-4xl font-bold mb-4 font-['Instrument_Sans',sans-serif]">
              Entropy — identity measured in bits
            </h2>
            <p className="text-gray-400 mb-4 leading-relaxed">
              A random human is ~33 bits of information — 2³³ ≈ world population.
              Every fact the open web resolves about you removes bits: your country,
              your email provider, your first name. The entropy engine turns every
              finding into a number: <span className="text-white">how many of your
              bits are already out</span>.
            </p>
            <p className="text-gray-500 text-sm mb-6 leading-relaxed">
              It reads the same findings as the pipeline, but answers a different
              question. Not "what exists" — <em>how identifying is it</em>. The output
              is a per-axis ledger: bits, source, and what to do about each one. Shown
              to the subject as a ledger — not held over them.
            </p>

            <ul className="space-y-2.5 text-sm text-gray-300 mb-6">
              {GOVERNORS.map((g, i) => (
                <motion.li
                  key={i}
                  className="flex items-start gap-2.5"
                  initial={{ opacity: 0, x: -10 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true, amount: 0.4 }}
                  transition={{ duration: 0.4, delay: 0.1 * i }}
                >
                  <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-[#3388ff] flex-shrink-0" />
                  <span>{g}</span>
                </motion.li>
              ))}
            </ul>

            <div className="text-xs text-gray-600 space-y-1.5 mb-6">
              <p>
                Feeds on the BFP layer: the behavioral hash becomes a belonging term
                — H(cluster), how many bits your bucket carries.
              </p>
              <p>
                Feeds on breach exposure: composition shapes only, extract-and-drop —
                no cleartext ever stored.
              </p>
            </div>

            <a
              href="/"
              className="inline-flex items-center gap-2 text-[#3388ff] hover:text-[#3388ff]/80 text-sm font-mono transition-colors"
            >
              See your own ledger →
            </a>
          </div>

          {/* === Right — the bits ledger diagram === */}
          <div>
            <EntropyLedgerDiagram />
          </div>
        </div>
      </div>
    </Section>
  )
}

// Illustrative bits ledger. x-origin at 150 (= 0 bits), scale 12 px/bit so the
// 33-bit axis lands at x=546. Bar values sum to 18 distinct bits — deliberately
// UNDER the ~20 cap so governor 4 reads correctly on the picture.
const X0 = 150
const K = 12 // px per bit
const xb = (bits) => X0 + K * bits

const BARS = [
  { label: 'country', bits: 4, color: '#3388ff', end: '≈4 b · −log2(p)' },
  { label: 'email provider', bits: 3, color: '#3388ff', end: '≈3 b' },
  { label: 'name (coarse)', bits: 5, color: '#3388ff', end: '≈5 b' },
  { label: 'H(cluster) — BFP', bits: 6, color: '#00ff88', end: '≈6 b' },
  { label: 'correlated', bits: 2, color: '#888', end: '≈2 b · discounted (0 counted)', discounted: true },
]
const BAR_Y0 = 70
const BAR_H = 28
const BAR_GAP = 10
const SIGMA_BITS = 18

function EntropyLedgerDiagram() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.3 }}
      transition={{ duration: 0.6 }}
    >
      <svg
        viewBox="0 0 600 400"
        className="w-full max-w-md mx-auto h-auto"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* cap line (~20 bits, OSINT ceiling) */}
        <line x1={xb(20)} y1={56} x2={xb(20)} y2={292} stroke="#ff5588" strokeWidth="1.5" strokeDasharray="4 4" />
        <text x={xb(20) - 6} y={30} textAnchor="end" fill="#ff5588" fontSize="11" fontFamily="monospace">
          cap ~20 bits — OSINT ceiling
        </text>

        {/* 33-bit line (one human) */}
        <line x1={xb(33)} y1={56} x2={xb(33)} y2={292} stroke="#888" strokeWidth="1.5" strokeDasharray="4 4" />
        <text x={xb(33) - 2} y={48} textAnchor="end" fill="#888" fontSize="11" fontFamily="monospace">
          ~33 bits ≈ one human
        </text>

        {/* bars */}
        {BARS.map((b, i) => {
          const y = BAR_Y0 + i * (BAR_H + BAR_GAP)
          const mid = y + BAR_H / 2 + 4
          return (
            <g key={b.label}>
              {/* faint full-scale track */}
              <rect x={X0} y={y} width={xb(33) - X0} height={BAR_H} rx={3} fill="#ffffff" opacity={0.04} />
              {/* value bar */}
              <rect
                x={X0}
                y={y}
                width={K * b.bits}
                height={BAR_H}
                rx={3}
                fill={b.color}
                opacity={b.discounted ? 0.35 : 0.85}
              />
              {/* left axis label */}
              <text x={X0 - 8} y={mid} textAnchor="end" fill="#aaa" fontSize="11" fontFamily="monospace">
                {b.label}
              </text>
              {/* right value label */}
              <text x={X0 + K * b.bits + 8} y={mid} textAnchor="start" fill={b.discounted ? '#888' : b.color} fontSize="11" fontFamily="monospace">
                {b.end}
              </text>
            </g>
          )
        })}

        {/* Σ distinct axes marker — lands under the cap */}
        <line x1={X0} y1={262} x2={xb(SIGMA_BITS)} y2={262} stroke="#dddddd" strokeWidth="1.5" />
        <line x1={X0} y1={258} x2={X0} y2={266} stroke="#dddddd" strokeWidth="1.5" />
        <line x1={xb(SIGMA_BITS)} y1={258} x2={xb(SIGMA_BITS)} y2={266} stroke="#dddddd" strokeWidth="1.5" />
        <text x={(X0 + xb(SIGMA_BITS)) / 2} y={280} textAnchor="middle" fill="#dddddd" fontSize="11" fontFamily="monospace">
          Σ distinct axes ≈ 18 bits
        </text>

        {/* horizontal bits axis */}
        <line x1={X0} y1={292} x2={560} y2={292} stroke="#888" strokeWidth="1.5" />
        {[0, 10, 20, 33].map((t) => (
          <g key={t}>
            <line x1={xb(t)} y1={292} x2={xb(t)} y2={298} stroke="#888" strokeWidth="1.5" />
            <text x={xb(t)} y={312} textAnchor="middle" fill="#888" fontSize="11" fontFamily="monospace">
              {t}
            </text>
          </g>
        ))}
        <text x={xb(33)} y={312} textAnchor="middle" fill="#888" fontSize="11" fontFamily="monospace" dx={0} dy={16}>
          bits
        </text>

        {/* legend */}
        <text x={300} y={364} textAnchor="middle" fill="#888" fontSize="11" fontFamily="monospace">
          Illustrative values — real ledger is per-target, in the Entropy tab
        </text>
      </svg>
    </motion.div>
  )
}
