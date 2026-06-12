const BUCKETS = [
  {
    key: 'shipped',
    label: 'Shipped',
    accent: '#00ff88',
    items: [
      { id: 'S147', title: 'network_signature — 11-axis fingerprint complete', date: 'May 2026' },
      { id: 'S166', title: 'Canonical behavioral hash — K=3 locality-sensitive clustering', date: 'May 2026' },
      { id: 'S167–S169', title: 'Append-only claim log + cross-verification + Merkle tamper-evidence', date: 'May 2026' },
      { id: 'S170', title: 'BFP_SPEC v0.2.0 committed', date: 'May 2026' },
      { id: 'S177', title: 'Spec Session 2 complete — trust layer + axis flags + §13 PQC stack', date: 'May 2026' },
      { id: 'S232', title: 'Subject attestation — consent-verified SSO', date: 'Jun 2026' },
      { id: 'S265–S267', title: 'Entropy engine — per-axis identifying-bits ledger + Entropy tab', date: 'Jun 2026' },
      { id: 'S271–S272', title: 'H(cluster) belonging term + breach-composition signal (extract-and-drop)', date: 'Jun 2026' },
    ],
  },
  {
    key: 'active',
    label: 'Active',
    accent: '#ffaa00',
    items: [
      { id: 'SPEC', title: 'BFP_SPEC — Session 3' },
      { id: 'VALIDATION', title: 'Validation framework (ground-truth corpus + cross-source convergence metrics)' },
      { id: 'PAGE', title: 'BFP public page — iterative buildout (this artifact)' },
    ],
  },
  {
    key: 'next',
    label: 'Next',
    accent: '#aa66ff',
    items: [
      { id: 'THRESHOLD', title: 'Similarity threshold tuning (same-person vs cluster split)' },
      { id: 'P1', title: 'Axis: public_exposure plumbing' },
      { id: 'CANDIDATE', title: 'Axis: temporal_persistence (candidate)' },
      { id: 'SUBJECT', title: 'Subject layer in xposeTIP (read / guidance UI)' },
    ],
  },
  {
    key: 'deferred',
    label: 'Long-term',
    accent: '#6688aa',
    items: [
      { id: 'FED', title: 'Federation governance model' },
      { id: 'INDEP', title: 'Independent reference implementations (≥2 required for federation)' },
      { id: 'LAUNCH', title: 'Public protocol launch (gated on trust properties measured)' },
      { id: 'STANDARD', title: 'Standards-body engagement (CIRCL, MISP, IETF)' },
    ],
  },
]

export default function BFPRoadmap() {
  return (
    <div className="max-w-5xl mx-auto px-6">
      <div className="text-center mb-16">
        <div className="text-xs font-mono text-[#00ff88]/70 uppercase tracking-wider mb-3">Roadmap</div>
        <h2 className="text-3xl md:text-4xl font-bold mb-4 font-['Instrument_Sans',sans-serif]">
          Where we are. Where we go.
        </h2>
        <p className="text-sm text-gray-500 max-w-2xl mx-auto">
          The reference implementation lives. The protocol matures in silence. Federation when trust properties are measured.
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {BUCKETS.map((bucket) => (
          <div
            key={bucket.key}
            className="p-6 bg-[#13131c] border border-[#1e1e2e] rounded-lg"
          >
            <div className="flex items-center gap-2 mb-5">
              <span
                className="w-2 h-2 rounded-full"
                style={{ background: bucket.accent }}
              />
              <h3 className="text-sm font-mono uppercase tracking-wider" style={{ color: bucket.accent }}>
                {bucket.label}
              </h3>
              <span className="text-xs text-gray-600 font-mono ml-auto">{bucket.items.length}</span>
            </div>
            <ul className="space-y-3">
              {bucket.items.map((item) => (
                <li key={item.id} className="flex items-start gap-3 text-sm">
                  <span className="text-xs font-mono text-gray-600 shrink-0 mt-0.5 min-w-[60px]">
                    {item.id}
                  </span>
                  <div className="flex-1">
                    <div className="text-gray-300">{item.title}</div>
                    {item.date && (
                      <div className="text-xs text-gray-600 font-mono mt-0.5">{item.date}</div>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  )
}
