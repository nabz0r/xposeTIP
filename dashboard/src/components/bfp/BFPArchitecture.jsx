import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { SOURCE_COUNT } from '../landing/constants'

// S242 — Each entry carries the trust + threat model that drives the
// crossfading block below the parallels row. BFP is the resting state
// (default + on mouse-leave), so its content matches the prior static block.
const PARALLELS = [
  {
    name: 'DNS', what: 'Resolves domains',
    trustTitle: 'Hierarchical delegation',
    trust: [
      'Root → TLD → authoritative chain of delegation',
      'DNSSEC signs records — verifiable chain of trust',
      'No single owner — distributed authority',
      'Resolvers cache with TTLs; billions of queries/day',
    ],
    threatTitle: 'Spoofing & poisoning',
    threat: [
      'Cache poisoning injects forged records',
      'On-path spoofing of unsigned answers',
      'DNSSEC validation mitigates',
      'Redundant resolvers limit single points of failure',
    ],
  },
  {
    name: 'Certificate Transparency', what: 'Verifies TLS certs',
    trustTitle: 'Public append-only logs',
    trust: [
      'Every issued certificate logged publicly',
      'Multiple independent log operators',
      'Merkle inclusion + consistency proofs',
      'Browsers require SCTs to trust a cert',
    ],
    threatTitle: 'Misissuance detection',
    threat: [
      'Rogue / misissued certificates',
      'Detected by public monitors, not prevented',
      'Gossip protocols cross-check logs',
      'Auditable by anyone, after the fact',
    ],
  },
  {
    name: 'MISP', what: 'Shares threat indicators',
    trustTitle: 'Federated communities',
    trust: [
      'Trust groups exchange structured indicators',
      'Source attribution on every indicator',
      'Taxonomies + confidence levels',
      'No central authority — peer federation',
    ],
    threatTitle: 'Indicator poisoning',
    threat: [
      'False or stale indicators degrade trust',
      'Oversharing leaks sensitive context',
      'Sightings + confidence scoring filter noise',
      'Distribution levels scope what is shared',
    ],
  },
  {
    name: 'BFP', what: 'Resolves identities', accent: true,
    trustTitle: 'Certificate Transparency-like',
    trust: [
      'Evidence-based consensus (≥ N independent scrapers converge)',
      'Append-only log of claims (Certificate Transparency-style)',
      'No proof-of-work — energy-light by design',
      'Audit trail traceable to each source',
    ],
    threatTitle: 'Conservative-by-design',
    threat: [
      'Conservative-by-design — absorbs unknown future threats',
      'Threat model emerges from supply-chain position',
      'Post-quantum cryptography from day one (NIST 2024)',
      'Multi-source convergence resists single-source poisoning',
    ],
  },
]

export default function BFPArchitecture() {
  const [active, setActive] = useState(PARALLELS.length - 1) // BFP is the resting state
  const ap = PARALLELS[active]
  return (
    <div className="max-w-5xl mx-auto px-6">
      <div className="text-center mb-16">
        <div className="text-xs font-mono text-[#00ff88]/70 uppercase tracking-wider mb-3">Architecture</div>
        <h2 className="text-3xl md:text-4xl font-bold mb-4 font-['Instrument_Sans',sans-serif]">
          Two layers, one protocol
        </h2>
        <p className="text-sm text-gray-500 max-w-2xl mx-auto leading-relaxed">
          The reference implementation runs in the cloud where business logic lives.
          The protocol itself runs locally on operator hardware — the same separation as CT logs, Bitcoin nodes, and MISP instances.
        </p>
      </div>

      {/* Two-layer split */}
      <div className="grid md:grid-cols-2 gap-6 mb-12">
        <div className="p-6 bg-[#13131c] border border-[#1e1e2e] rounded-lg">
          <div className="text-xs font-mono text-gray-500 uppercase tracking-wider mb-2">Layer</div>
          <h3 className="text-lg font-bold text-white mb-4 font-['Instrument_Sans',sans-serif]">
            xposeTIP cloud
          </h3>
          <p className="text-sm text-gray-400 leading-relaxed mb-4">
            Business and operator experience. Cloud-native, multi-tenant, evolves with the product roadmap.
          </p>
          <ul className="space-y-2 text-sm text-gray-300">
            <li className="flex items-start gap-2"><span className="text-gray-600 mt-1">·</span>Data collection ({SOURCE_COUNT} scrapers, 28 scanners)</li>
            <li className="flex items-start gap-2"><span className="text-gray-600 mt-1">·</span>Identity graph + clustering + similarity</li>
            <li className="flex items-start gap-2"><span className="text-gray-600 mt-1">·</span>Operator dashboard + reporting</li>
            <li className="flex items-start gap-2"><span className="text-gray-600 mt-1">·</span>Play 1 / Play 2 / Play 3 delivery</li>
          </ul>
        </div>

        <div className="p-6 bg-[#13131c] border border-[#00ff88]/30 rounded-lg">
          <div className="text-xs font-mono text-[#00ff88]/70 uppercase tracking-wider mb-2">Protocol</div>
          <h3 className="text-lg font-bold text-white mb-4 font-['Instrument_Sans',sans-serif]">
            BFP local binary
          </h3>
          <p className="text-sm text-gray-400 leading-relaxed mb-4">
            Cryptographic core. Runs on operator hardware. Same independence model as CT logs and MISP instances.
          </p>
          <ul className="space-y-2 text-sm text-gray-300">
            <li className="flex items-start gap-2"><span className="text-[#00ff88]/40 mt-1">·</span>Canonical behavioral hash (locality-sensitive)</li>
            <li className="flex items-start gap-2"><span className="text-[#00ff88]/40 mt-1">·</span>Subject + operator signatures (post-quantum)</li>
            <li className="flex items-start gap-2"><span className="text-[#00ff88]/40 mt-1">·</span>Append-only claim log (Merkle-anchored)</li>
            <li className="flex items-start gap-2"><span className="text-[#00ff88]/40 mt-1">·</span>Subject binding ceremony</li>
          </ul>
        </div>
      </div>

      {/* S242 — Parallels row drives the Trust/Threat block via hover/focus.
          Resting state = BFP; mouse-leave snaps back to BFP. */}
      <div onMouseLeave={() => setActive(PARALLELS.length - 1)}>
        <div className="text-xs font-mono text-gray-500 uppercase tracking-wider mb-4 text-center">Infrastructure parallels</div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          {PARALLELS.map((p, i) => (
            <button
              key={p.name}
              type="button"
              onMouseEnter={() => setActive(i)}
              onFocus={() => setActive(i)}
              onClick={() => setActive(i)}
              className={`p-4 bg-[#13131c] border rounded-lg text-center transition-all duration-200 hover:-translate-y-0.5 ${
                i === active
                  ? (p.accent ? 'border-[#00ff88]/70' : 'border-gray-500')
                  : (p.accent ? 'border-[#00ff88]/40' : 'border-[#1e1e2e]')
              }`}
            >
              <div className={`text-sm font-bold mb-1 font-['Instrument_Sans',sans-serif] ${
                p.accent ? 'text-[#00ff88]' : 'text-white'
              }`}>
                {p.name}
              </div>
              <div className="text-xs text-gray-500">{p.what}</div>
            </button>
          ))}
        </div>

        <AnimatePresence mode="wait">
          <motion.div
            key={active}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.18 }}
            className="grid md:grid-cols-2 gap-6"
          >
            <div className="p-6 bg-[#13131c] border border-[#1e1e2e] rounded-lg">
              <div className="text-xs font-mono text-gray-500 uppercase tracking-wider mb-2">Trust model</div>
              <h3 className="text-base font-bold text-white mb-4 font-['Instrument_Sans',sans-serif]">{ap.trustTitle}</h3>
              <ul className="space-y-2 text-sm text-gray-400">
                {ap.trust.map((p, i) => (
                  <li key={i} className="flex items-start gap-2"><span className="text-gray-600 mt-1 shrink-0">·</span><span>{p}</span></li>
                ))}
              </ul>
            </div>
            <div className="p-6 bg-[#13131c] border border-[#1e1e2e] rounded-lg">
              <div className="text-xs font-mono text-gray-500 uppercase tracking-wider mb-2">Threat model</div>
              <h3 className="text-base font-bold text-white mb-4 font-['Instrument_Sans',sans-serif]">{ap.threatTitle}</h3>
              <ul className="space-y-2 text-sm text-gray-400">
                {ap.threat.map((p, i) => (
                  <li key={i} className="flex items-start gap-2"><span className="text-gray-600 mt-1 shrink-0">·</span><span>{p}</span></li>
                ))}
              </ul>
            </div>
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  )
}
