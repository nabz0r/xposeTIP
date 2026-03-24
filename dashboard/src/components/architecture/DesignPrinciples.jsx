import Section from '../shared/Section'

export default function DesignPrinciples() {
  return (
    <Section className="py-20">
      <div className="max-w-3xl mx-auto px-6">
        <h2 className="text-2xl font-bold mb-8 text-center font-['Instrument_Sans',sans-serif]">Design Principles</h2>
        <div className="space-y-6">
          {[
            {
              num: '01', title: 'Two-Pass Intelligence', color: '#00ff88',
              desc: 'Pass 1 gathers data by email/username. Pass 2 enriches by resolved name. This separation ensures name-based searches only run with high-confidence names.',
            },
            {
              num: '02', title: 'Operator Ground Truth', color: '#3388ff',
              desc: 'Operators can assert country and name — overriding automated resolution. Assertions have confidence=1.0 and survive re-scans.',
            },
            {
              num: '03', title: 'Layer Isolation', color: '#ffcc00',
              desc: 'Each scraper runs independently. API failures don\'t cascade. Partial results are always stored and displayed.',
            },
            {
              num: '04', title: 'Confidence-First', color: '#ff8800',
              desc: 'Every data point carries a confidence score. Name-based matches are always "potential" — never auto-confirmed. Users see confidence badges and mandatory disclaimers.',
            },
            {
              num: '05', title: 'Privacy by Design', color: '#ff2244',
              desc: 'All API keys AES-256 encrypted at rest. Every DB query scoped to workspace. No data shared between workspaces.',
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
