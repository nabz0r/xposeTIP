import { useMemo, useRef, useState } from 'react'
import { Globe } from 'lucide-react'
import * as d3 from 'd3'
import {
  useWorldData,
  useZoom,
  createProjection,
  createPathGenerator,
  projectPoint,
  ISO_ALPHA2_TO_NUMERIC,
  MAP_WIDTH,
  MAP_HEIGHT,
} from '../lib/geo'

const riskColor = (score) => {
  if (score >= 60) return '#ff2244'
  if (score >= 30) return '#ff8800'
  if (score >= 15) return '#ffcc00'
  return '#00ff88'
}

const pinSize = (score) => Math.max(8, Math.min(24, 6 + (score || 0) * 0.3))

export default function WorkspaceGeoMap({ targets = [], onTargetClick }) {
  const svgRef = useRef(null)
  const gRef = useRef(null)
  const [tooltip, setTooltip] = useState(null)
  const [expandedCluster, setExpandedCluster] = useState(null)
  const [selectedCountry, setSelectedCountry] = useState(null) // ISO numeric

  const { data: world, loading: worldLoading } = useWorldData()
  useZoom(svgRef, gRef)

  const projection = useMemo(() => createProjection(), [])
  const pathGen = useMemo(() => createPathGenerator(projection), [projection])

  const countryDensity = useMemo(() => {
    const counts = {}
    for (const t of targets) {
      const cc = (t.country_code || '').toUpperCase()
      if (!cc) continue
      const iso = ISO_ALPHA2_TO_NUMERIC[cc]
      if (!iso) continue
      counts[iso] = (counts[iso] || 0) + 1
    }
    return counts
  }, [targets])

  const maxCountryCount = useMemo(
    () => Math.max(1, ...Object.values(countryDensity)),
    [countryDensity]
  )

  const densityScale = useMemo(
    () => d3.scaleSequential(d3.interpolateRgb('#1a1a2e', '#00ff88'))
      .domain([0, maxCountryCount]),
    [maxCountryCount]
  )

  const selectedCountryTargets = useMemo(() => {
    if (!selectedCountry) return []
    const alpha2 = Object.entries(ISO_ALPHA2_TO_NUMERIC)
      .find(([, num]) => num === selectedCountry)?.[0]
    if (!alpha2) return []
    return targets.filter((t) => (t.country_code || '').toUpperCase() === alpha2)
  }, [selectedCountry, targets])

  const { pins, locatedCount, unlocatedCount, countryCount } = useMemo(() => {
    const located = []
    for (const t of targets) {
      const name = t.primary_name || t.display_name || t.email?.split('@')[0] || ''
      const base = {
        id: t.id,
        name,
        email: t.email,
        score: t.exposure_score || 0,
        threat: t.threat_score || 0,
        color: riskColor(t.exposure_score || 0),
        size: pinSize(t.exposure_score || 0),
      }

      if (t.location_data?.lat && t.location_data?.lon) {
        located.push({ ...base, lat: t.location_data.lat, lon: t.location_data.lon, label: t.location_data.label, type: t.location_data.type })
      } else if (t.user_locations?.length) {
        const ul = t.user_locations.find((u) => u.lat && u.lon)
        if (ul) located.push({ ...base, lat: ul.lat, lon: ul.lon, label: ul.city || ul.location || ul.country || '', type: 'self_reported' })
      }
      if (!located.find((p) => p.id === t.id) && t.geo_locations?.length) {
        const gl = t.geo_locations.find((g) => g.lat && g.lon)
        if (gl) located.push({ ...base, lat: gl.lat, lon: gl.lon, label: [gl.city, gl.country].filter(Boolean).join(', '), type: 'server' })
      }
    }

    const clusters = []
    const assigned = new Set()
    for (let i = 0; i < located.length; i++) {
      if (assigned.has(i)) continue
      const cluster = [located[i]]
      assigned.add(i)
      for (let j = i + 1; j < located.length; j++) {
        if (assigned.has(j)) continue
        const dist = Math.abs(located[i].lat - located[j].lat) + Math.abs(located[i].lon - located[j].lon)
        if (dist < 3) { cluster.push(located[j]); assigned.add(j) }
      }
      const avgLat = cluster.reduce((s, p) => s + p.lat, 0) / cluster.length
      const avgLon = cluster.reduce((s, p) => s + p.lon, 0) / cluster.length
      const maxScore = Math.max(...cluster.map((p) => p.score))
      clusters.push({
        targets: cluster, lat: avgLat, lon: avgLon, label: cluster[0].label,
        count: cluster.length, maxScore, color: riskColor(maxScore),
        size: cluster.length > 1 ? 28 : pinSize(maxScore),
      })
    }

    const lc = located.length
    const countries = new Set(located.map((p) => p.label).filter(Boolean))
    return { pins: clusters, locatedCount: lc, unlocatedCount: targets.length - lc, countryCount: countries.size }
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
          {unlocatedCount > 0 && ` · ${unlocatedCount} without location`}
        </span>
      </div>

      <div className="relative p-4">
        {worldLoading && (
          <div className="absolute inset-0 flex items-center justify-center text-xs text-gray-500 z-10">
            Loading world data…
          </div>
        )}

        <svg
          ref={svgRef}
          viewBox={`0 0 ${MAP_WIDTH} ${MAP_HEIGHT}`}
          className="w-full cursor-grab active:cursor-grabbing"
          style={{ maxHeight: 420, background: '#0a0a0f' }}
        >
          <g ref={gRef}>
            <rect x="0" y="0" width={MAP_WIDTH} height={MAP_HEIGHT} fill="#0a0a0f" />

            {/* Country polygons (density heatmap) */}
            {world?.features.map((f) => {
              const isoNum = String(f.id || '')
              const count = countryDensity[isoNum] || 0
              const isSelected = selectedCountry === isoNum
              const fillColor = count > 0 ? densityScale(count) : '#13131f'
              return (
                <path
                  key={isoNum || f.properties?.name}
                  d={pathGen(f) || ''}
                  fill={fillColor}
                  stroke={isSelected ? '#00ff88' : '#2a2a3e'}
                  strokeWidth={isSelected ? 1.5 : 0.4}
                  className="cursor-pointer transition-colors"
                  onMouseEnter={(e) => {
                    if (count === 0) return
                    const rect = svgRef.current?.getBoundingClientRect()
                    if (!rect) return
                    setTooltip({
                      x: e.clientX - rect.left,
                      y: e.clientY - rect.top,
                      country: { name: f.properties?.name || 'Unknown', count },
                    })
                  }}
                  onMouseLeave={() => setTooltip(null)}
                  onClick={() => {
                    if (count === 0) { setSelectedCountry(null); return }
                    setSelectedCountry(selectedCountry === isoNum ? null : isoNum)
                    setExpandedCluster(null)
                  }}
                />
              )
            })}

            {/* Target pins */}
            {pins.map((pin, i) => {
              const projected = projectPoint(projection, pin.lat, pin.lon)
              if (!projected) return null
              const [x, y] = projected
              const r = pin.size / 2
              const isCluster = pin.count > 1
              const isSelfReported = pin.targets[0]?.type === 'self_reported'

              return (
                <g
                  key={i}
                  transform={`translate(${x},${y})`}
                  className="cursor-pointer"
                  onMouseEnter={(e) => {
                    const rect = svgRef.current?.getBoundingClientRect()
                    if (!rect) return
                    setTooltip({
                      x: e.clientX - rect.left,
                      y: e.clientY - rect.top,
                      pin,
                    })
                  }}
                  onMouseLeave={() => setTooltip(null)}
                  onClick={(e) => {
                    e.stopPropagation()
                    if (isCluster) {
                      setExpandedCluster(expandedCluster === i ? null : i)
                      setSelectedCountry(null)
                    } else {
                      onTargetClick?.(pin.targets[0].id)
                    }
                  }}
                >
                  <circle r={r + 4} fill={pin.color} opacity="0.15" />
                  <circle
                    r={r}
                    fill="#0a0a12"
                    stroke={pin.color}
                    strokeWidth={isSelfReported ? 2 : 1.5}
                    strokeDasharray={isSelfReported ? 'none' : '3,2'}
                  />
                  {isCluster ? (
                    <text textAnchor="middle" dominantBaseline="central" fill={pin.color} fontSize={r * 0.9} fontWeight="bold" fontFamily="monospace">
                      {pin.count}
                    </text>
                  ) : (
                    <circle r={r * 0.35} fill={pin.color} />
                  )}
                </g>
              )
            })}
          </g>
        </svg>

        {/* Country tooltip */}
        {tooltip?.country && (
          <div
            className="absolute z-10 pointer-events-none bg-[#0a0a12] border border-[#00ff88]/40 rounded-lg px-3 py-1.5 text-xs shadow-lg"
            style={{ left: Math.min(tooltip.x + 12, 700), top: tooltip.y - 8 }}
          >
            <div className="font-semibold text-white">{tooltip.country.name}</div>
            <div className="text-[#00ff88] font-mono">{tooltip.country.count} target{tooltip.country.count !== 1 ? 's' : ''}</div>
          </div>
        )}

        {/* Pin tooltip */}
        {tooltip?.pin && (
          <div
            className="absolute z-10 pointer-events-none bg-[#0a0a12] border border-[#2a2a3e] rounded-lg px-3 py-2 text-xs shadow-lg"
            style={{ left: Math.min(tooltip.x + 12, 600), top: tooltip.y - 8, maxWidth: 260 }}
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
            {tooltip.pin.count > 5 && <div className="text-gray-500 mt-1">+{tooltip.pin.count - 5} more</div>}
            <div className="text-gray-600 mt-1">{tooltip.pin.label}</div>
          </div>
        )}

        {/* Expanded cluster list */}
        {expandedCluster !== null && pins[expandedCluster] && (
          <div className="absolute bottom-4 right-4 bg-[#0a0a12] border border-[#2a2a3e] rounded-lg p-3 text-xs shadow-lg max-h-48 overflow-y-auto" style={{ maxWidth: 240 }}>
            <div className="text-gray-400 mb-2 font-semibold">{pins[expandedCluster].label} ({pins[expandedCluster].count})</div>
            {pins[expandedCluster].targets.map((t, i) => (
              <div key={i} className="py-1 px-1 rounded cursor-pointer hover:bg-[#1a1a2e] flex items-center justify-between" onClick={() => onTargetClick?.(t.id)}>
                <span className="text-white truncate">{t.name}</span>
                <span className="ml-2 font-mono" style={{ color: t.color }}>{t.score}</span>
              </div>
            ))}
          </div>
        )}

        {/* Country-selected side panel */}
        {selectedCountry && selectedCountryTargets.length > 0 && (
          <div className="absolute top-4 right-4 bg-[#0a0a12] border border-[#00ff88]/40 rounded-lg p-3 text-xs shadow-lg max-h-64 overflow-y-auto" style={{ maxWidth: 280 }}>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[#00ff88] font-semibold">
                {selectedCountryTargets.length} target{selectedCountryTargets.length !== 1 ? 's' : ''} in country
              </span>
              <button onClick={() => setSelectedCountry(null)} className="text-gray-500 hover:text-white">×</button>
            </div>
            {selectedCountryTargets.map((t) => (
              <div
                key={t.id}
                className="py-1 px-1 rounded cursor-pointer hover:bg-[#1a1a2e] flex items-center justify-between gap-2"
                onClick={() => onTargetClick?.(t.id)}
              >
                <span className="text-white truncate">{t.primary_name || t.display_name || t.email}</span>
                <span className="ml-2 font-mono shrink-0" style={{ color: riskColor(t.exposure_score || 0) }}>{t.exposure_score || 0}</span>
              </div>
            ))}
          </div>
        )}

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-4 mt-3 text-xs text-gray-500">
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
          <span className="ml-auto text-[10px] text-gray-600">scroll to zoom · drag to pan · click country for breakdown</span>
        </div>
      </div>
    </div>
  )
}
