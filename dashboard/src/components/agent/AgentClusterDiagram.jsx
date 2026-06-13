import { motion } from 'framer-motion'

// S302b — illustrative agent-cluster diagram for the public /doc/agent explainer.
// STATIC + illustrative only: representative public agent names, NO data fetch, NO
// getAgentNetwork() call (the live viz stays auth-gated at /agent-network). Reuses
// the exact category palette from AgentNetwork.jsx so explainer + internal viz read
// as one system. House-style raccord with HeroDiagram / EngineFlowDiagram.

const FILL = { shared: '#185FA5', own: '#0F6E56', foreign: '#993C1D', host: '#5F5E5A' }
const vp = { once: true, amount: 0.3 }

// representative public crawler/agent identities — safe to name, NOT workspace data
const HUBS = [
  {
    cat: 'shared', name: 'CLOUDFLARENET', asn: 'AS13335', cx: 270, cy: 250, r: 60,
    agents: [
      { label: 'GPTBot', signed: true, a: -90 },
      { label: 'ChatGPT-User', signed: true, a: -34 },
      { label: 'PerplexityBot', signed: false, a: 22 },
      { label: 'CCBot', signed: false, a: 90 },
      { label: 'Bingbot', signed: false, a: 158 },
      { label: 'Claude-Web', signed: false, a: 214 },
    ],
  },
  {
    cat: 'own', name: 'GOOGLE', asn: 'AS15169', cx: 620, cy: 160, r: 40,
    agents: [
      { label: 'Google-Extended', signed: true, a: -120 },
      { label: 'Amazonbot', signed: false, a: 0 },
      { label: 'ClaudeBot', signed: false, a: 110 },
    ],
  },
  {
    cat: 'foreign', name: 'CHINAMOBILE-CN', asn: 'AS9808', cx: 610, cy: 440, r: 30,
    agents: [
      { label: 'Bytespider', signed: false, a: 30 },
    ],
  },
]

export default function AgentClusterDiagram() {
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
      <svg viewBox="0 0 800 600" className="w-full max-w-3xl mx-auto h-auto relative z-10" xmlns="http://www.w3.org/2000/svg">
        {/* edges (under nodes) */}
        {HUBS.map((h, hi) =>
          h.agents.map((ag, i) => {
            const rad = (ag.a * Math.PI) / 180
            const ax = h.cx + Math.cos(rad) * (h.r + 52)
            const ay = h.cy + Math.sin(rad) * (h.r + 52)
            return (
              <motion.line
                key={`e-${hi}-${i}`} x1={h.cx} y1={h.cy} x2={ax} y2={ay}
                stroke="#1e2a3a" strokeWidth="1.5"
                initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={vp}
                transition={{ duration: 0.4, delay: 0.6 + hi * 0.3 + i * 0.06 }}
              />
            )
          })
        )}

        {/* hubs */}
        {HUBS.map((h, hi) => (
          <motion.g key={`h-${hi}`}
            initial={{ opacity: 0, scale: 0.9 }} whileInView={{ opacity: 1, scale: 1 }} viewport={vp}
            transition={{ duration: 0.5, delay: 0.2 + hi * 0.3 }}>
            <circle cx={h.cx} cy={h.cy} r={h.r} fill={FILL[h.cat]} opacity="0.9" />
            <text x={h.cx} y={h.cy - 2} textAnchor="middle" fill="#fff" fontSize="12" fontFamily="monospace" fontWeight="bold">{h.name}</text>
            <text x={h.cx} y={h.cy + 14} textAnchor="middle" fill="#cfe" fontSize="11" fontFamily="monospace">{h.asn}</text>
          </motion.g>
        ))}

        {/* agent nodes */}
        {HUBS.map((h, hi) =>
          h.agents.map((ag, i) => {
            const rad = (ag.a * Math.PI) / 180
            const ax = h.cx + Math.cos(rad) * (h.r + 52)
            const ay = h.cy + Math.sin(rad) * (h.r + 52)
            return (
              <motion.g key={`a-${hi}-${i}`}
                initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={vp}
                transition={{ duration: 0.4, delay: 0.8 + hi * 0.3 + i * 0.06 }}>
                {/* signed = filled green ring (WBA, verifiable) ; known = hollow */}
                <circle cx={ax} cy={ay} r="11" fill="#10151f"
                  stroke={ag.signed ? '#9bcc3a' : FILL[h.cat]} strokeWidth={ag.signed ? '2.5' : '1.5'} />
                <text x={ax} y={ay + 25} textAnchor="middle" fill="#9aa7bd" fontSize="11" fontFamily="monospace">{ag.label}</text>
              </motion.g>
            )
          })
        )}
      </svg>

      {/* legend */}
      <div className="flex gap-4 flex-wrap justify-center mt-3 text-[11px] font-mono text-gray-400">
        <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full inline-block" style={{ background: FILL.shared }} />shared CDN</span>
        <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full inline-block" style={{ background: FILL.own }} />own ASN / hyperscaler</span>
        <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full inline-block" style={{ background: FILL.foreign }} />foreign network</span>
        <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full inline-block" style={{ background: FILL.host }} />3rd-party host</span>
        <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full inline-block border-2 border-[#9bcc3a]" />signed · Web Bot Auth</span>
      </div>
    </div>
  )
}
