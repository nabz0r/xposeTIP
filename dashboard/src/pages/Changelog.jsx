import { useState, useMemo } from 'react'
import { Search } from 'lucide-react'
import commitsRaw from '../data/changelog.json'

const COMMITS = commitsRaw

const TYPE_COLORS = {
  feat: '#00ff88',
  fix: '#ff8800',
  chore: '#aa55ff',
  docs: '#3388ff',
  refactor: '#cc88ff',
  test: '#ffcc00',
  style: '#888888',
  perf: '#ff5588',
  build: '#888888',
  ci: '#888888',
  other: '#666688',
}

const TYPE_FILTERS = ['all', 'feat', 'fix', 'docs', 'chore', 'other']

const MONTH_LABELS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

function monthKey(isoDate) {
  const d = new Date(isoDate)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

function monthLabel(key) {
  const [year, month] = key.split('-')
  return `${MONTH_LABELS[parseInt(month, 10) - 1]} ${year}`
}

function dayLabel(isoDate) {
  const d = new Date(isoDate)
  return `${String(d.getDate()).padStart(2, '0')} ${MONTH_LABELS[d.getMonth()]}`
}

export default function Changelog() {
  const [typeFilter, setTypeFilter] = useState('all')
  const [search, setSearch] = useState('')

  const typeCounts = useMemo(() => {
    const counts = { all: COMMITS.length }
    for (const t of TYPE_FILTERS) {
      if (t === 'all') continue
      if (t === 'other') {
        counts.other = COMMITS.filter((c) => !['feat', 'fix', 'docs', 'chore'].includes(c.type)).length
      } else {
        counts[t] = COMMITS.filter((c) => c.type === t).length
      }
    }
    return counts
  }, [])

  const filtered = useMemo(() => {
    let list = COMMITS
    if (typeFilter !== 'all') {
      if (typeFilter === 'other') {
        list = list.filter((c) => !['feat', 'fix', 'docs', 'chore'].includes(c.type))
      } else {
        list = list.filter((c) => c.type === typeFilter)
      }
    }
    if (search.trim()) {
      const q = search.trim().toLowerCase()
      list = list.filter(
        (c) =>
          c.subject.toLowerCase().includes(q) ||
          (c.sprint && c.sprint.toLowerCase().includes(q)) ||
          c.sha.toLowerCase().includes(q),
      )
    }
    return list
  }, [typeFilter, search])

  const grouped = useMemo(() => {
    const map = new Map()
    for (const c of filtered) {
      const k = monthKey(c.date)
      if (!map.has(k)) map.set(k, [])
      map.get(k).push(c)
    }
    return Array.from(map.entries())
  }, [filtered])

  const dateRange = useMemo(() => {
    if (COMMITS.length === 0) return null
    return {
      first: dayLabel(COMMITS[COMMITS.length - 1].date),
      last: dayLabel(COMMITS[0].date),
      firstYear: new Date(COMMITS[COMMITS.length - 1].date).getFullYear(),
    }
  }, [])

  return (
    <div className="pb-20">
      <div className="max-w-3xl mx-auto px-6 pb-16">
        {/* Hero */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 text-xs font-mono text-[#00ff88]/70 mb-4">
            <span className="w-1.5 h-1.5 bg-[#00ff88] rounded-full animate-pulse" />
            Public log · Every commit
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-4 font-['Instrument_Sans',sans-serif]">
            Changelog
          </h1>
          <p className="text-gray-400 max-w-lg mx-auto">
            <span className="text-white font-semibold">{COMMITS.length}</span> commits since{' '}
            {dateRange ? `${dateRange.first} ${dateRange.firstYear}` : 'project start'}.
            Sourced directly from{' '}
            <a
              href="https://github.com/nabz0r/xposeTIP/commits/main"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#00ff88] hover:underline"
            >
              git
            </a>
            {' '}— this is the truth.
          </p>
        </div>

        {/* Search */}
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-600" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Filter by sprint (S140), keyword, or sha…"
            className="w-full pl-10 pr-4 py-2.5 bg-[#12121a] border border-[#1e1e2e] rounded-lg text-sm text-white placeholder:text-gray-600 font-mono focus:outline-none focus:border-[#2e2e3e] transition-colors"
          />
        </div>

        {/* Type filter chips */}
        <div className="flex flex-wrap gap-2 mb-10">
          {TYPE_FILTERS.map((t) => (
            <button
              key={t}
              onClick={() => setTypeFilter(t)}
              className={`text-xs font-mono px-3 py-1.5 rounded-full transition-colors ${
                typeFilter === t
                  ? 'bg-[#00ff88] text-black font-semibold'
                  : 'bg-[#12121a] border border-[#1e1e2e] text-gray-400 hover:text-white'
              }`}
            >
              {t}
              <span className={`ml-1.5 ${typeFilter === t ? 'text-black/60' : 'text-gray-600'}`}>
                {typeCounts[t]}
              </span>
            </button>
          ))}
        </div>

        {/* Results count */}
        <p className="text-xs text-gray-600 font-mono mb-6">
          {filtered.length} {filtered.length === 1 ? 'commit' : 'commits'} shown
        </p>

        {/* Grouped timeline */}
        {grouped.length > 0 ? (
          <div className="space-y-10">
            {grouped.map(([month, commits]) => (
              <div key={month}>
                <h2 className="text-xs font-mono text-gray-500 mb-4 pb-2 border-b border-[#1e1e2e]">
                  {monthLabel(month)} · <span className="text-gray-700">{commits.length} commits</span>
                </h2>
                <div className="space-y-2">
                  {commits.map((c) => {
                    const color = TYPE_COLORS[c.type] || TYPE_COLORS.other
                    return (
                      <div
                        key={c.sha}
                        className="flex items-start gap-3 bg-[#12121a]/60 border border-[#1e1e2e] rounded-lg px-4 py-3 hover:border-[#2e2e3e] transition-colors"
                      >
                        <span
                          className="shrink-0 text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded"
                          style={{ color, backgroundColor: color + '15' }}
                        >
                          {c.type}
                        </span>
                        {c.sprint && (
                          <span className="shrink-0 text-[10px] font-mono text-gray-500 bg-[#1e1e2e] px-2 py-0.5 rounded">
                            {c.sprint}
                          </span>
                        )}
                        <span className="text-sm text-gray-300 flex-1 leading-relaxed">{c.subject}</span>
                        <a
                          href={`https://github.com/nabz0r/xposeTIP/commit/${c.sha}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="shrink-0 text-[10px] font-mono text-gray-600 hover:text-[#00ff88] transition-colors"
                        >
                          {c.sha}
                        </a>
                      </div>
                    )
                  })}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-center text-gray-600 text-sm py-12">No commits match the current filter.</p>
        )}

        {/* Footer note */}
        <p className="text-center text-[10px] text-gray-700 font-mono mt-16">
          Auto-generated from <code className="text-gray-500">git log</code> at build time ·{' '}
          <a
            href="https://github.com/nabz0r/xposeTIP/commits/main"
            target="_blank"
            rel="noopener noreferrer"
            className="text-gray-500 hover:text-white transition-colors"
          >
            view on GitHub
          </a>
        </p>
      </div>
    </div>
  )
}
