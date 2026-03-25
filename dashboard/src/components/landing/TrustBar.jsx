import Section from '../shared/Section'

export default function TrustBar() {
  return (
    <Section className="py-20">
      <div className="max-w-4xl mx-auto px-6">
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 text-center">
          {[
            { value: '117', label: 'OSINT sources' },
            { value: '9-axis', label: 'Behavioral radar' },
            { value: '40+', label: 'Sanctions lists' },
            { value: 'GDPR', label: 'Aware architecture' },
            { value: 'AES-256', label: 'Encrypted at rest' },
            { value: '\ud83c\uddf1\ud83c\uddfa', label: 'Made in Luxembourg' },
          ].map(t => (
            <div key={t.label} className="bg-[#12121a] border border-[#1e1e2e] rounded-lg py-3 px-2">
              <div className="text-sm font-mono font-bold text-[#00ff88]">{t.value}</div>
              <div className="text-[10px] text-gray-500 mt-0.5">{t.label}</div>
            </div>
          ))}
        </div>
        <p className="text-sm text-gray-600 text-center mt-4">
          Open source · On-premise ready · Your data stays yours.
        </p>
      </div>
    </Section>
  )
}
