import Section from '../shared/Section'

export default function RoadmapSection() {
  return (
    <Section className="py-20" id="roadmap">
      <div className="max-w-3xl mx-auto px-6">
        <h2 className="text-2xl font-bold mb-4 text-center font-['Instrument_Sans',sans-serif]">Vision</h2>
        <p className="text-center text-gray-500 text-sm mb-12 max-w-lg mx-auto">
          Today, an email gives you a report. Tomorrow, behavioral fingerprints feed firewalls and SIEMs.
          The attacker changes IP — the fingerprint persists.
        </p>
        <div className="space-y-8">
          {[
            {
              version: 'v1', date: 'Now — Investigation & Awareness', color: '#00ff88',
              items: [
                { done: true, text: 'Email → complete identity report with behavioral fingerprint' },
                { done: true, text: '120 OSINT sources across 11 categories' },
                { done: true, text: 'Personalized PageRank confidence propagation' },
                { done: true, text: '9-axis behavioral radar — the identity\'s digital DNA' },
                { done: true, text: 'Digital persona clustering with name resolution' },
                { done: true, text: '32×32 pixel art identity avatars (~5.4B combinations)' },
                { done: true, text: 'Three-pass pipeline: Email → Username expansion → Name enrichment' },
                { done: true, text: 'Public exposure: news, sanctions (40+ lists), corporate records' },
                { done: true, text: 'Operator identity assertions (ground truth override)' },
                { done: true, text: 'Geographic exposure map (self-reported + server locations)' },
                { done: true, text: 'Freemium quick scan with zero-friction onboarding' },
                { done: true, text: 'Plans: Free / Pro €49 / Enterprise €299' },
                { done: true, text: 'PDF identity report export (ReportLab, dark theme, plan-tiered)' },
                { done: true, text: 'Deep username scan — operator-triggered investigation' },
                { done: true, text: 'Code leak monitoring — GitHub Code Search + paste dumps' },
                { done: true, text: 'Behavioral profiling — 5 archetypes from cross-platform metrics' },
                { done: true, text: 'Consumer dashboard preview with score evolution' },
                { done: true, text: 'Remediation engine with prioritized action plans' },
              ],
            },
            {
              version: 'v2', date: '2026 — API & Integration', color: '#3388ff',
              items: [
                { done: false, text: 'Public API — behavioral fingerprints as structured intelligence' },
                { done: false, text: 'SIEM integration — fingerprint feeds for Splunk, Elastic, Sentinel' },
                { done: false, text: 'Webhook notifications on identity changes' },
                { done: false, text: 'Batch scan scheduling and domain-wide employee scans' },
                { done: false, text: 'Custom scraper plugins and community marketplace' },
              ],
            },
            {
              version: 'v3', date: '2027 — Behavioral Matching', color: '#ff8800',
              items: [
                { done: false, text: 'Cross-persona pattern detection — same behavior, different emails' },
                { done: false, text: 'Behavioral similarity scoring between identities' },
                { done: false, text: 'Threat actor clustering from fingerprint patterns' },
                { done: false, text: 'Historical fingerprint evolution tracking' },
              ],
            },
            {
              version: 'v4', date: '2028 — Behavioral Feeds', color: '#ff2244',
              items: [
                { done: false, text: 'Firewalls block behaviors, not IPs' },
                { done: false, text: 'Behavioral fingerprint as a new indicator type in STIX/TAXII' },
                { done: false, text: 'The identity layer the security stack is missing' },
                { done: false, text: 'From IOC feeds to identity feeds — the paradigm shift' },
              ],
            },
          ].map(phase => (
            <div key={phase.version} className="relative pl-8 border-l-2" style={{ borderColor: phase.color + '44' }}>
              <div className="absolute left-[-7px] top-0 w-3 h-3 rounded-full" style={{ backgroundColor: phase.color }} />
              <div className="flex items-baseline gap-3 mb-3">
                <span className="text-lg font-bold font-mono" style={{ color: phase.color }}>{phase.version}</span>
                <span className="text-sm text-gray-500">{phase.date}</span>
              </div>
              <div className="space-y-1.5">
                {phase.items.map((item, i) => (
                  <div key={i} className="flex items-center gap-2 text-sm">
                    {item.done ? (
                      <span className="text-[#00ff88] text-xs">&#10003;</span>
                    ) : (
                      <span className="text-gray-600 text-xs">&#9675;</span>
                    )}
                    <span className={item.done ? 'text-gray-300' : 'text-gray-500'}>{item.text}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </Section>
  )
}
