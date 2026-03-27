import Section from '../shared/Section'

export default function ScraperBreakdown() {
  return (
    <Section className="py-20 bg-[#12121a]/50">
      <div className="max-w-3xl mx-auto px-6">
        <h2 className="text-2xl font-bold mb-8 text-center font-['Instrument_Sans',sans-serif]">120 Intelligence Sources</h2>
        <div className="bg-[#0a0a0f] border border-[#1e1e2e] rounded-xl overflow-hidden">
          {[
            { cat: 'Social', count: 35, color: '#3388ff', examples: 'Twitter, Instagram, Reddit, TikTok, Bluesky, Mastodon...' },
            { cat: 'Dev', count: 12, color: '#cc88ff', examples: 'GitHub, GitLab, npm, PyPI, Keybase, Codeberg...' },
            { cat: 'Breach', count: 9, color: '#ff2244', examples: 'HIBP, LeakCheck, IntelX, DeHashed, Pastebin...' },
            { cat: 'Metadata', count: 12, color: '#aa55ff', examples: 'DNS, WHOIS, email validation, Gravatar...' },
            { cat: 'Gaming', count: 8, color: '#ff8800', examples: 'Steam, Chess.com, Roblox, RuneScape...' },
            { cat: 'People Search', count: 7, color: '#00ddcc', examples: 'WebMii, Google Scholar, NPM, PyPI...' },
            { cat: 'Archive', count: 10, color: '#ffcc00', examples: 'Wayback Machine, cached profiles...' },
            { cat: 'Public Exposure', count: 7, color: '#ff5588', examples: 'GDELT, GNews, RSS, OpenSanctions, Interpol, OpenCorporates, LBR' },
            { cat: 'LinkedIn', count: 6, color: '#0077b5', examples: 'Profile discovery, employment history...' },
            { cat: 'Code Leak', count: 3, color: '#ff00ff', examples: 'GitHub Code Search, GitHub Gists, Pastebin dumps' },
            { cat: 'Other', count: 8, color: '#666688', examples: 'Misc scrapers, enrichers...' },
          ].map(c => (
            <div key={c.cat} className="flex items-center gap-4 px-5 py-3 border-b border-[#1e1e2e] last:border-0">
              <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: c.color }} />
              <span className="text-sm font-semibold w-28 shrink-0" style={{ color: c.color }}>{c.cat}</span>
              <span className="text-sm font-mono font-bold w-8 text-center">{c.count}</span>
              <span className="text-xs text-gray-500 truncate">{c.examples}</span>
            </div>
          ))}
          <div className="flex items-center gap-4 px-5 py-3 bg-[#1e1e2e]/30">
            <span className="w-2 h-2 rounded-full shrink-0 bg-white" />
            <span className="text-sm font-bold w-28 shrink-0">Total</span>
            <span className="text-sm font-mono font-bold w-8 text-center text-[#00ff88]">120</span>
            <span className="text-xs text-gray-400">Across 11 categories</span>
          </div>
        </div>
      </div>
    </Section>
  )
}
