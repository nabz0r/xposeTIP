import Section from '../shared/Section'

export default function ScraperBreakdown() {
  return (
    <Section className="py-20 bg-[#12121a]/50">
      <div className="max-w-3xl mx-auto px-6">
        <h2 className="text-2xl font-bold mb-8 text-center font-['Instrument_Sans',sans-serif]">174 Intelligence Sources</h2>
        <div className="bg-[#0a0a0f] border border-[#1e1e2e] rounded-xl overflow-hidden">
          {[
            // S206-2 palette unify: 4 semantic colors mapped to BFPLayer S205 standards.
            //   #00ff88 — primary identity signals (social/professional/people-search/identity-validators)
            //   #3388ff — data flow / metadata / archival
            //   #ff5588 — risk / exposure / leaks
            //   #888    — context categories that don't fit cleanly (gaming presence, financial activity)
            { cat: 'Social',          count: 74, color: '#00ff88', examples: 'Reddit, Steam, Telegram, Twitch, Pinterest, Strava, Snapchat, Threads, Bluesky, Last.fm, Issuu, Calendly, Blogger, PayPal, Gumroad, Speakerdeck, Wattpad, HackMD, OpenCollective, Steemit, DeviantArt, Scratch, Couchsurfing, Patreon...' },
            { cat: 'Metadata',        count: 19, color: '#3388ff', examples: 'DNS DMARC, WHOIS, Gravatar (x3), crt.sh, mailcheck, github_timezone, phone dorks (Google/DDG/Bing/Yandex), HackerNews Algolia...' },
            { cat: 'People Search',   count: 11, color: '#00ff88', examples: 'WebMii, Google Scholar, Google Groups, npm, PyPI, Snapchat, Crunchbase...' },
            { cat: 'Gaming',          count: 10, color: '#888',    examples: 'Steam, Chess.com, Roblox, Lichess, Xbox, RuneScape, MyAnimeList, Anilist...' },
            { cat: 'Public Exposure', count: 15, color: '#ff5588', examples: 'GDELT, GNews, RSS, OpenSanctions, Interpol, OpenCorporates, LBR, Courtlistener, BODACC, UK Gazette, arXiv, ORCID, DBLP, Semantic Scholar, AlienVault OTX' },
            { cat: 'Breach',          count: 9,  color: '#ff5588', examples: 'LeakCheck, IntelX, EmailRep, HackerTarget, XposedOrNot, LeakLookup...' },
            { cat: 'Archive',         count: 9,  color: '#3388ff', examples: 'Wayback Machine — domain, count, profile, LinkedIn, Twitter, Instagram, Facebook, GitHub' },
            { cat: 'Identity',        count: 8,  color: '#00ff88', examples: 'Agify, Genderize, Nationalize, NumVerify, Veriphone, API Ninjas, AbstractAPI' },
            { cat: 'Code Leak',       count: 3,  color: '#ff5588', examples: 'GitHub Code Search (email), GitHub Code Search (username), GitHub Gists' },
            { cat: 'Financial',       count: 14, color: '#888',    examples: 'Blockchain.info, Blockchair, ChainAbuse, Etherscan, BscScan, Polygonscan, Snowtrace, Arbiscan, Optimistic, Basescan, Tronscan, SolanaFM, Mempool BTC/LTC/DOGE' },
            { cat: 'Social Account',  count: 2,  color: '#00ff88', examples: 'LinkedIn Profile, Proxycurl LinkedIn' },
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
            <span className="text-sm font-mono font-bold w-8 text-center text-[#00ff88]">174</span>
            <span className="text-xs text-gray-400">Across 11 categories</span>
          </div>
          <div className="flex items-center gap-4 px-5 py-2 bg-[#1e1e2e]/10 border-t border-[#1e1e2e]">
            <span className="w-2 h-2 rounded-full shrink-0 bg-[#00ff88]" />
            <span className="text-xs font-mono w-28 shrink-0 text-gray-400">Active / Disabled</span>
            <span className="text-xs font-mono w-16 text-center"><span className="text-[#00ff88]">149</span><span className="text-gray-600"> / </span><span className="text-gray-500">25</span></span>
            <span className="text-[10px] text-gray-600">85% activation rate · disabled = pending API key or pending validation</span>
          </div>
        </div>
      </div>
    </Section>
  )
}
