const CRYPTO_STACK = [
  {
    role: 'Canonical behavioral hash',
    algo: 'MinHash over SHA-3-256',
    family: 'Locality-sensitive hashing',
    why: 'Locality-sensitive — small footprint changes produce small hash shifts. Derived from invariants only (never name, email, or usernames). Behavioral clustering primitive — unique identity arises from composition with subject binding signature and future network-layer signals. 256-bit post-quantum security via Grover bound.',
  },
  {
    role: 'Subject attestations',
    algo: 'SPHINCS+ (SLH-DSA)',
    family: 'Hash-based signatures',
    why: 'Hash-based, no algebraic assumptions, audit-trivial. Minimal hardware cost — aligned with Green Ethic. NIST FIPS 205 (August 2024).',
  },
  {
    role: 'Operator + scraper signatures',
    algo: 'ML-DSA (Dilithium)',
    family: 'Lattice-based signatures',
    why: 'Efficient for high-volume signing (each scraper claim signed). NIST FIPS 204 (August 2024).',
  },
  {
    role: 'Key encapsulation / encryption',
    algo: 'ML-KEM (Kyber)',
    family: 'Lattice-based KEM',
    why: 'Confidentiality where needed (subject-operator channels). NIST FIPS 203 (August 2024).',
  },
  {
    role: 'Append-only log integrity',
    algo: 'Merkle tree, SHA-3-256',
    family: 'Hash chains',
    why: 'Same primitive as Certificate Transparency. Verifiable inclusion proofs. Post-quantum safe.',
  },
]

export default function BFPCryptography() {
  return (
    <div className="max-w-5xl mx-auto px-6">
      <div className="text-center mb-16">
        <div className="text-xs font-mono text-[#00ff88]/70 uppercase tracking-wider mb-3">Cryptography</div>
        <h2 className="text-3xl md:text-4xl font-bold mb-4 font-['Instrument_Sans',sans-serif]">
          Post-quantum from day one
        </h2>
        <p className="text-sm text-gray-500 max-w-2xl mx-auto leading-relaxed">
          Identity persistence is measured in decades. Anything signed today with pre-quantum cryptography is potentially broken by the next one.
          BFP commits to the NIST 2024 post-quantum suite throughout — with a deliberate preference for hash-based primitives where the protocol allows, to honor the Green Ethic.
        </p>
      </div>

      <div className="space-y-3">
        {CRYPTO_STACK.map((c) => (
          <div
            key={c.role}
            className="p-5 bg-[#13131c] border border-[#1e1e2e] rounded-lg hover:border-[#00ff88]/20 transition-colors"
          >
            <div className="grid md:grid-cols-[180px_1fr] gap-4 items-start">
              <div>
                <div className="text-xs font-mono text-gray-500 uppercase tracking-wider mb-1">{c.family}</div>
                <div className="text-sm font-bold text-white font-['Instrument_Sans',sans-serif]">
                  {c.role}
                </div>
                <div className="text-sm font-mono text-[#00ff88] mt-1">{c.algo}</div>
              </div>
              <div className="text-sm text-gray-400 leading-relaxed">{c.why}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-10 text-center text-xs text-gray-500 max-w-2xl mx-auto leading-relaxed">
        Implementation libraries available today: <span className="text-gray-400 font-mono">liboqs</span> ·{' '}
        <span className="text-gray-400 font-mono">AWS-LC</span> ·{' '}
        <span className="text-gray-400 font-mono">RustCrypto</span>.
        All choices are NIST-standardized as of August 2024 (FIPS 203, 204, 205).
      </div>
    </div>
  )
}
