import Section from '../shared/Section'

export default function ScraperBreakdown() {
  return (
    <Section className="py-20 bg-[#12121a]/50">
      <div className="max-w-3xl mx-auto px-6">
        <h2 className="text-2xl font-bold mb-8 text-center font-['Instrument_Sans',sans-serif]">120 Intelligence Sources</h2>
        <div className="bg-[#0a0a0f] border border-[#1e1e2e] rounded-xl overflow-hidden">
          {[
            { cat: 'Social', count: 51, color: '#3388ff', examples: 'Reddit, Steam, Telegram, Twitch, Pinterest, Strava, Snapchat, Threads, Bluesky...' },
            { cat: 'Metadata', count: 14, color: '#aa55ff', examples: 'DNS, WHOIS, Gravatar, crt.sh, email validation, mailcheck...' },
            { cat: 'People Search', count: 11, color: '#00ddcc', examples: 'WebMii, Google Scholar, Google Groups, npm, PyPI...' },
            { cat: 'Gaming', count: 10, color: '#ff8800', examples: 'Steam, Chess.com, Roblox, Lichess, Xbox, RuneScape, MyAnimeList...' },
            { cat: 'Breach', count: 9, color: '#ff2244', examples: 'LeakCheck, IntelX, EmailRep, HackerTarget, XposedOrNot...' },
            { cat: 'Archive', count: 9, color: '#ffcc00', examples: 'Wayback Machine, cached profiles, LinkedIn/Twitter archive...' },
            { cat: 'Public Exposure', count: 7, color: '#ff5588', examples: 'GDELT, GNews, RSS, OpenSanctions, Interpol, OpenCorporates, LBR' },
            { cat: 'Identity', count: 3, color: '#cc88ff', examples: 'Agify, Genderize, Nationalize' },
            { cat: 'Code Leak', count: 3, color: '#ff00ff', examples: 'GitHub Code Search, GitHub Gists, GitHub Scraper' },
            { cat: 'Other', count: 3, color: '#666688', examples: 'Misc social account scrapers' },
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
            <span className="text-xs text-gray-400">Across 10 categories</span>
          </div>
        </div>
      </div>
    </Section>
  )
}
