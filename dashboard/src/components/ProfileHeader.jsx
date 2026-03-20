import { Globe, MapPin, Building2, Calendar, Github, ExternalLink } from 'lucide-react'

const scoreColor = (score) => {
  if (score == null) return '#666688'
  if (score >= 61) return '#ff2244'
  if (score >= 31) return '#ff8800'
  return '#00ff88'
}

export default function ProfileHeader({ target, findings, animScore }) {
  // Extract enriched profile data from findings
  const gravatarFinding = findings.find(f => f.module === 'gravatar' && f.data?.display_name)
  const githubFinding = findings.find(f => f.module === 'social_enricher' && f.data?.username)
  const geoFindings = findings.filter(f => f.category === 'geolocation')
  const googleFinding = findings.find(f => f.module === 'google_profile' && f.data?.google_service)

  const displayName = gravatarFinding?.data?.display_name || githubFinding?.data?.name || target.display_name || ''
  const avatarUrl = gravatarFinding?.data?.avatar_url || githubFinding?.data?.avatar_url || null
  const bio = gravatarFinding?.data?.about || githubFinding?.data?.bio || ''
  const location = gravatarFinding?.data?.location || githubFinding?.data?.location || ''
  const company = githubFinding?.data?.company || ''
  const githubUsername = githubFinding?.data?.username || ''
  const repos = githubFinding?.data?.public_repos
  const followers = githubFinding?.data?.followers

  const breachCount = findings.filter(f => f.category === 'breach').length
  const socialCount = findings.filter(f => f.category === 'social_account').length
  const pasteCount = findings.filter(f => f.category === 'paste').length
  const countries = [...new Set(geoFindings.map(f => f.data?.country).filter(Boolean))]

  const breakdown = target.score_breakdown || {}

  return (
    <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-6">
      <div className="flex gap-6">
        {/* Avatar */}
        <div className="shrink-0">
          {avatarUrl ? (
            <img src={avatarUrl} alt="" className="w-20 h-20 rounded-full border-2 border-[#1e1e2e]" />
          ) : (
            <div className="w-20 h-20 rounded-full bg-[#1e1e2e] flex items-center justify-center text-2xl font-bold text-gray-500">
              {(target.email || '?')[0].toUpperCase()}
            </div>
          )}
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between">
            <div>
              {displayName && <h2 className="text-xl font-semibold">{displayName}</h2>}
              <p className="text-sm font-mono text-gray-400">{target.email}</p>
              {bio && <p className="text-sm text-gray-300 mt-1 line-clamp-2">{bio}</p>}
              <div className="flex flex-wrap gap-3 mt-2 text-xs text-gray-400">
                {location && <span className="inline-flex items-center gap-1"><MapPin className="w-3 h-3" />{location}</span>}
                {company && <span className="inline-flex items-center gap-1"><Building2 className="w-3 h-3" />{company}</span>}
                {googleFinding && <span className="inline-flex items-center gap-1"><Globe className="w-3 h-3" />{googleFinding.data.google_service}</span>}
                {githubUsername && (
                  <a href={`https://github.com/${githubUsername}`} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-[#3388ff] hover:underline">
                    <Github className="w-3 h-3" />{githubUsername}
                  </a>
                )}
                {countries.length > 0 && <span className="inline-flex items-center gap-1"><Globe className="w-3 h-3" />{countries.join(', ')}</span>}
              </div>
            </div>

            {/* Score donut */}
            <div className="flex flex-col items-center gap-1 shrink-0">
              <div className="relative w-20 h-20">
                <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
                  <circle cx="18" cy="18" r="15.5" fill="none" stroke="#1e1e2e" strokeWidth="3" />
                  <circle cx="18" cy="18" r="15.5" fill="none"
                    stroke={scoreColor(target.exposure_score)}
                    strokeWidth="3"
                    strokeDasharray={`${animScore} 100`}
                    strokeLinecap="round"
                    style={{ transition: 'stroke-dasharray 0.3s ease' }} />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-lg font-mono font-bold" style={{ color: scoreColor(target.exposure_score) }}>
                    {target.exposure_score ?? '-'}
                  </span>
                </div>
              </div>
              <span className="text-[10px] text-gray-500 uppercase tracking-wider">Exposure</span>
            </div>
          </div>
        </div>
      </div>

      {/* Stats bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 pt-4 border-t border-[#1e1e2e]">
        <div className="text-center">
          <div className="text-lg font-mono font-bold text-[#ff2244]">{breachCount}</div>
          <div className="text-[10px] text-gray-500 uppercase tracking-wider">Breaches</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-mono font-bold text-[#3388ff]">{socialCount}</div>
          <div className="text-[10px] text-gray-500 uppercase tracking-wider">Accounts</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-mono font-bold text-[#ff8800]">{pasteCount}</div>
          <div className="text-[10px] text-gray-500 uppercase tracking-wider">Pastes</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-mono font-bold text-[#ffcc00]">{findings.length}</div>
          <div className="text-[10px] text-gray-500 uppercase tracking-wider">Total Findings</div>
        </div>
      </div>

      {/* Score breakdown bars */}
      {Object.keys(breakdown).length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4 pt-4 border-t border-[#1e1e2e]">
          {Object.entries(breakdown).sort((a, b) => b[1] - a[1]).map(([cat, score]) => (
            <div key={cat} className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-gray-400">{cat.replace(/_/g, ' ')}</span>
                <span className="font-mono text-gray-300">{score}</span>
              </div>
              <div className="h-1.5 bg-[#1e1e2e] rounded-full overflow-hidden">
                <div className="h-full rounded-full transition-all duration-500"
                  style={{ width: `${score}%`, backgroundColor: score >= 60 ? '#ff2244' : score >= 30 ? '#ff8800' : '#00ff88' }} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
