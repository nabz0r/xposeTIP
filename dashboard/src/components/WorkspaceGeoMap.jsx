import { useMemo, useState } from 'react'
import { Globe } from 'lucide-react'

// Simple Mercator projection: lat/lng → x/y on a 960×480 SVG
function project(lat, lng) {
  const x = (lng + 180) * (960 / 360)
  const latRad = (lat * Math.PI) / 180
  const mercN = Math.log(Math.tan(Math.PI / 4 + latRad / 2))
  const y = 240 - (960 * mercN) / (2 * Math.PI)
  return [Math.max(0, Math.min(960, x)), Math.max(0, Math.min(480, y))]
}

// Simplified world map outline (same as LocationMap)
const WORLD_PATH =
  'M131,97L137,95L141,97L141,101L137,103L131,101Z ' +
  'M150,85L175,75L195,78L210,90L205,105L195,110L180,115L165,120L155,118L145,110L140,100Z ' +
  'M170,125L178,130L185,145L190,160L185,170L175,175L165,165L160,150L162,135Z ' +
  'M180,175L195,180L200,200L195,220L185,235L175,230L170,215L172,195Z ' +
  'M430,65L445,55L470,50L500,55L520,60L540,65L545,80L540,95L520,105L500,110L480,115L460,110L445,100L435,85Z ' +
  'M450,120L475,110L510,115L540,120L555,130L560,150L550,170L530,180L500,185L480,175L465,155L455,135Z ' +
  'M475,185L500,190L520,200L525,220L515,240L500,245L485,235L475,215L472,195Z ' +
  'M560,65L590,55L630,50L670,60L700,70L720,80L730,95L720,110L700,115L680,110L660,100L640,95L620,90L600,85L575,80Z ' +
  'M620,100L650,105L680,115L700,120L710,130L700,145L680,155L660,160L640,155L625,140L615,120Z ' +
  'M600,130L615,135L620,150L615,165L600,175L585,170L580,155L585,140Z ' +
  'M700,155L720,150L740,160L750,180L745,200L730,210L715,205L705,190L700,170Z ' +
  'M740,220L770,215L800,225L810,250L800,270L780,280L760,275L745,260L740,240Z ' +
  'M630,170L645,175L655,185L650,200L635,195L625,185Z'

const riskColor = (score) => {
  if (score >= 60) return '#ff2244'
  if (score >= 30) return '#ff8800'
  if (score >= 15) return '#ffcc00'
  return '#00ff88'
}

const pinSize = (score) => Math.max(8, Math.min(24, 6 + (score || 0) * 0.3))

export default function WorkspaceGeoMap({ targets = [], onTargetClick }) {
  const [tooltip, setTooltip] = useState(null)
  const [expandedCluster, setExpandedCluster] = useState(null)

  const { pins, locatedCount, unlocatedCount, countryCount } = useMemo(() => {
    const located = targets
      .filter(t => t.location_data?.lat && t.location_data?.lon)
      .map(t => ({
        id: t.id,
        name: t.primary_name || t.display_name || t.email?.split('@')[0] || '',
        email: t.email,
        score: t.exposure_score || 0,
        threat: t.threat_score || 0,
        color: riskColor(t.exposure_score || 0),
        size: pinSize(t.exposure_score || 0),
        lat: t.location_data.lat,
        lon: t.location_data.lon,
        label: t.location_data.label,
        type: t.location_data.type,
        avatar_seed: t.fingerprint_avatar_seed,
      }))

    // Cluster nearby pins (within ~3 degrees)
    const clusters = []
    const assigned = new Set()

    for (let i = 0; i < located.length; i++) {
      if (assigned.has(i)) continue
      const cluster = [located[i]]
      assigned.add(i)

      for (let j = i + 1; j < located.length; j++) {
        if (assigned.has(j)) continue
        const dist = Math.abs(located[i].lat - located[j].lat) + Math.abs(located[i].lon - located[j].lon)
        if (dist < 3) {
          cluster.push(located[j])
          assigned.add(j)
        }
      }

      const avgLat = cluster.reduce((s, p) => s + p.lat, 0) / cluster.length
      const avgLon = cluster.reduce((s, p) => s + p.lon, 0) / cluster.length
      const maxScore = Math.max(...cluster.map(p => p.score))

      clusters.push({
        targets: cluster,
        lat: avgLat,
        lon: avgLon,
        label: cluster[0].label,
        count: cluster.length,
        maxScore,
        color: riskColor(maxScore),
        size: cluster.length > 1 ? 28 : pinSize(maxScore),
      })
    }

    const lc = located.length
    const countries = new Set(located.map(p => p.label).filter(Boolean))

    return {
      pins: clusters,
      locatedCount: lc,
      unlocatedCount: targets.length - lc,
      countryCount: countries.size,
    }
  }, [targets])

  if (!targets.length) return null

  return (
    <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl overflow-hidden">
      <div className="px-5 py-4 border-b border-[#1e1e2e] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Globe className="w-4 h-4 text-[#00ff88]" />
          <h2 className="text-sm font-semibold">Geographic Exposure</h2>
        </div>
        <span className="text-xs text-gray-500">
          {locatedCount} target{locatedCount !== 1 ? 's' : ''} in {countryCount} location{countryCount !== 1 ? 's' : ''}
          {unlocatedCount > 0 && ` \u00b7 ${unlocatedCount} without location`}
        </span>
      </div>

      <div className="relative p-4">
        <svg viewBox="0 0 960 480" className="w-full" style={{ maxHeight: 360 }}>
          {/* World outline */}
          <path d={WORLD_PATH} fill="#1a1a2e" stroke="#2a2a3e" strokeWidth="1" />

          {/* Grid lines */}
          {[-60, -30, 0, 30, 60].map(lat => {
            const [, y] = project(lat, 0)
            return <line key={`lat${lat}`} x1="0" y1={y} x2="960" y2={y} stroke="#1a1a2e" strokeWidth="0.5" />
          })}
          {[-120, -60, 0, 60, 120].map(lng => {
            const [x] = project(0, lng)
            return <line key={`lng${lng}`} x1={x} y1="0" x2={x} y2="480" stroke="#1a1a2e" strokeWidth="0.5" />
          })}

          {/* Target pins */}
          {pins.map((pin, i) => {
            const [x, y] = project(pin.lat, pin.lon)
            const r = pin.size / 2
            const isCluster = pin.count > 1
            const isSelfReported = pin.targets[0]?.type === 'self_reported'

            return (
              <g
                key={i}
                transform={`translate(${x},${y})`}
                className="cursor-pointer"
                onMouseEnter={(e) => {
                  const rect = e.currentTarget.closest('svg').getBoundingClientRect()
                  setTooltip({
                    x: e.clientX - rect.left,
                    y: e.clientY - rect.top,
                    pin,
                  })
                }}
                onMouseLeave={() => setTooltip(null)}
                onClick={() => {
                  if (isCluster) {
                    setExpandedCluster(expandedCluster === i ? null : i)
                  } else {
                    onTargetClick?.(pin.targets[0].id)
                  }
                }}
              >
                {/* Glow effect */}
                <circle r={r + 4} fill={pin.color} opacity="0.15" />

                {/* Pin circle */}
                <circle
                  r={r}
                  fill="#0a0a12"
                  stroke={pin.color}
                  strokeWidth={isSelfReported ? 2 : 1.5}
                  strokeDasharray={isSelfReported ? 'none' : '3,2'}
                />

                {/* Content: count for clusters, dot for single */}
                {isCluster ? (
                  <text
                    textAnchor="middle"
                    dominantBaseline="central"
                    fill={pin.color}
                    fontSize={r * 0.9}
                    fontWeight="bold"
                    fontFamily="monospace"
                  >
                    {pin.count}
                  </text>
                ) : (
                  <circle r={r * 0.35} fill={pin.color} />
                )}
              </g>
            )
          })}
        </svg>

        {/* Tooltip */}
        {tooltip && (
          <div
            className="absolute z-10 pointer-events-none bg-[#0a0a12] border border-[#2a2a3e] rounded-lg px-3 py-2 text-xs shadow-lg"
            style={{
              left: Math.min(tooltip.x + 12, 600),
              top: tooltip.y - 8,
              maxWidth: 260,
            }}
          >
            {tooltip.pin.targets.slice(0, 5).map((t, i) => (
              <div key={i} className={i > 0 ? 'mt-1 pt-1 border-t border-[#1e1e2e]' : ''}>
                <div className="font-semibold text-white truncate">{t.name}</div>
                <div className="text-gray-500 truncate">{t.email}</div>
                <div className="flex items-center gap-2 mt-0.5">
                  <span style={{ color: t.color }}>Score: {t.score}</span>
                  {t.type === 'server' && <span className="text-gray-600">(server)</span>}
                </div>
              </div>
            ))}
            {tooltip.pin.count > 5 && (
              <div className="text-gray-500 mt-1">+{tooltip.pin.count - 5} more</div>
            )}
            <div className="text-gray-600 mt-1">{tooltip.pin.label}</div>
          </div>
        )}

        {/* Expanded cluster list */}
        {expandedCluster !== null && pins[expandedCluster] && (
          <div className="absolute bottom-4 right-4 bg-[#0a0a12] border border-[#2a2a3e] rounded-lg p-3 text-xs shadow-lg max-h-48 overflow-y-auto" style={{ maxWidth: 240 }}>
            <div className="text-gray-400 mb-2 font-semibold">
              {pins[expandedCluster].label} ({pins[expandedCluster].count})
            </div>
            {pins[expandedCluster].targets.map((t, i) => (
              <div
                key={i}
                className="py-1 px-1 rounded cursor-pointer hover:bg-[#1a1a2e] flex items-center justify-between"
                onClick={() => onTargetClick?.(t.id)}
              >
                <span className="text-white truncate">{t.name}</span>
                <span className="ml-2 font-mono" style={{ color: t.color }}>{t.score}</span>
              </div>
            ))}
          </div>
        )}

        {/* Legend */}
        <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
          <span className="flex items-center gap-1">
            <span className="inline-block w-2 h-2 rounded-full bg-[#00ff88]" /> Low (0-14)
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block w-2 h-2 rounded-full bg-[#ffcc00]" /> Moderate (15-29)
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block w-2 h-2 rounded-full bg-[#ff8800]" /> High (30-59)
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block w-2 h-2 rounded-full bg-[#ff2244]" /> Critical (60+)
          </span>
          <span className="ml-auto flex items-center gap-2">
            <span className="inline-block w-4 border-t-2 border-[#666]" /> Server
            <span className="inline-block w-4 border-t-2 border-[#666] border-solid" style={{ borderStyle: 'solid' }} /> Self-reported
          </span>
        </div>
      </div>
    </div>
  )
}
