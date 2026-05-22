const PILLARS = [
  {
    title: 'Identity is a layer',
    body: 'Identity is a layer of the internet — and it is the only one without infrastructure. DNS resolves domains. Certificate Transparency verifies certificates. MISP shares threat indicators. There is no equivalent for the people behind those signals. BFP closes that gap.',
  },
  {
    title: 'A protocol, not a product',
    body: 'BFP is to identity what DNS is to domains, what Certificate Transparency is to TLS, what MISP is to malware IOCs. xposeTIP is the reference implementation. The protocol itself is a specification — open, federated, locally-executed.',
  },
  {
    title: 'Subject as first-class participant',
    body: 'Subjects read their own fingerprint, receive remediation guidance, can subscribe to monitoring, can engage managed cleanup services. The default is transparency-empowerment, not paternalist non-indexation. Takedown remains available as a legal safety valve for protected categories.',
  },
  {
    title: 'Post-quantum, local-first, green by design',
    body: 'Cryptography from NIST 2024 PQC suite (SPHINCS+, ML-DSA, ML-KEM). Canonical fingerprint hashes derived from invariants only, forgery-resistant via subject binding ceremony. Trust model is Certificate Transparency-like — evidence-based, no proof-of-work, energy-light. Protocol runs locally on operator hardware.',
  },
]

export default function BFPFoundation() {
  return (
    <div className="max-w-5xl mx-auto px-6">
      <div className="text-center mb-16">
        <div className="text-xs font-mono text-[#00ff88]/70 uppercase tracking-wider mb-3">Foundation</div>
        <h2 className="text-3xl md:text-4xl font-bold mb-4 font-['Instrument_Sans',sans-serif]">
          What BFP is, in four statements
        </h2>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {PILLARS.map((pillar) => (
          <div
            key={pillar.title}
            className="p-6 bg-[#13131c] border border-[#1e1e2e] rounded-lg hover:border-[#00ff88]/30 transition-colors"
          >
            <h3 className="text-lg font-bold text-white mb-3 font-['Instrument_Sans',sans-serif]">
              {pillar.title}
            </h3>
            <p className="text-sm text-gray-400 leading-relaxed">{pillar.body}</p>
          </div>
        ))}
      </div>

      <div className="mt-12 text-center text-sm text-gray-500 italic max-w-2xl mx-auto">
        Lineage: cypherpunk principles, David Brin's Transparent Society, the infrastructure protocols
        that make the modern internet trustworthy at scale.
      </div>
    </div>
  )
}
