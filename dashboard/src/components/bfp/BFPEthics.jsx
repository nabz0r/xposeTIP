const PRINCIPLES = [
  {
    title: 'Asymmetry is the harm',
    body: 'The harm is not that information exists about you. The harm is that everyone else sees it, and you do not. BFP corrects the asymmetry, not the information.',
  },
  {
    title: 'Empowerment over paternalism',
    body: 'Refusing to index does not protect a subject whose data is already in a hundred broker databases. It only ensures the subject remains the last person to know what the world knows. We choose empowerment.',
  },
  {
    title: 'Auditable by design',
    body: 'BFP scoring methodology is fully public. The reference implementation is open-source. The protocol specification is open. No part of the trust model depends on what we choose not to reveal.',
  },
]

export default function BFPEthics() {
  return (
    <div className="max-w-5xl mx-auto px-6">
      <div className="text-center mb-12">
        <div className="text-xs font-mono text-[#00ff88]/70 uppercase tracking-wider mb-3">Ethics</div>
        <h2 className="text-3xl md:text-4xl font-bold mb-4 font-['Instrument_Sans',sans-serif]">
          Transparency-empowerment, not paternalist non-indexation
        </h2>
      </div>

      {/* Thesis statement */}
      <div className="max-w-3xl mx-auto mb-12 p-6 bg-[#0a0a0f] border-l-2 border-[#00ff88] rounded-r-lg">
        <p className="text-base text-gray-300 leading-relaxed italic">
          The internet has already indexed every adult with a digital footprint. The data brokers know.
          The platforms know. The state knows. Refusing to give the subject the same view does not undo any of that —
          it only preserves the asymmetry. BFP returns the view to the person it concerns.
        </p>
        <div className="mt-4 text-xs font-mono text-gray-500 not-italic">
          Lineage: cypherpunk principles · David Brin, <span className="text-gray-400">The Transparent Society</span> · the Right to Read
        </div>
      </div>

      {/* Three principles */}
      <div className="grid md:grid-cols-3 gap-4 mb-12">
        {PRINCIPLES.map((p) => (
          <div
            key={p.title}
            className="p-5 bg-[#13131c] border border-[#1e1e2e] rounded-lg"
          >
            <h3 className="text-sm font-bold text-white mb-3 font-['Instrument_Sans',sans-serif]">
              {p.title}
            </h3>
            <p className="text-xs text-gray-400 leading-relaxed">{p.body}</p>
          </div>
        ))}
      </div>

      {/* Two structural commitments */}
      <div className="grid md:grid-cols-2 gap-4">
        <div className="p-5 bg-[#13131c] border border-[#1e1e2e] rounded-lg">
          <div className="text-xs font-mono text-gray-500 uppercase tracking-wider mb-2">Structural commitment</div>
          <h3 className="text-base font-bold text-white mb-3 font-['Instrument_Sans',sans-serif]">
            Takedown protocol
          </h3>
          <p className="text-sm text-gray-400 leading-relaxed">
            Removal of a subject from the corpus is available on presentation of a legally recognized basis —
            never as a philosophical carve-out by category. This preserves transparency-empowerment as the rule
            while honoring the legal regimes that exist for protected categories.
          </p>
        </div>

        <div className="p-5 bg-[#13131c] border border-[#1e1e2e] rounded-lg">
          <div className="text-xs font-mono text-gray-500 uppercase tracking-wider mb-2">Structural commitment</div>
          <h3 className="text-base font-bold text-white mb-3 font-['Instrument_Sans',sans-serif]">
            Auditable methodology
          </h3>
          <p className="text-sm text-gray-400 leading-relaxed">
            The scoring algorithm is published. The reference implementation is open-source.
            Play 3 monetization (paid remediation) cannot rely on inflated findings — the methodology is checkable
            by anyone, including subjects who paid for remediation.
          </p>
        </div>
      </div>
    </div>
  )
}
