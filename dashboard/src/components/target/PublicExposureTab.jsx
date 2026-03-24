import { useMemo, useState } from 'react'
import { Newspaper, ExternalLink, Globe, Calendar, Search, Filter, Languages } from 'lucide-react'

const SCRAPER_BADGES = {
  gdelt_news: { label: 'GDELT', color: '#3b82f6', bg: '#3b82f610', border: '#3b82f630' },
  gnews_news: { label: 'GNews', color: '#00ff88', bg: '#00ff8810', border: '#00ff8830' },
  google_news_rss: { label: 'RSS', color: '#888888', bg: '#88888810', border: '#88888830' },
}

function ConfidenceBadge({ value }) {
  const pct = Math.round((value || 0) * 100)
  const color = pct >= 80 ? '#00ff88' : pct >= 60 ? '#ffcc00' : '#ff8800'
  return (
    <span className="text-xs font-mono px-1.5 py-0.5 rounded" style={{ color, background: `${color}15`, border: `1px solid ${color}30` }}>
      {pct}%
    </span>
  )
}

function ScraperBadge({ scraper }) {
  const badge = SCRAPER_BADGES[scraper] || { label: scraper || '?', color: '#666', bg: '#66666610', border: '#66666630' }
  return (
    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded uppercase tracking-wider" style={{ color: badge.color, background: badge.bg, border: `1px solid ${badge.border}` }}>
      {badge.label}
    </span>
  )
}

function formatDate(dateStr) {
  if (!dateStr) return null
  try {
    const d = new Date(dateStr)
    if (isNaN(d.getTime())) return dateStr
    return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
  } catch {
    return dateStr
  }
}

export default function PublicExposureTab({ findings = [], profile }) {
  const [search, setSearch] = useState('')
  const [sortBy, setSortBy] = useState('date')
  const [langFilter, setLangFilter] = useState('all')

  const exposureFindings = useMemo(() => {
    return findings.filter(f =>
      f.category === 'public_exposure' || f.indicator_type === 'media_mention'
    )
  }, [findings])

  // Extract unique languages
  const languages = useMemo(() => {
    const l = new Set()
    exposureFindings.forEach(f => {
      const lang = f.data?.language
      if (lang) l.add(lang)
    })
    return ['all', ...[...l].sort()]
  }, [exposureFindings])

  const filtered = useMemo(() => {
    let items = [...exposureFindings]

    if (langFilter !== 'all') {
      items = items.filter(f => f.data?.language === langFilter)
    }

    if (search) {
      const q = search.toLowerCase()
      items = items.filter(f =>
        (f.title || '').toLowerCase().includes(q) ||
        (f.description || '').toLowerCase().includes(q) ||
        (f.url || '').toLowerCase().includes(q)
      )
    }

    items.sort((a, b) => {
      if (sortBy === 'confidence') return (b.confidence || 0) - (a.confidence || 0)
      if (sortBy === 'source') return (a.data?.source_domain || '').localeCompare(b.data?.source_domain || '')
      const da = a.data?.pub_date || a.created_at || ''
      const db = b.data?.pub_date || b.created_at || ''
      return db.localeCompare(da)
    })

    return items
  }, [exposureFindings, search, sortBy, langFilter])

  // Extract unique sources
  const sources = useMemo(() => {
    const s = new Set()
    exposureFindings.forEach(f => {
      const src = f.data?.source_domain || f.data?.source_name
      if (src) s.add(src)
    })
    return [...s].sort()
  }, [exposureFindings])

  // Scraper distribution
  const scraperCounts = useMemo(() => {
    const counts = {}
    exposureFindings.forEach(f => {
      const s = f.data?.scraper || 'unknown'
      counts[s] = (counts[s] || 0) + 1
    })
    return counts
  }, [exposureFindings])

  // Stats
  const stats = useMemo(() => {
    const highConf = exposureFindings.filter(f => (f.confidence || 0) >= 0.80).length
    const countries = new Set(exposureFindings.map(f => f.data?.source_country).filter(Boolean))
    const uniqueLangs = new Set(exposureFindings.map(f => f.data?.language).filter(Boolean))
    return { total: exposureFindings.length, highConf, countries: countries.size, languages: uniqueLangs.size, sources: sources.length }
  }, [exposureFindings, sources])

  // Empty states
  if (!exposureFindings.length) {
    const hasName = profile?.primary_name
    const nameIsUsername = hasName && (!hasName.includes(' ') || hasName.includes('_'))

    return (
      <div className="text-center py-16 text-gray-500">
        <Newspaper className="w-12 h-12 mx-auto mb-4 opacity-30" />
        {!hasName ? (
          <>
            <p className="text-lg mb-2">Name not resolved</p>
            <p className="text-sm">Public exposure search requires a resolved primary name.</p>
            <p className="text-xs text-gray-600 mt-2">Run a full scan to resolve the identity first.</p>
          </>
        ) : nameIsUsername ? (
          <>
            <p className="text-lg mb-2">Name looks like a username</p>
            <p className="text-sm">"{hasName}" doesn't look like a real name. Public exposure search skipped.</p>
          </>
        ) : (
          <>
            <p className="text-lg mb-2">No media mentions found</p>
            <p className="text-sm">No news articles or media coverage found for "{hasName}".</p>
          </>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Stats bar */}
      <div className="grid grid-cols-5 gap-3">
        {[
          { label: 'Mentions', value: stats.total, color: '#00ff88' },
          { label: 'High Confidence', value: stats.highConf, color: '#ffcc00' },
          { label: 'Sources', value: stats.sources, color: '#00ccff' },
          { label: 'Countries', value: stats.countries, color: '#ff8800' },
          { label: 'Languages', value: stats.languages, color: '#cc88ff' },
        ].map(s => (
          <div key={s.label} className="bg-[#0a0a12] border border-[#1e1e2e] rounded-lg p-3 text-center">
            <div className="text-2xl font-bold font-mono" style={{ color: s.color }}>{s.value}</div>
            <div className="text-xs text-gray-500 mt-1">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Scraper distribution badges */}
      <div className="flex gap-3 items-center text-xs text-gray-500">
        <span>Sources:</span>
        {Object.entries(scraperCounts).map(([scraper, count]) => (
          <span key={scraper} className="flex items-center gap-1">
            <ScraperBadge scraper={scraper} />
            <span className="text-gray-600">{count}</span>
          </span>
        ))}
      </div>

      {/* Search + Sort + Language filter */}
      <div className="flex gap-3 items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            placeholder="Search mentions..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full bg-[#0a0a12] border border-[#1e1e2e] rounded-lg pl-10 pr-4 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-[#00ff88]/50"
          />
        </div>

        {/* Language filter */}
        {languages.length > 2 && (
          <div className="flex items-center gap-1 text-xs">
            <Languages className="w-3 h-3 text-gray-500" />
            {languages.map(l => (
              <button
                key={l}
                onClick={() => setLangFilter(l)}
                className={`px-2 py-1 rounded uppercase ${langFilter === l ? 'bg-[#cc88ff]/10 text-[#cc88ff]' : 'text-gray-500 hover:text-white'}`}
              >
                {l}
              </button>
            ))}
          </div>
        )}

        <div className="flex items-center gap-1 text-xs">
          <Filter className="w-3 h-3 text-gray-500" />
          {['date', 'confidence', 'source'].map(s => (
            <button
              key={s}
              onClick={() => setSortBy(s)}
              className={`px-2 py-1 rounded capitalize ${sortBy === s ? 'bg-[#00ff88]/10 text-[#00ff88]' : 'text-gray-500 hover:text-white'}`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Findings list */}
      <div className="space-y-2">
        {filtered.map(f => {
          const pubDate = formatDate(f.data?.pub_date)
          const sourceDomain = f.data?.source_domain || f.data?.source_name || ''
          const country = f.data?.source_country || ''
          const lang = f.data?.language || ''
          const scraper = f.data?.scraper || ''

          return (
            <div
              key={f.id}
              className="bg-[#0a0a12] border border-[#1e1e2e] rounded-lg p-4 hover:border-[#2a2a3e] transition-colors"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <Newspaper className="w-3.5 h-3.5 text-gray-500 shrink-0" />
                    <h3 className="text-sm font-medium text-white truncate">{f.title}</h3>
                    <ScraperBadge scraper={scraper} />
                  </div>

                  {f.description && f.description !== f.title && (
                    <p className="text-xs text-gray-400 line-clamp-2 mt-1">{f.description}</p>
                  )}

                  <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                    {sourceDomain && (
                      <span className="flex items-center gap-1">
                        <Globe className="w-3 h-3" />
                        {sourceDomain}
                      </span>
                    )}
                    {pubDate && (
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        {pubDate}
                      </span>
                    )}
                    {country && <span>{country}</span>}
                    {lang && <span className="uppercase">{lang}</span>}
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <ConfidenceBadge value={f.confidence} />
                  {f.url && (
                    <a
                      href={f.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-gray-500 hover:text-[#00ff88] transition-colors"
                      onClick={e => e.stopPropagation()}
                    >
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Source summary */}
      {sources.length > 0 && (
        <div className="bg-[#0a0a12] border border-[#1e1e2e] rounded-lg p-4">
          <h3 className="text-xs font-semibold text-gray-400 mb-2">News Sources ({sources.length})</h3>
          <div className="flex flex-wrap gap-2">
            {sources.map(src => {
              const count = exposureFindings.filter(f => (f.data?.source_domain || f.data?.source_name) === src).length
              return (
                <span key={src} className="text-xs bg-[#1e1e2e] px-2 py-1 rounded text-gray-300">
                  {src} <span className="text-gray-500">({count})</span>
                </span>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
