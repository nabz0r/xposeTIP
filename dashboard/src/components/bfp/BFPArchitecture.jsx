const PARALLELS = [
  { name: 'DNS', what: 'Resolves domains' },
  { name: 'Certificate Transparency', what: 'Verifies TLS certificates' },
  { name: 'MISP', what: 'Shares malware indicators' },
  { name: 'BFP', what: 'Resolves identities', accent: true },
]

const TRUST_PROPERTIES = [
  'Evidence-based consensus (≥ N independent scrapers converge)',
  'Append-only log of claims (Certificate Transparency-style)',
  'No proof-of-work — energy-light by design',
  'Audit trail traceable to each source',
]

const THREAT_PROPERTIES = [
  'Conservative-by-design — absorbs unknown future threats',
  'Threat model emerges from supply-chain position',
  'Post-quantum cryptography from day one (NIST 2024)',
  'Multi-source convergence resists single-source poisoning',
]

export default function BFPArchitecture() {
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
            <li className="flex items-start gap-2"><span className="text-gray-600 mt-1">·</span>Data collection (174 scrapers, 27 scanners)</li>
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

      {/* Parallels row */}
      <div className="mb-12">
        <div className="text-xs font-mono text-gray-500 uppercase tracking-wider mb-4 text-center">Infrastructure parallels</div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {PARALLELS.map((p) => (
            <div
              key={p.name}
              className={`p-4 bg-[#13131c] border rounded-lg text-center transition-colors ${
                p.accent ? 'border-[#00ff88]/40' : 'border-[#1e1e2e]'
              }`}
            >
              <div className={`text-sm font-bold mb-1 font-['Instrument_Sans',sans-serif] ${
                p.accent ? 'text-[#00ff88]' : 'text-white'
              }`}>
                {p.name}
              </div>
              <div className="text-xs text-gray-500">{p.what}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Trust + Threat models */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="p-6 bg-[#13131c] border border-[#1e1e2e] rounded-lg">
          <div className="text-xs font-mono text-gray-500 uppercase tracking-wider mb-2">Trust model</div>
          <h3 className="text-base font-bold text-white mb-4 font-['Instrument_Sans',sans-serif]">
            Certificate Transparency-like
          </h3>
          <ul className="space-y-2 text-sm text-gray-400">
            {TRUST_PROPERTIES.map((p, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-gray-600 mt-1 shrink-0">·</span>
                <span>{p}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="p-6 bg-[#13131c] border border-[#1e1e2e] rounded-lg">
          <div className="text-xs font-mono text-gray-500 uppercase tracking-wider mb-2">Threat model</div>
          <h3 className="text-base font-bold text-white mb-4 font-['Instrument_Sans',sans-serif]">
            Conservative-by-design
          </h3>
          <ul className="space-y-2 text-sm text-gray-400">
            {THREAT_PROPERTIES.map((p, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-gray-600 mt-1 shrink-0">·</span>
                <span>{p}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}
