import { useMemo, useState } from 'react'
import { Newspaper, ExternalLink, Globe, Calendar, Search, Filter } from 'lucide-react'

const severityColor = {
  critical: '#ff2244',
  high: '#ff4444',
  medium: '#ff8800',
  low: '#ffcc00',
  info: '#00ff88',
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
  const [sortBy, setSortBy] = useState('date') // date, confidence, source

  const exposureFindings = useMemo(() => {
    return findings.filter(f =>
      f.category === 'public_exposure' || f.indicator_type === 'media_mention'
    )
  }, [findings])

  const filtered = useMemo(() => {
    let items = [...exposureFindings]

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
      // Default: date descending
      const da = a.data?.pub_date || a.created_at || ''
      const db = b.data?.pub_date || b.created_at || ''
      return db.localeCompare(da)
    })

    return items
  }, [exposureFindings, search, sortBy])

  // Extract unique sources
  const sources = useMemo(() => {
    const s = new Set()
    exposureFindings.forEach(f => {
      const src = f.data?.source_domain
      if (src) s.add(src)
    })
    return [...s].sort()
  }, [exposureFindings])

  // Stats
  const stats = useMemo(() => {
    const highConf = exposureFindings.filter(f => (f.confidence || 0) >= 0.80).length
    const countries = new Set(exposureFindings.map(f => f.data?.source_country).filter(Boolean))
    const languages = new Set(exposureFindings.map(f => f.data?.language).filter(Boolean))
    return { total: exposureFindings.length, highConf, countries: countries.size, languages: languages.size, sources: sources.length }
  }, [exposureFindings, sources])

  if (!exposureFindings.length) {
    return (
      <div className="text-center py-16 text-gray-500">
        <Newspaper className="w-12 h-12 mx-auto mb-4 opacity-30" />
        <p className="text-lg mb-2">No public exposure detected</p>
        <p className="text-sm">No media mentions or news articles found for this identity.</p>
        {profile?.primary_name && (
          <p className="text-xs text-gray-600 mt-2">Searched for: "{profile.primary_name}"</p>
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

      {/* Search + Sort */}
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
          const sourceDomain = f.data?.source_domain || ''
          const country = f.data?.source_country || ''
          const lang = f.data?.language || ''

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
          <h3 className="text-xs font-semibold text-gray-400 mb-2">Sources ({sources.length})</h3>
          <div className="flex flex-wrap gap-2">
            {sources.map(src => {
              const count = exposureFindings.filter(f => f.data?.source_domain === src).length
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
