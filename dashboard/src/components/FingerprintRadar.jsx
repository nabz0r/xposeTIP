import React, { useMemo, useState } from 'react'

const AXIS_LABELS = [
  { key: 'accounts', label: 'accounts' },
  { key: 'platforms', label: 'platforms' },
  { key: 'username_reuse', label: 'username reuse' },
  { key: 'breaches', label: 'breaches' },
  { key: 'geo_spread', label: 'geo spread' },
  { key: 'data_leaked', label: 'data leaked' },
  { key: 'email_age', label: 'email age' },
  { key: 'security', label: 'security' },
]

const RAW_LABELS = {
  accounts: (v) => `${v} accounts found`,
  platforms: (v) => `${v} unique platforms`,
  username_reuse: (v) => `${v} usernames reused`,
  breaches: (v) => `${v} confirmed breaches`,
  geo_spread: (v) => `${v} countries detected`,
  data_leaked: (v) => `${v} data types exposed`,
  email_age: (v) => `${v} years online`,
  security: (v) => `${v} security weaknesses`,
}

function polarToCartesian(cx, cy, r, i, total = 8) {
  const angle = (2 * Math.PI * i / total) - (Math.PI / 2)
  return { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) }
}

export default function FingerprintRadar({ fingerprint, size = 'large', animate = true }) {
  const [hoverAxis, setHoverAxis] = useState(null)
  const [hoverScar, setHoverScar] = useState(null)

  const isSmall = size === 'small'
  const w = isSmall ? 120 : 500
  const h = isSmall ? 120 : 500
  const cx = w / 2
  const cy = h / 2
  const radius = isSmall ? 44 : 180

  const axes = fingerprint?.axes || {}
  const color = fingerprint?.color || '#1D9E75'
  const fillColor = fingerprint?.fill_color || 'rgba(29,158,117,0.12)'
  const hash = fingerprint?.hash || '--------'
  const score = fingerprint?.score ?? 0
  const riskLevel = fingerprint?.risk_level || 'LOW'
  const label = fingerprint?.label || ''
  const scars = fingerprint?.scars || []
  const rawValues = fingerprint?.raw_values || {}

  const points = useMemo(() => {
    return AXIS_LABELS.map((a, i) => {
      const val = Math.max(0.08, axes[a.key] || 0)
      return polarToCartesian(cx, cy, radius * val, i)
    })
  }, [axes, cx, cy, radius])

  const edgePoints = useMemo(() => {
    return AXIS_LABELS.map((_, i) => polarToCartesian(cx, cy, radius, i))
  }, [cx, cy, radius])

  const polygonStr = points.map(p => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ')

  if (isSmall) {
    return (
      <div className="relative group" title={`${hash} · score ${score}`}>
        <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}
          role="img" aria-label={`Fingerprint score ${score}, ${riskLevel}`}>
          {/* Background circle to define radar area */}
          <circle cx={cx} cy={cy} r={radius} fill="#1e1e2e" opacity="0.15" />
          {/* Grid */}
          {[0.5, 1.0].map(pct => (
            <circle key={pct} cx={cx} cy={cy} r={radius * pct}
              fill="none" stroke="#1e1e2e" strokeWidth="0.5" />
          ))}
          {/* Polygon */}
          <polygon points={polygonStr} fill={fillColor} stroke={color} strokeWidth="1.5"
            style={{ transition: 'all 0.5s ease' }} />
          {/* Vertex dots */}
          {points.map((p, i) => (
            <circle key={i} cx={p.x} cy={p.y} r="2" fill={color}>
              {animate && <animate attributeName="r" values="2;3;2"
                dur={`${1.5 + (axes[AXIS_LABELS[i].key] || 0) * 2}s`} repeatCount="indefinite" />}
            </circle>
          ))}
          {/* Center */}
          <circle cx={cx} cy={cy} r="2" fill={color} opacity="0.5" />
        </svg>
      </div>
    )
  }

  // Large version
  return (
    <div className="relative">
      <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}
        role="img" aria-label={`Digital fingerprint. Risk level: ${riskLevel}. Score: ${score}. ${
          Object.entries(rawValues).map(([k, v]) => `${k.replace(/_/g, ' ')}: ${v}`).join(', ')
        }`}>
        {/* Grid circles */}
        {[0.25, 0.5, 0.75, 1.0].map(pct => (
          <circle key={pct} cx={cx} cy={cy} r={radius * pct}
            fill="none" stroke="#1e1e2e" strokeWidth="1" />
        ))}

        {/* Axis lines + labels */}
        {AXIS_LABELS.map((a, i) => {
          const edge = edgePoints[i]
          const labelR = radius + 28
          const lp = polarToCartesian(cx, cy, labelR, i)
          let anchor = 'middle'
          if (lp.x < cx - 20) anchor = 'end'
          else if (lp.x > cx + 20) anchor = 'start'
          const isHovered = hoverAxis === i
          const val = axes[a.key] || 0

          return (
            <g key={a.key}>
              <line x1={cx} y1={cy} x2={edge.x} y2={edge.y}
                stroke={isHovered ? color : '#1e1e2e'} strokeWidth={isHovered ? 1.5 : 1}
                style={{ transition: 'all 0.3s' }} />
              <text x={lp.x} y={lp.y}
                fill={isHovered ? '#fff' : '#666'}
                fontSize="11" fontFamily="Inter, sans-serif"
                textAnchor={anchor} dominantBaseline="middle"
                style={{ transition: 'fill 0.3s', cursor: 'default' }}
                onMouseEnter={() => setHoverAxis(i)}
                onMouseLeave={() => setHoverAxis(null)}>
                {a.label}
              </text>
              {/* Value text on hover */}
              {isHovered && (
                <text x={lp.x} y={lp.y + 16}
                  fill={color} fontSize="10" fontFamily="JetBrains Mono, monospace"
                  textAnchor={anchor} dominantBaseline="middle">
                  {(val * 100).toFixed(0)}%
                </text>
              )}
            </g>
          )
        })}

        {/* Filled polygon */}
        <polygon points={polygonStr} fill={fillColor} stroke={color} strokeWidth="2"
          style={{ transition: 'all 0.5s ease' }} />

        {/* Scars (correlated axis connections) */}
        {scars.map((scar, si) => {
          const fp = points[scar.from]
          const tp = points[scar.to]
          if (!fp || !tp) return null
          const isHoveredScar = hoverScar === si
          return (
            <g key={si}>
              <line x1={fp.x} y1={fp.y} x2={tp.x} y2={tp.y}
                stroke={color} strokeWidth={isHoveredScar ? 2.5 : 1.5}
                strokeDasharray="6,4" opacity={isHoveredScar ? 0.9 : 0.4}
                style={{ cursor: 'pointer', transition: 'all 0.3s' }}
                onMouseEnter={() => setHoverScar(si)}
                onMouseLeave={() => setHoverScar(null)}>
                <animate attributeName="stroke-dashoffset"
                  from="0" to="-20" dur="2s" repeatCount="indefinite" />
              </line>
            </g>
          )
        })}

        {/* Vertex dots with pulse */}
        {points.map((p, i) => {
          const val = axes[AXIS_LABELS[i].key] || 0
          const pulseSpeed = Math.max(0.8, 3 - val * 3)
          const isHovered = hoverAxis === i
          return (
            <g key={i}
              onMouseEnter={() => setHoverAxis(i)}
              onMouseLeave={() => setHoverAxis(null)}
              style={{ cursor: 'default' }}>
              {/* Outer glow on hover */}
              {isHovered && (
                <circle cx={p.x} cy={p.y} r="12" fill={color} opacity="0.15" />
              )}
              <circle cx={p.x} cy={p.y} r={isHovered ? 6 : 4} fill={color}
                style={{ transition: 'r 0.2s' }}>
                {animate && (
                  <animate attributeName="r" values={isHovered ? '6;8;6' : '4;5.5;4'}
                    dur={`${pulseSpeed}s`} repeatCount="indefinite" />
                )}
              </circle>
            </g>
          )
        })}

        {/* Vertex raw value labels (non-zero only) */}
        {points.map((p, i) => {
          const rawKey = AXIS_LABELS[i].key === 'email_age' ? 'email_age_years' :
                         AXIS_LABELS[i].key === 'security' ? 'security_weak' :
                         AXIS_LABELS[i].key
          const rawVal = rawValues[rawKey]
          if (!rawVal || rawVal === 0) return null
          // Offset label slightly outward from the vertex
          const labelP = polarToCartesian(cx, cy, radius * Math.max(0.08, axes[AXIS_LABELS[i].key] || 0) + 12, i)
          return (
            <text key={`val-${i}`} x={labelP.x} y={labelP.y}
              fill={color} fontSize="10" fontFamily="JetBrains Mono, monospace"
              textAnchor="middle" dominantBaseline="middle" opacity="0.8">
              {typeof rawVal === 'number' && rawVal % 1 !== 0 ? rawVal.toFixed(1) : rawVal}
            </text>
          )
        })}

        {/* Center dot + ring */}
        <circle cx={cx} cy={cy} r="6" fill="none" stroke={color} strokeWidth="1" opacity="0.3" />
        <circle cx={cx} cy={cy} r="3" fill={color} opacity="0.6" />
      </svg>

      {/* Hover tooltip for axis */}
      {hoverAxis !== null && (
        <div className="absolute top-2 right-2 bg-[#12121a] border border-[#1e1e2e] rounded-lg px-3 py-2 text-xs pointer-events-none z-10"
          style={{ borderColor: color + '40' }}>
          <div className="font-medium text-white">{AXIS_LABELS[hoverAxis].label}</div>
          <div className="font-mono mt-0.5" style={{ color }}>
            {RAW_LABELS[AXIS_LABELS[hoverAxis].key]?.(rawValues[
              AXIS_LABELS[hoverAxis].key === 'email_age' ? 'email_age_years' :
              AXIS_LABELS[hoverAxis].key === 'security' ? 'security_weak' :
              AXIS_LABELS[hoverAxis].key
            ] || 0)}
          </div>
        </div>
      )}

      {/* Hover tooltip for scar */}
      {hoverScar !== null && scars[hoverScar] && (
        <div className="absolute top-2 right-2 bg-[#12121a] border border-[#1e1e2e] rounded-lg px-3 py-2 text-xs pointer-events-none z-10"
          style={{ borderColor: color + '40' }}>
          <div className="font-medium" style={{ color }}>{scars[hoverScar].label}</div>
          <div className="text-gray-400 mt-0.5">
            {AXIS_LABELS[scars[hoverScar].from]?.label} ↔ {AXIS_LABELS[scars[hoverScar].to]?.label}
          </div>
        </div>
      )}

      {/* Footer: hash + risk */}
      <div className="flex items-center justify-center gap-3 -mt-2">
        <span className="text-xs font-mono" style={{ color }}>
          fingerprint: {hash}
        </span>
        {label && (
          <>
            <span className="text-gray-600">·</span>
            <span className="text-xs text-gray-400">{label}</span>
          </>
        )}
      </div>
      <div className="flex items-center justify-center gap-2 mt-1">
        <span className="text-[10px] font-mono px-2 py-0.5 rounded-full"
          style={{ backgroundColor: color + '20', color }}>
          {riskLevel}
        </span>
        <span className="text-xs font-mono text-gray-500">score {score}</span>
      </div>
    </div>
  )
}

export function FingerprintTimeline({ snapshots = [], onSelectSnapshot }) {
  if (!snapshots.length) return null

  return (
    <div>
      <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">
        Fingerprint Evolution ({snapshots.length} scans)
      </h3>
      <div className="flex gap-4 overflow-x-auto pb-3">
        {snapshots.map((snap, i) => {
          const prev = i > 0 ? snapshots[i - 1] : null
          const scoreDiff = prev ? snap.score - prev.score : 0
          const color = snap.score <= 20 ? '#1D9E75' : snap.score <= 50 ? '#EF9F27' : snap.score <= 75 ? '#D85A30' : '#E24B4A'

          // Build mini polygon for snapshot
          const axes = snap.axes || {}
          const miniCx = 50, miniCy = 50, miniR = 36
          const miniPoints = AXIS_LABELS.map((a, j) => {
            const val = Math.max(0.08, axes[a.key] || 0)
            const pt = polarToCartesian(miniCx, miniCy, miniR * val, j)
            return `${pt.x.toFixed(1)},${pt.y.toFixed(1)}`
          }).join(' ')

          const date = snap.computed_at ? new Date(snap.computed_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : ''

          return (
            <div key={i} className="shrink-0 bg-[#12121a] border border-[#1e1e2e] rounded-lg p-3 w-44 hover:border-gray-600 transition-colors cursor-pointer"
              onClick={() => onSelectSnapshot?.(snap)}>
              <svg width="100" height="100" viewBox="0 0 100 100" className="mx-auto">
                <circle cx={miniCx} cy={miniCy} r={miniR} fill="none" stroke="#1e1e2e" strokeWidth="0.5" />
                <polygon points={miniPoints} fill={color + '18'} stroke={color} strokeWidth="1.5"
                  style={{ transition: 'all 0.3s' }} />
                <circle cx={miniCx} cy={miniCy} r="2" fill={color} opacity="0.5" />
              </svg>
              <div className="text-center mt-1">
                <div className="text-xs text-gray-400">{date}</div>
                <div className="font-mono text-sm font-bold" style={{ color }}>
                  {snap.score}
                  {scoreDiff !== 0 && (
                    <span className={`text-[10px] ml-1 ${scoreDiff > 0 ? 'text-[#ff2244]' : 'text-[#00ff88]'}`}>
                      {scoreDiff > 0 ? '+' : ''}{scoreDiff}
                    </span>
                  )}
                </div>
                <div className="text-[10px] font-mono text-gray-600">{snap.hash}</div>
                {snap.label && <div className="text-[10px] text-gray-500 mt-0.5 truncate">{snap.label}</div>}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export function FingerprintCompare({ targetA, targetB }) {
  if (!targetA?.fingerprint || !targetB?.fingerprint) return null

  return (
    <div className="grid grid-cols-2 gap-6">
      {[targetA, targetB].map((t, i) => (
        <div key={i} className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-4">
          <div className="text-sm font-mono text-center text-gray-400 mb-2">{t.email}</div>
          <FingerprintRadar fingerprint={t.fingerprint} size="large" animate={false} />
          <div className="grid grid-cols-2 gap-2 mt-3">
            {AXIS_LABELS.map(a => {
              const val = t.fingerprint.axes?.[a.key] || 0
              return (
                <div key={a.key} className="flex items-center justify-between text-[10px] px-2 py-1 rounded bg-[#0a0a0f]">
                  <span className="text-gray-500">{a.label}</span>
                  <span className="font-mono" style={{ color: t.fingerprint.color }}>
                    {(val * 100).toFixed(0)}%
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      ))}
    </div>
  )
}
