import Section from '../shared/Section'

export default function DesignPrinciples() {
  return (
    <Section className="py-20">
      <div className="max-w-3xl mx-auto px-6">
        <h2 className="text-2xl font-bold mb-8 text-center font-['Instrument_Sans',sans-serif]">Design Principles</h2>
        <div className="space-y-6">
          {[
            {
              num: '01', title: 'Identity-First', color: '#00ff88',
              desc: 'The unit of intelligence is the person, not the indicator. An IP changes. A blocklist goes stale. A behavioral fingerprint persists. xposeTIP builds identities, not IOC lists.',
            },
            {
              num: '02', title: 'Confidence-Scored', color: '#3388ff',
              desc: 'Every data point carries a confidence score derived from PageRank propagation. Nothing is assumed. Name-based matches are always "potential" — never auto-confirmed. Users see confidence badges and mandatory disclaimers.',
            },
            {
              num: '03', title: 'Operator-Augmented', color: '#ffcc00',
              desc: 'Machine intelligence builds the graph. Human knowledge refines it. Operators can assert country and name — overriding automated resolution with confidence=1.0. Assertions survive re-scans.',
            },
            {
              num: '04', title: 'Layer-Isolated', color: '#ff8800',
              desc: 'Each source runs independently. API failures don\'t cascade. Partial results are always stored and displayed. Three enrichment layers (media, compliance, corporate) fail independently — one broken API never blocks the pipeline.',
            },
            {
              num: '05', title: 'Privacy by Design', color: '#ff2244',
              desc: 'All API keys AES-256 encrypted at rest. Every DB query scoped to workspace. No data shared between workspaces. GDPR-aware architecture — we reveal existing public exposure, we don\'t create new exposure.',
            },
            {
              num: '06', title: 'Green Intelligence', color: '#00ddcc',
              desc: 'Maximum insight per watt. 127 scrapers, PageRank, Markov chains — on a single machine. No GPU clusters, no cloud bloat. Data-driven scrapers (JSON config, not code per source). Pixel art avatars: 5.4B combos, zero GPU. Every decision asks: is this the lightest way?',
            },
          ].map(p => (
            <div key={p.num} className="flex gap-4">
              <span className="text-2xl font-mono font-bold shrink-0" style={{ color: p.color + '33' }}>{p.num}</span>
              <div>
                <h3 className="text-sm font-semibold mb-1" style={{ color: p.color }}>{p.title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{p.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </Section>
  )
}
