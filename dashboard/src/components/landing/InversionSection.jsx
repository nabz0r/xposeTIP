import { motion } from 'framer-motion'
import Section from '../shared/Section'

// S204 — Inversion section. Materializes the foundational vision locked
// 2026-05-22: "The internet knows who you are. Everyone knows who you
// are. Except you." Animated SVG via Framer Motion with scroll-trigger.

const EXTRACTORS = [
  { id: 'brokers',      label: 'Data brokers',     angle: 30  },
  { id: 'platforms',    label: 'Social platforms', angle: 90  },
  { id: 'surveillance', label: 'Surveillance',     angle: 150 },
  { id: 'breaches',     label: 'Breaches',         angle: 210 },
  { id: 'search',       label: 'Search engines',   angle: 270 },
  { id: 'records',      label: 'Public records',   angle: 330 },
]

const CENTER = { x: 300, y: 300 }
const SUBJECT_R = 40
const RING_R = SUBJECT_R + 28
const ACTOR_DIST = 240

const actorPos = (angle) => {
  const rad = (angle * Math.PI) / 180
  return { x: CENTER.x + Math.cos(rad) * ACTOR_DIST, y: CENTER.y + Math.sin(rad) * ACTOR_DIST }
}

const arrowEnd = (angle, dist) => {
  const rad = (angle * Math.PI) / 180
  return { x: CENTER.x + Math.cos(rad) * dist, y: CENTER.y + Math.sin(rad) * dist }
}

export default function InversionSection() {
  return (
    <Section className="py-32 relative overflow-hidden">
      {/* Background grid — raccord exact with Hero */}
      <div
        className="absolute inset-0 opacity-[0.02] pointer-events-none"
        style={{
          backgroundImage:
            'linear-gradient(#00ff88 1px, transparent 1px), linear-gradient(90deg, #00ff88 1px, transparent 1px)',
          backgroundSize: '60px 60px',
        }}
      />

      <div className="max-w-5xl mx-auto px-6 relative z-10">
        {/* SVG visual — the inversion */}
        <div className="flex justify-center mb-16">
          <svg viewBox="0 0 600 600" className="w-full max-w-xl h-auto" xmlns="http://www.w3.org/2000/svg">
            {/* === State 1 : extraction arrows pointing IN (asymmetry) === */}
            {EXTRACTORS.map((e, i) => {
              const start = actorPos(e.angle)
              const end = arrowEnd(e.angle, SUBJECT_R + 8)
              return (
                <motion.line
                  key={`in-${e.id}`}
                  x1={start.x} y1={start.y}
                  x2={end.x}   y2={end.y}
                  stroke="#ff5588"
                  strokeWidth="1.5"
                  strokeOpacity="0.55"
                  initial={{ pathLength: 0, opacity: 0 }}
                  whileInView={{ pathLength: 1, opacity: 0.55 }}
                  viewport={{ once: true, amount: 0.4 }}
                  transition={{ duration: 0.7, delay: 0.1 * i }}
                />
              )
            })}

            {/* Subject central */}
            <motion.circle
              cx={CENTER.x} cy={CENTER.y} r={SUBJECT_R}
              fill="#0a0a0f"
              stroke="#666"
              strokeWidth="1"
              initial={{ scale: 0, opacity: 0 }}
              whileInView={{ scale: 1, opacity: 1 }}
              viewport={{ once: true, amount: 0.4 }}
              transition={{ duration: 0.5 }}
            />
            <motion.text
              x={CENTER.x} y={CENTER.y + 5}
              textAnchor="middle"
              fill="#888"
              fontSize="14"
              fontFamily="monospace"
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true, amount: 0.4 }}
              transition={{ duration: 0.4, delay: 0.3 }}
            >
              you
            </motion.text>

            {/* === State 2 : BFP ring + symmetry arrows pointing OUT === */}
            <motion.circle
              cx={CENTER.x} cy={CENTER.y} r={RING_R}
              fill="none"
              stroke="#00ff88"
              strokeWidth="2"
              initial={{ scale: 0, opacity: 0 }}
              whileInView={{ scale: 1, opacity: 1 }}
              viewport={{ once: true, amount: 0.4 }}
              transition={{ duration: 0.9, delay: 1.2 }}
            />

            {EXTRACTORS.map((e, i) => {
              const start = arrowEnd(e.angle, RING_R)
              const end = arrowEnd(e.angle, ACTOR_DIST - 24)
              return (
                <motion.line
                  key={`out-${e.id}`}
                  x1={start.x} y1={start.y}
                  x2={end.x}   y2={end.y}
                  stroke="#00ff88"
                  strokeWidth="1.5"
                  strokeOpacity="0.85"
                  strokeDasharray="4 2"
                  initial={{ pathLength: 0, opacity: 0 }}
                  whileInView={{ pathLength: 1, opacity: 0.85 }}
                  viewport={{ once: true, amount: 0.4 }}
                  transition={{ duration: 0.7, delay: 1.6 + 0.08 * i }}
                />
              )
            })}

            {/* Actor labels */}
            {EXTRACTORS.map((e, i) => {
              const pos = actorPos(e.angle)
              return (
                <motion.text
                  key={`label-${e.id}`}
                  x={pos.x} y={pos.y}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  fill="#666"
                  fontSize="11"
                  fontFamily="monospace"
                  initial={{ opacity: 0 }}
                  whileInView={{ opacity: 1 }}
                  viewport={{ once: true, amount: 0.4 }}
                  transition={{ duration: 0.4, delay: 0.15 + 0.1 * i }}
                >
                  {e.label}
                </motion.text>
              )
            })}
          </svg>
        </div>

        {/* Headline */}
        <div className="max-w-3xl mx-auto text-center">
          <motion.h2
            className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight leading-[1.15] mb-6 font-['Instrument_Sans',sans-serif]"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.3 }}
            transition={{ duration: 0.6 }}
          >
            The internet knows who you are.<br />
            Everyone knows who you are.<br />
            <span className="text-[#00ff88]">Except you.</span>
          </motion.h2>

          {/* S251 — shock-stat: quantifies the asymmetry's human cost.
              Sourced (ITRC 2024), one number only, never FUD. Sequenced
              after the headline and before the answer line. */}
          <motion.div
            className="max-w-lg mx-auto mb-6"
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.3 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <p className="text-xl md:text-2xl text-gray-300 leading-snug">
              Nearly <span className="text-[#ff5588] font-bold">half</span> of identity-theft
              victims who sought help were still unresolved a year later.
            </p>
            <p className="text-xs text-gray-600 mt-2 font-mono">— Identity Theft Resource Center, 2024</p>
          </motion.div>

          <motion.p
            className="text-lg text-gray-400 max-w-lg mx-auto"
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true, amount: 0.3 }}
            transition={{ duration: 0.6, delay: 0.45 }}
          >
            BFP returns this knowledge to you.
          </motion.p>
        </div>
      </div>
    </Section>
  )
}
