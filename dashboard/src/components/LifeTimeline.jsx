import { useState } from 'react'
import { ChevronDown, ChevronRight, Shield, UserPlus, Archive, Eye, Activity } from 'lucide-react'

const EVENT_CONFIG = {
  breach:          { color: '#ff2244', bg: 'rgba(255,34,68,0.12)', icon: Shield,   label: 'Breach' },
  account_created: { color: '#00ff88', bg: 'rgba(0,255,136,0.12)', icon: UserPlus, label: 'Account' },
  archive:         { color: '#3388ff', bg: 'rgba(51,136,255,0.12)', icon: Archive,  label: 'Archive' },
  first_seen:      { color: '#ffcc00', bg: 'rgba(255,204,0,0.12)',  icon: Eye,      label: 'First Seen' },
  activity:        { color: '#666688', bg: 'rgba(102,102,136,0.12)', icon: Activity, label: 'Activity' },
}

function groupByYear(events) {
  const groups = {}
  for (const ev of events) {
    const year = new Date(ev.date).getFullYear()
    if (!groups[year]) groups[year] = []
    groups[year].push(ev)
  }
  // Sort years descending
  return Object.entries(groups)
    .sort(([a], [b]) => Number(b) - Number(a))
    .map(([year, items]) => [
      year,
      items.sort((a, b) => new Date(b.date) - new Date(a.date)),
    ])
}

function formatDate(dateStr) {
  try {
    const d = new Date(dateStr)
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  } catch {
    return dateStr?.slice(0, 10) || ''
  }
}

export default function LifeTimeline({ events, compact = false }) {
  const [expandedYear, setExpandedYear] = useState(null)

  if (!events || events.length === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-gray-500 text-sm">
        No timeline events discovered yet.
      </div>
    )
  }

  const grouped = groupByYear(events)

  // Auto-expand first year if none expanded
  const activeYear = expandedYear ?? grouped[0]?.[0]

  return (
    <div className={compact ? '' : 'space-y-1'}>
      {/* Legend */}
      {!compact && (
        <div className="flex flex-wrap gap-3 mb-4 text-xs">
          {Object.entries(EVENT_CONFIG).map(([key, cfg]) => (
            <span key={key} className="flex items-center gap-1.5">
              <span
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: cfg.color }}
              />
              <span className="text-gray-400">{cfg.label}</span>
            </span>
          ))}
        </div>
      )}

      {grouped.map(([year, items]) => {
        const isOpen = activeYear === year
        const breachCount = items.filter(e => e.type === 'breach').length
        const accountCount = items.filter(e => e.type === 'account_created').length

        return (
          <div key={year}>
            {/* Year header */}
            <button
              onClick={() => setExpandedYear(isOpen ? null : year)}
              className="w-full flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-white/5 transition-colors"
            >
              {isOpen
                ? <ChevronDown size={14} className="text-gray-500" />
                : <ChevronRight size={14} className="text-gray-500" />
              }
              <span className="font-mono text-sm font-bold" style={{ color: '#00ff88' }}>
                {year}
              </span>
              <span className="text-xs text-gray-500">
                {items.length} event{items.length !== 1 ? 's' : ''}
              </span>
              {breachCount > 0 && (
                <span className="text-xs px-1.5 py-0.5 rounded" style={{ color: '#ff2244', background: 'rgba(255,34,68,0.15)' }}>
                  {breachCount} breach{breachCount !== 1 ? 'es' : ''}
                </span>
              )}
              {accountCount > 0 && (
                <span className="text-xs px-1.5 py-0.5 rounded" style={{ color: '#00ff88', background: 'rgba(0,255,136,0.15)' }}>
                  {accountCount} account{accountCount !== 1 ? 's' : ''}
                </span>
              )}
            </button>

            {/* Events */}
            {isOpen && (
              <div className="ml-5 border-l border-gray-700/50 pl-4 pb-2 space-y-0.5">
                {items.map((ev, idx) => {
                  const cfg = EVENT_CONFIG[ev.type] || EVENT_CONFIG.activity
                  const Icon = cfg.icon

                  return (
                    <div
                      key={idx}
                      className="flex items-start gap-3 py-1.5 group"
                    >
                      {/* Dot on the line */}
                      <div className="relative -ml-[21px] mt-1.5">
                        <div
                          className="w-2.5 h-2.5 rounded-full border-2"
                          style={{
                            borderColor: cfg.color,
                            backgroundColor: cfg.bg,
                          }}
                        />
                      </div>

                      {/* Date */}
                      <span className="text-xs font-mono text-gray-500 w-16 shrink-0 mt-0.5">
                        {formatDate(ev.date)}
                      </span>

                      {/* Icon + label */}
                      <div
                        className="flex items-center gap-2 px-2 py-1 rounded text-xs"
                        style={{ background: cfg.bg }}
                      >
                        <Icon size={12} style={{ color: cfg.color }} />
                        <span style={{ color: cfg.color }} className="font-medium">
                          {ev.label || cfg.label}
                        </span>
                      </div>

                      {/* Source */}
                      {ev.source && !compact && (
                        <span className="text-[10px] text-gray-600 mt-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          via {ev.source}
                        </span>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )
      })}

      {/* Summary footer */}
      {!compact && (
        <div className="mt-3 pt-3 border-t border-gray-800 flex items-center gap-4 text-xs text-gray-500">
          <span>{events.length} events</span>
          <span>{grouped.length} year{grouped.length !== 1 ? 's' : ''} of digital history</span>
          {events.length > 0 && (
            <span>
              Earliest: {new Date(events[events.length - 1]?.date || events[0]?.date).getFullYear()}
            </span>
          )}
        </div>
      )}
    </div>
  )
}
