import Section from '../shared/Section'

export default function RoadmapSection() {
  return (
    <Section className="py-20" id="roadmap">
      <div className="max-w-3xl mx-auto px-6">
        <h2 className="text-2xl font-bold mb-8 text-center font-['Instrument_Sans',sans-serif]">Roadmap</h2>
        <div className="space-y-8">
          {[
            {
              version: 'v1.0', date: 'Nexus 2026 (June)', color: '#00ff88',
              items: [
                { done: true, text: '117 sources across 10 categories (social, breach, dev, archive, gaming, people, metadata, LinkedIn, news, compliance)' },
                { done: true, text: 'Personalized PageRank / Markov chain confidence engine' },
                { done: true, text: '32x32 pixel art identity avatars (~5.4B unique combinations)' },
                { done: true, text: '9-axis digital fingerprint radar (+ public exposure)' },
                { done: true, text: 'Digital personas with display names, aliases, platform badges' },
                { done: true, text: 'Profile photos tab (cross-platform collection)' },
                { done: true, text: 'Geographic exposure map (self-reported + server locations)' },
                { done: true, text: 'Workspace-wide geo map on Dashboard' },
                { done: true, text: 'Name resolution: family consensus + source method penalty' },
                { done: true, text: 'Life timeline with breach/account/archive events' },
                { done: true, text: 'Freemium quick scan with upsell' },
                { done: true, text: 'Plans (Free/Consultant \u20ac49/Enterprise \u20ac199)' },
                { done: true, text: 'Two-pass scan: name-based enrichment after identity resolution' },
                { done: true, text: 'Public exposure intelligence: news, sanctions, corporate roles' },
                { done: true, text: 'Operator identity assertions (name + country ground truth)' },
                { done: true, text: 'Scraper health monitoring dashboard' },
                { done: true, text: 'Language-aware multi-lang news search' },
                { done: true, text: 'Corporate email pattern detection' },
                { done: false, text: 'PDF report export' },
                { done: false, text: 'Admin scoring tuning sliders' },
              ],
            },
            {
              version: 'v1.1', date: 'Post-Nexus (Jul-Aug)', color: '#3388ff',
              items: [
                { done: false, text: 'Corporate scrapers (O365, Azure AD, GitHub org)' },
                { done: false, text: 'Domain-wide scan (all employees of company)' },
                { done: false, text: 'Batch scan scheduling' },
                { done: false, text: 'Public API for integrations + webhook notifications' },
                { done: false, text: 'Custom scraper plugins' },
                { done: false, text: 'Multi-language UI (FR, DE, LU)' },
              ],
            },
            {
              version: 'v1.2', date: 'Enterprise (Q4 2026)', color: '#ff8800',
              items: [
                { done: false, text: 'OAuth audit (Google/Microsoft)' },
                { done: false, text: 'Scheduled recurring scans' },
                { done: false, text: 'Compliance reports (NIS2, DORA)' },
                { done: false, text: 'Multi-language (FR, DE, LU)' },
              ],
            },
            {
              version: 'v2.0', date: 'Platform (2027)', color: '#ff2244',
              items: [
                { done: false, text: 'Community scraper marketplace' },
                { done: false, text: 'Plugin API for custom integrations' },
                { done: false, text: 'Mobile app (iOS/Android)' },
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
