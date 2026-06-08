import { useMemo, useState } from 'react'

/**
 * S235 — Activity rhythm clock.
 * Pure viz of profile.timezone (already computed by analyze_timezone).
 * Renders nothing when sample_count < 5 — small-N inference would mislead.
 *
 * Tradecraft: "humans sleep" — an OSINT classic, made visible. Never
 * presented as fact: labelled "Inferred", with explicit sample_count
 * and confidence, and a UTC/Local toggle so the reader can audit the shift.
 */

const SIZE = 320
const CENTER = SIZE / 2
const R_OUTER = 132
const R_INNER = 36
const TICK_HOURS = [0, 6, 12, 18]

// 0h at top, clockwise. Hour h sits at angle (h * 15 - 90) degrees.
const angleFor = (h) => ((h * 15 - 90) * Math.PI) / 180
const polar = (h, r) => [
  CENTER + Math.cos(angleFor(h)) * r,
  CENTER + Math.sin(angleFor(h)) * r,
]

// SVG arc path between two hour boundaries — used for the sleep-window wedge.
const wedgePath = (startHour, endHour, rInner, rOuter) => {
  // The wedge spans [startHour, endHour); represent each hour boundary as
  // the angle at its leading edge so the wedge encloses whole hour bars.
  const a0 = ((startHour * 15 - 90 - 7.5) * Math.PI) / 180
  const a1 = ((endHour * 15 - 90 - 7.5) * Math.PI) / 180
  const span = (endHour - startHour + 24) % 24
  const largeArc = span > 12 ? 1 : 0
  const [x0o, y0o] = [CENTER + Math.cos(a0) * rOuter, CENTER + Math.sin(a0) * rOuter]
  const [x1o, y1o] = [CENTER + Math.cos(a1) * rOuter, CENTER + Math.sin(a1) * rOuter]
  const [x1i, y1i] = [CENTER + Math.cos(a1) * rInner, CENTER + Math.sin(a1) * rInner]
  const [x0i, y0i] = [CENTER + Math.cos(a0) * rInner, CENTER + Math.sin(a0) * rInner]
  return [
    `M ${x0o} ${y0o}`,
    `A ${rOuter} ${rOuter} 0 ${largeArc} 1 ${x1o} ${y1o}`,
    `L ${x1i} ${y1i}`,
    `A ${rInner} ${rInner} 0 ${largeArc} 0 ${x0i} ${y0i}`,
    'Z',
  ].join(' ')
}

const readDist = (dist, h) => {
  if (!dist) return 0
  // JSON serialization turns int keys into strings; tolerate both.
  return Number(dist[h] ?? dist[String(h)] ?? 0)
}

export default function ActivityRhythm({ timezone }) {
  const [view, setView] = useState('local') // 'local' | 'utc'

  if (!timezone || (timezone.sample_count || 0) < 5) return null

  const offset = Number(timezone.utc_offset || 0)
  const dist = timezone.hourly_distribution || {}
  // sleep_window is a tuple (start, end) in UTC; JSON-serialized as array.
  const [sleepStartUtc, sleepEndUtc] = timezone.sleep_window || [0, 5]

  const { bars, peakHours, sleepStart, sleepEnd, hourLabel } = useMemo(() => {
    const showLocal = view === 'local'
    const shift = showLocal ? offset : 0
    const localized = Array.from({ length: 24 }, (_, h) => {
      const utcH = (h - shift + 24) % 24
      return { h, count: readDist(dist, utcH) }
    })
    const max = Math.max(1, ...localized.map((b) => b.count))
    const bars = localized.map((b) => ({
      ...b,
      norm: b.count / max,
    }))
    const peak = Math.max(...localized.map((b) => b.count))
    const peakHours = new Set(localized.filter((b) => b.count === peak && peak > 0).map((b) => b.h))
    const sleepStart = (sleepStartUtc + shift + 24) % 24
    const sleepEnd = (sleepEndUtc + shift + 24) % 24
    const hourLabel = (h) => (showLocal ? `${h}h` : `${h}Z`)
    return { bars, peakHours, sleepStart, sleepEnd, hourLabel }
  }, [view, offset, dist, sleepStartUtc, sleepEndUtc])

  const offsetSign = offset >= 0 ? '+' : ''
  const region = timezone.regions?.[0] || `UTC${offsetSign}${offset}`

  return (
    <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-4 mt-3">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">
            Activity Rhythm
          </span>
          <span
            className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#1e1e2e] text-gray-400 border border-dashed border-[#1e1e2e]"
            title="Inferred from finding timestamps; not a confirmed schedule."
          >
            Inferred
          </span>
        </div>
        <div className="flex items-center gap-1 text-[11px]">
          <button
            type="button"
            onClick={() => setView('local')}
            className={`px-2 py-0.5 rounded font-mono ${
              view === 'local'
                ? 'bg-[#3388ff]/15 text-[#3388ff] border border-[#3388ff]/30'
                : 'text-gray-500 border border-transparent hover:text-gray-300'
            }`}
            title="Inferred local time (apply utc_offset to UTC distribution)"
          >
            Local · UTC{offsetSign}{offset}
          </button>
          <button
            type="button"
            onClick={() => setView('utc')}
            className={`px-2 py-0.5 rounded font-mono ${
              view === 'utc'
                ? 'bg-[#3388ff]/15 text-[#3388ff] border border-[#3388ff]/30'
                : 'text-gray-500 border border-transparent hover:text-gray-300'
            }`}
            title="Raw UTC distribution"
          >
            UTC
          </button>
        </div>
      </div>

      <div className="flex justify-center">
        <svg viewBox={`0 0 ${SIZE} ${SIZE}`} className="w-full max-w-[320px]" role="img"
             aria-label="24-hour activity rhythm clock">
          {/* dial ring */}
          <circle cx={CENTER} cy={CENTER} r={R_OUTER} fill="none" stroke="#1e1e2e" strokeWidth="1.5" />
          <circle cx={CENTER} cy={CENTER} r={R_INNER} fill="none" stroke="#1e1e2e" strokeWidth="1" />

          {/* sleep window wedge */}
          <path
            d={wedgePath(sleepStart, sleepEnd, R_INNER - 2, R_OUTER + 4)}
            fill="#ff224422"
            stroke="#ff224455"
            strokeWidth="1"
          >
            <title>
              Quietest 5h block — inferred sleep window {sleepStart}h–{sleepEnd}h
              {view === 'local' ? ' local' : ' UTC'}
            </title>
          </path>

          {/* hour bars */}
          {bars.map(({ h, count, norm }) => {
            const r1 = R_INNER + 4
            const r2 = R_INNER + 4 + (R_OUTER - R_INNER - 8) * norm
            const [x1, y1] = polar(h, r1)
            const [x2, y2] = polar(h, r2)
            const isPeak = peakHours.has(h) && count > 0
            return (
              <g key={h}>
                <line
                  x1={x1}
                  y1={y1}
                  x2={x2}
                  y2={y2}
                  stroke={isPeak ? '#00ff88' : '#3388ff'}
                  strokeOpacity={isPeak ? 1 : 0.55}
                  strokeWidth="6"
                  strokeLinecap="round"
                >
                  <title>{hourLabel(h)} · {count} event{count === 1 ? '' : 's'}</title>
                </line>
              </g>
            )
          })}

          {/* hour ticks */}
          {TICK_HOURS.map((h) => {
            const [tx, ty] = polar(h, R_OUTER + 14)
            return (
              <text
                key={h}
                x={tx}
                y={ty}
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize="11"
                fontFamily="ui-monospace, monospace"
                fill="#666688"
              >
                {hourLabel(h)}
              </text>
            )
          })}

          {/* center label */}
          <text x={CENTER} y={CENTER - 6} textAnchor="middle" fontSize="12"
                fontFamily="ui-monospace, monospace" fill="#e5e7eb">
            UTC{offsetSign}{offset}
          </text>
          <text x={CENTER} y={CENTER + 10} textAnchor="middle" fontSize="11"
                fontFamily="ui-sans-serif, system-ui" fill="#9ca3af">
            {region}
          </text>
        </svg>
      </div>

      <div className="flex items-center justify-center gap-3 mt-2 text-[11px] text-gray-500">
        <span>{timezone.sample_count} timestamp{timezone.sample_count === 1 ? '' : 's'}</span>
        <span className="text-gray-600">·</span>
        <span>{Math.round((timezone.confidence || 0) * 100)}% confidence</span>
        <span className="text-gray-600">·</span>
        <span className="inline-flex items-center gap-1">
          <span className="inline-block w-2 h-2 rounded-sm bg-[#ff224455] border border-[#ff224455]" />
          sleep window
        </span>
      </div>
    </div>
  )
}
