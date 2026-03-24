import { useMemo, useState } from 'react'
import { ChevronDown, ChevronRight, ExternalLink, Zap } from 'lucide-react'

const PLATFORM_COLORS = {
  github: '#238636', gitlab: '#fc6d26', reddit: '#ff4500',
  steam: '#1b2838', medium: '#00ab6c', telegram: '#0088cc',
  mastodon: '#6364ff', pinterest: '#e60023', linkedin: '#0a66c2',
  twitter: '#1da1f2', instagram: '#e4405f', flickr: '#ff0084',
  keybase: '#ff6f21', imgur: '#1bb76e', stackoverflow: '#f48024',
  hackerrank: '#2ec866', chess: '#769656', lichess: '#ffffff',
  codewars: '#b1361e', replit: '#f26207', soundcloud: '#ff5500',
  devto: '#0a0a0a', hashnode: '#2962ff', bluesky: '#0085ff',
  about_me: '#00405d', linktree: '#43e55e', speedrun: '#ffdd57',
}

function getPlatformColor(platform) {
  if (!platform) return '#666688'
  const key = platform.toLowerCase().replace(/[.\-\s]/g, '_')
  return PLATFORM_COLORS[key] || '#666688'
}

export default function UsernameTab({ findings, graphData }) {
  const [expandedUser, setExpandedUser] = useState(null)

  // Build username map from findings + graph identities
  const usernameGroups = useMemo(() => {
    const groups = {}

    // From findings with indicator_type="username"
    for (const f of findings) {
      if (f.indicator_type !== 'username' || !f.indicator_value) continue
      const key = f.indicator_value.toLowerCase()
      if (!groups[key]) {
        groups[key] = {
          username: f.indicator_value,
          platforms: [],
          findings: [],
          fromExpansion: false,
          maxConfidence: 0,
        }
      }
      groups[key].findings.push(f)
      groups[key].maxConfidence = Math.max(groups[key].maxConfidence, f.confidence || 0)
      if (f.data?.pass === '1.5') groups[key].fromExpansion = true

      // Extract platform from module name
      const platform = f.module?.replace('scraper_', '').split('_')[0] || f.data?.platform
      if (platform && !groups[key].platforms.some(p => p.name === platform)) {
        groups[key].platforms.push({
          name: platform,
          url: f.url,
          module: f.module,
          severity: f.severity,
          confidence: f.confidence,
          fromExpansion: f.data?.pass === '1.5',
        })
      }
    }

    // Enrich from graph nodes (type="username")
    if (graphData?.nodes) {
      for (const node of graphData.nodes) {
        if (node.type !== 'username' || !node.value) continue
        const key = node.value.toLowerCase()
        if (!groups[key]) {
          groups[key] = {
            username: node.value,
            platforms: [],
            findings: [],
            fromExpansion: false,
            maxConfidence: node.confidence || 0,
          }
        }
        if (node.platform && !groups[key].platforms.some(p => p.name === node.platform)) {
          groups[key].platforms.push({
            name: node.platform,
            url: null,
            module: node.source_module,
            severity: null,
            confidence: node.confidence,
            fromExpansion: node.source_module?.includes('pass1.5') || false,
          })
        }
        groups[key].maxConfidence = Math.max(groups[key].maxConfidence, node.confidence || 0)
      }
    }

    // Sort by platform count descending, then confidence
    return Object.values(groups).sort((a, b) =>
      b.platforms.length - a.platforms.length || b.maxConfidence - a.maxConfidence
    )
  }, [findings, graphData])

  // Reuse analysis
  const reuseCount = usernameGroups.filter(g => g.platforms.length >= 2).length
  const expansionCount = usernameGroups.filter(g => g.fromExpansion).length
  const totalPlatforms = usernameGroups.reduce((sum, g) => sum + g.platforms.length, 0)

  if (usernameGroups.length === 0) {
    return (
      <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-8 text-center text-gray-500 text-sm">
        No usernames discovered yet. Run a scan to discover usernames.
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Summary bar */}
      <div className="flex items-center gap-4 text-xs text-gray-400">
        <span className="font-mono">
          <span className="text-white font-semibold">{usernameGroups.length}</span> usernames
        </span>
        <span className="font-mono">
          <span className="text-white font-semibold">{totalPlatforms}</span> accounts
        </span>
        {reuseCount > 0 && (
          <span className="text-[#ffcc00] font-mono">
            {reuseCount} reused across platforms
          </span>
        )}
        {expansionCount > 0 && (
          <span className="flex items-center gap-1 text-[#00ff88] font-mono">
            <Zap className="w-3 h-3" />
            {expansionCount} from Pass 1.5
          </span>
        )}
      </div>

      {/* Username cards */}
      <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl overflow-hidden divide-y divide-[#1e1e2e]">
        {usernameGroups.map(group => {
          const isExpanded = expandedUser === group.username
          return (
            <div key={group.username}>
              {/* Username row */}
              <div
                className="flex items-center justify-between px-5 py-3 cursor-pointer hover:bg-white/[0.02] transition-colors"
                onClick={() => setExpandedUser(isExpanded ? null : group.username)}
              >
                <div className="flex items-center gap-3 min-w-0">
                  {isExpanded
                    ? <ChevronDown className="w-3.5 h-3.5 text-gray-500 shrink-0" />
                    : <ChevronRight className="w-3.5 h-3.5 text-gray-500 shrink-0" />}
                  <span className="text-sm font-mono font-semibold text-white truncate">
                    {group.username}
                  </span>
                  {group.fromExpansion && (
                    <span className="flex items-center gap-1 text-[9px] font-mono text-[#00ff88] bg-[#00ff8815] px-1.5 py-0.5 rounded">
                      <Zap className="w-2.5 h-2.5" /> PASS 1.5
                    </span>
                  )}
                  {group.platforms.length >= 2 && (
                    <span className="text-[9px] font-mono text-[#ffcc00] bg-[#ffcc0015] px-1.5 py-0.5 rounded">
                      REUSED
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {/* Platform badges */}
                  <div className="flex gap-1.5 flex-wrap justify-end">
                    {group.platforms.map(p => (
                      <span
                        key={p.name}
                        className="text-[10px] font-mono px-2 py-0.5 rounded"
                        style={{
                          backgroundColor: getPlatformColor(p.name) + '20',
                          color: getPlatformColor(p.name),
                          borderLeft: `2px solid ${getPlatformColor(p.name)}`,
                        }}
                      >
                        {p.name}
                      </span>
                    ))}
                  </div>
                  {/* Confidence */}
                  <span className="text-xs font-mono text-gray-500 w-12 text-right">
                    {Math.round(group.maxConfidence * 100)}%
                  </span>
                </div>
              </div>

              {/* Expanded detail */}
              {isExpanded && (
                <div className="px-5 pb-4 pt-0 ml-7 space-y-3">
                  {/* Platform details */}
                  <div className="grid gap-2">
                    {group.platforms.map(p => (
                      <div key={p.name} className="flex items-center justify-between px-3 py-2 rounded-lg bg-[#0a0a0f]">
                        <div className="flex items-center gap-3">
                          <span
                            className="w-2 h-2 rounded-full shrink-0"
                            style={{ backgroundColor: getPlatformColor(p.name) }}
                          />
                          <span className="text-sm font-mono text-gray-300">{p.name}</span>
                          {p.fromExpansion && (
                            <Zap className="w-3 h-3 text-[#00ff88]" />
                          )}
                          {p.severity && (
                            <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${
                              p.severity === 'critical' ? 'text-red-400 bg-red-400/10' :
                              p.severity === 'high' ? 'text-orange-400 bg-orange-400/10' :
                              p.severity === 'medium' ? 'text-yellow-400 bg-yellow-400/10' :
                              'text-gray-400 bg-gray-400/10'
                            }`}>
                              {p.severity}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="text-[10px] text-gray-600 font-mono">
                            {Math.round((p.confidence || 0) * 100)}% conf
                          </span>
                          {p.url && (
                            <a
                              href={p.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-gray-500 hover:text-[#00ff88] transition-colors"
                              onClick={e => e.stopPropagation()}
                            >
                              <ExternalLink className="w-3.5 h-3.5" />
                            </a>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Finding details if any */}
                  {group.findings.length > 0 && (
                    <div className="text-[10px] text-gray-600 font-mono pt-1">
                      {group.findings.length} finding{group.findings.length !== 1 ? 's' : ''} &middot;
                      {' '}modules: {[...new Set(group.findings.map(f => f.module))].join(', ')}
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
