import { useMemo, useRef } from 'react'
import { Globe } from 'lucide-react'
import {
  useWorldData,
  useZoom,
  createProjection,
  createPathGenerator,
  projectPoint,
  ISO_ALPHA2_TO_NUMERIC,
  COUNTRY_CENTROIDS,
  MAP_WIDTH,
  MAP_HEIGHT,
} from '../lib/geo'

export default function LocationMap({ findings, userLocations, countryCode }) {
  const svgRef = useRef(null)
  const gRef = useRef(null)
  const { data: world, loading: worldLoading } = useWorldData()
  useZoom(svgRef, gRef)

  const projection = useMemo(() => createProjection(), [])
  const pathGen = useMemo(() => createPathGenerator(projection), [projection])

  const geoFindings = useMemo(
    () => findings.filter((f) => f.category === 'geolocation' && f.data?.latitude && f.data?.longitude),
    [findings]
  )

  const userPoints = useMemo(() => {
    if (!userLocations?.length) return []
    return userLocations
      .filter((u) => u.lat && u.lon)
      .map((u, i) => {
        const p = projectPoint(projection, u.lat, u.lon)
        if (!p) return null
        return { x: p[0], y: p[1], label: u.city || u.location || u.country || '?', source: u.source, type: 'self_reported', index: i }
      })
      .filter(Boolean)
  }, [userLocations, projection])

  const serverPoints = useMemo(() => {
    return geoFindings
      .map((f, i) => {
        const p = projectPoint(projection, f.data.latitude, f.data.longitude)
        if (!p) return null
        return { x: p[0], y: p[1], label: `${f.data.city || '?'}, ${f.data.country || '?'}`, source: f.data.isp || 'GeoIP', type: 'server', finding: f, index: i }
      })
      .filter(Boolean)
  }, [geoFindings, projection])

  const groundTruthPoint = useMemo(() => {
    if (!countryCode) return null
    const coords = COUNTRY_CENTROIDS[countryCode.toUpperCase()]
    if (!coords) return null
    const p = projectPoint(projection, coords[0], coords[1])
    if (!p) return null
    return { x: p[0], y: p[1], code: countryCode.toUpperCase() }
  }, [countryCode, projection])

  const groundTruthIso = useMemo(() => {
    if (!countryCode) return null
    return ISO_ALPHA2_TO_NUMERIC[countryCode.toUpperCase()] || null
  }, [countryCode])

  const hasData = userPoints.length > 0 || serverPoints.length > 0 || groundTruthPoint

  if (!hasData) {
    return (
      <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-8 text-center">
        <p className="text-gray-500 text-sm">No geolocation data available. Run a scan to discover location data from profiles and mail servers.</p>
      </div>
    )
  }

  return (
    <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl overflow-hidden">
      <div className="px-5 py-3 border-b border-[#1e1e2e] flex items-center gap-2">
        <Globe className="w-4 h-4 text-[#3388ff]" />
        <span className="text-sm font-semibold">Locations</span>
        {userPoints.length > 0 && <span className="text-[10px] text-[#00ff88] ml-2">{userPoints.length} self-reported</span>}
        {serverPoints.length > 0 && <span className="text-[10px] text-gray-600 ml-2">{serverPoints.length} mail server{serverPoints.length > 1 ? 's' : ''}</span>}
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
          style={{ maxHeight: 440, background: '#0a0a0f' }}
        >
          <g ref={gRef}>
            <rect x="0" y="0" width={MAP_WIDTH} height={MAP_HEIGHT} fill="#0a0a0f" />

            {/* Country polygons */}
            {world?.features.map((f) => {
              const isoNum = String(f.id || '')
              const isGroundTruth = groundTruthIso && isoNum === groundTruthIso
              return (
                <path
                  key={isoNum || f.properties?.name}
                  d={pathGen(f) || ''}
                  fill={isGroundTruth ? '#ffd70022' : '#13131f'}
                  stroke={isGroundTruth ? '#ffd700' : '#2a2a3e'}
                  strokeWidth={isGroundTruth ? 1.2 : 0.4}
                />
              )
            })}

            {/* Server location pulses (dim) */}
            {serverPoints.map((p, i) => (
              <g key={`srv-pulse-${i}`} opacity="0.3">
                <circle cx={p.x} cy={p.y} r="20" fill="none" stroke="#3388ff" strokeWidth="1" opacity="0.3">
                  <animate attributeName="r" from="8" to="30" dur="2s" repeatCount="indefinite" />
                  <animate attributeName="opacity" from="0.3" to="0" dur="2s" repeatCount="indefinite" />
                </circle>
              </g>
            ))}

            {/* User location pulses (bright) */}
            {userPoints.map((p, i) => (
              <g key={`usr-pulse-${i}`}>
                <circle cx={p.x} cy={p.y} r="20" fill="none" stroke="#00ff88" strokeWidth="1.5" opacity="0.5">
                  <animate attributeName="r" from="8" to="30" dur="2s" repeatCount="indefinite" />
                  <animate attributeName="opacity" from="0.6" to="0" dur="2s" repeatCount="indefinite" />
                </circle>
                <circle cx={p.x} cy={p.y} r="12" fill="none" stroke="#00ff88" strokeWidth="0.5" opacity="0.3">
                  <animate attributeName="r" from="6" to="20" dur="2s" begin="0.5s" repeatCount="indefinite" />
                  <animate attributeName="opacity" from="0.4" to="0" dur="2s" begin="0.5s" repeatCount="indefinite" />
                </circle>
              </g>
            ))}

            {/* Server location dots */}
            {serverPoints.map((p, i) => (
              <g key={`srv-dot-${i}`} opacity="0.4">
                <circle cx={p.x} cy={p.y} r="5" fill="#3388ff" opacity="0.3" />
                <circle cx={p.x} cy={p.y} r="3" fill="#3388ff" />
                <circle cx={p.x} cy={p.y} r="1" fill="#ffffff" />
              </g>
            ))}

            {/* User location dots */}
            {userPoints.map((p, i) => (
              <g key={`usr-dot-${i}`}>
                <circle cx={p.x} cy={p.y} r="7" fill="#00ff88" opacity="0.3" />
                <circle cx={p.x} cy={p.y} r="5" fill="#00ff88" />
                <circle cx={p.x} cy={p.y} r="2" fill="#ffffff" />
              </g>
            ))}

            {/* Ground truth pin */}
            {groundTruthPoint && (
              <g>
                <circle cx={groundTruthPoint.x} cy={groundTruthPoint.y} r="24" fill="none" stroke="#ffd700" strokeWidth="1.5" opacity="0.4">
                  <animate attributeName="r" from="10" to="35" dur="2.5s" repeatCount="indefinite" />
                  <animate attributeName="opacity" from="0.5" to="0" dur="2.5s" repeatCount="indefinite" />
                </circle>
                <circle cx={groundTruthPoint.x} cy={groundTruthPoint.y} r="9" fill="#ffd700" opacity="0.25" />
                <circle cx={groundTruthPoint.x} cy={groundTruthPoint.y} r="6" fill="#ffd700" opacity="0.6" />
                <circle cx={groundTruthPoint.x} cy={groundTruthPoint.y} r="3" fill="#ffffff" />
                <rect x={groundTruthPoint.x + 14} y={groundTruthPoint.y - 14} width="92" height="20" rx="4" fill="#12121a" stroke="#ffd700" strokeWidth="1" opacity="0.95" />
                <text x={groundTruthPoint.x + 20} y={groundTruthPoint.y} fill="#ffd700" fontSize="10" fontFamily="monospace" fontWeight="bold">
                  {groundTruthPoint.code} (confirmed)
                </text>
              </g>
            )}

            {/* User location labels */}
            {userPoints.map((p, i) => (
              <g key={`usr-label-${i}`}>
                <rect x={p.x + 12} y={p.y - 14} width={Math.max(80, (p.label?.length || 0) * 7 + 20)} height="20" rx="4" fill="#12121a" stroke="#00ff88" strokeWidth="1" opacity="0.9" />
                <text x={p.x + 18} y={p.y} fill="#00ff88" fontSize="10" fontFamily="monospace">{p.label}</text>
              </g>
            ))}

            {/* Server location labels */}
            {serverPoints.map((p, i) => (
              <g key={`srv-label-${i}`} opacity="0.5">
                <rect x={p.x + 10} y={p.y - 14} width={Math.max(80, (p.label?.length || 0) * 7 + 20)} height="20" rx="4" fill="#12121a" stroke="#1e1e2e" strokeWidth="1" />
                <text x={p.x + 16} y={p.y} fill="#666688" fontSize="10" fontFamily="monospace">{p.label} (server)</text>
              </g>
            ))}
          </g>
        </svg>
      </div>

      {/* Legend */}
      <div className="px-4 py-3 border-t border-[#1e1e2e]">
        <div className="flex flex-wrap gap-4 text-xs text-gray-400">
          {groundTruthPoint && (
            <span className="inline-flex items-center gap-1.5 text-[#ffd700]">
              <span className="w-2 h-2 rounded-full bg-[#ffd700]" />
              Operator-confirmed country
            </span>
          )}
          {userPoints.length > 0 && (
            <span className="inline-flex items-center gap-1.5 text-[#00ff88]">
              <span className="w-2 h-2 rounded-full bg-[#00ff88]" />
              Self-reported locations
            </span>
          )}
          {serverPoints.length > 0 && (
            <span className="inline-flex items-center gap-1.5 text-gray-600">
              <span className="w-2 h-2 rounded-full bg-[#3388ff] opacity-50" />
              Mail server locations (GeoIP)
            </span>
          )}
          <span className="ml-auto text-[10px] text-gray-600">scroll to zoom · drag to pan</span>
        </div>
        <div className="flex flex-wrap gap-4 text-xs text-gray-400 mt-2">
          {userPoints.map((p, i) => (
            <span key={`ul-${i}`} className="inline-flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[#00ff88]" />
              {p.label} — {p.source}
            </span>
          ))}
          {serverPoints.map((p, i) => (
            <span key={`sl-${i}`} className="inline-flex items-center gap-1.5 opacity-50">
              <span className="w-2 h-2 rounded-full bg-[#3388ff]" />
              {p.label} — {p.finding?.data?.ip || 'server'}
              {p.finding?.data?.isp && <span className="text-gray-600">({p.finding.data.isp})</span>}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}
