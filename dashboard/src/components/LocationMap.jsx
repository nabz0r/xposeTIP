import { useMemo } from 'react'
import { Globe } from 'lucide-react'

// Simple Mercator projection: lat/lng → x/y on a 960×480 SVG
function project(lat, lng) {
  const x = (lng + 180) * (960 / 360)
  const latRad = (lat * Math.PI) / 180
  const mercN = Math.log(Math.tan(Math.PI / 4 + latRad / 2))
  const y = 240 - (960 * mercN) / (2 * Math.PI)
  return [Math.max(0, Math.min(960, x)), Math.max(0, Math.min(480, y))]
}

// Simplified world map outline (low-poly, covers major landmasses)
const WORLD_PATH =
  'M131,97L137,95L141,97L141,101L137,103L131,101Z ' + // North America west
  'M150,85L175,75L195,78L210,90L205,105L195,110L180,115L165,120L155,118L145,110L140,100Z ' + // North America
  'M170,125L178,130L185,145L190,160L185,170L175,175L165,165L160,150L162,135Z ' + // Central America / South America north
  'M180,175L195,180L200,200L195,220L185,235L175,230L170,215L172,195Z ' + // South America
  'M430,65L445,55L470,50L500,55L520,60L540,65L545,80L540,95L520,105L500,110L480,115L460,110L445,100L435,85Z ' + // Europe
  'M450,120L475,110L510,115L540,120L555,130L560,150L550,170L530,180L500,185L480,175L465,155L455,135Z ' + // Africa north
  'M475,185L500,190L520,200L525,220L515,240L500,245L485,235L475,215L472,195Z ' + // Africa south
  'M560,65L590,55L630,50L670,60L700,70L720,80L730,95L720,110L700,115L680,110L660,100L640,95L620,90L600,85L575,80Z ' + // Russia/Asia north
  'M620,100L650,105L680,115L700,120L710,130L700,145L680,155L660,160L640,155L625,140L615,120Z ' + // China/Central Asia
  'M600,130L615,135L620,150L615,165L600,175L585,170L580,155L585,140Z ' + // India
  'M700,155L720,150L740,160L750,180L745,200L730,210L715,205L705,190L700,170Z ' + // Southeast Asia
  'M740,220L770,215L800,225L810,250L800,270L780,280L760,275L745,260L740,240Z ' + // Australia
  'M630,170L645,175L655,185L650,200L635,195L625,185Z' // Indonesia

export default function LocationMap({ findings, userLocations }) {
  const geoFindings = useMemo(
    () => findings.filter(f => f.category === 'geolocation' && f.data?.latitude && f.data?.longitude),
    [findings]
  )

  // User-reported locations from profile_data.user_locations (self-reported, high value)
  const userPoints = useMemo(() => {
    if (!userLocations?.length) return []
    return userLocations
      .filter(u => u.lat && u.lon)
      .map((u, i) => {
        const [x, y] = project(u.lat, u.lon)
        return { x, y, label: u.city || u.location || u.country || '?', source: u.source, type: 'self_reported', index: i }
      })
  }, [userLocations])

  // Server locations from GeoIP findings (low value)
  const serverPoints = useMemo(() => {
    return geoFindings.map((f, i) => {
      const [x, y] = project(f.data.latitude, f.data.longitude)
      return { x, y, label: `${f.data.city || '?'}, ${f.data.country || '?'}`, source: f.data.isp || 'GeoIP', type: 'server', finding: f, index: i }
    })
  }, [geoFindings])

  const hasData = userPoints.length > 0 || serverPoints.length > 0

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
      <div className="p-4">
        <svg viewBox="0 0 960 480" className="w-full" style={{ maxHeight: '400px' }}>
          {/* Ocean background */}
          <rect width="960" height="480" fill="#0a0a0f" rx="8" />

          {/* Grid lines */}
          {[...Array(7)].map((_, i) => (
            <line key={`h${i}`} x1="0" y1={i * 80} x2="960" y2={i * 80} stroke="#1e1e2e" strokeWidth="0.5" />
          ))}
          {[...Array(13)].map((_, i) => (
            <line key={`v${i}`} x1={i * 80} y1="0" x2={i * 80} y2="480" stroke="#1e1e2e" strokeWidth="0.5" />
          ))}

          {/* World outline */}
          <path d={WORLD_PATH} fill="#1a1a2e" stroke="#2a2a3e" strokeWidth="1" opacity="0.8" />

          {/* Server location pulse rings (dim) */}
          {serverPoints.map((p, i) => (
            <g key={`srv-pulse-${i}`} opacity="0.3">
              <circle cx={p.x} cy={p.y} r="20" fill="none" stroke="#3388ff" strokeWidth="1" opacity="0.3">
                <animate attributeName="r" from="8" to="30" dur="2s" repeatCount="indefinite" />
                <animate attributeName="opacity" from="0.3" to="0" dur="2s" repeatCount="indefinite" />
              </circle>
            </g>
          ))}

          {/* User location pulse rings (bright) */}
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

          {/* Server location dots (dim blue) */}
          {serverPoints.map((p, i) => (
            <g key={`srv-dot-${i}`} opacity="0.4">
              <circle cx={p.x} cy={p.y} r="5" fill="#3388ff" opacity="0.3" />
              <circle cx={p.x} cy={p.y} r="3" fill="#3388ff" />
              <circle cx={p.x} cy={p.y} r="1" fill="#ffffff" />
            </g>
          ))}

          {/* User location dots (bright green) */}
          {userPoints.map((p, i) => (
            <g key={`usr-dot-${i}`}>
              <circle cx={p.x} cy={p.y} r="7" fill="#00ff88" opacity="0.3" />
              <circle cx={p.x} cy={p.y} r="5" fill="#00ff88" />
              <circle cx={p.x} cy={p.y} r="2" fill="#ffffff" />
            </g>
          ))}

          {/* User location labels */}
          {userPoints.map((p, i) => (
            <g key={`usr-label-${i}`}>
              <rect x={p.x + 12} y={p.y - 14} width={Math.max(80, (p.label?.length || 0) * 7 + 20)} height="20" rx="4" fill="#12121a" stroke="#00ff88" strokeWidth="1" opacity="0.9" />
              <text x={p.x + 18} y={p.y} fill="#00ff88" fontSize="10" fontFamily="monospace">
                {p.label}
              </text>
            </g>
          ))}

          {/* Server location labels */}
          {serverPoints.map((p, i) => (
            <g key={`srv-label-${i}`} opacity="0.5">
              <rect x={p.x + 10} y={p.y - 14} width={Math.max(80, (p.label?.length || 0) * 7 + 20)} height="20" rx="4" fill="#12121a" stroke="#1e1e2e" strokeWidth="1" />
              <text x={p.x + 16} y={p.y} fill="#666688" fontSize="10" fontFamily="monospace">
                {p.label} (server)
              </text>
            </g>
          ))}
        </svg>
      </div>
      {/* Legend */}
      <div className="px-4 py-3 border-t border-[#1e1e2e]">
        <div className="flex flex-wrap gap-4 text-xs text-gray-400">
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
