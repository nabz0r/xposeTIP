import { useMemo, useState, useEffect } from 'react'
import { ChevronDown, ChevronRight, ExternalLink, Zap, Search, Loader2 } from 'lucide-react'
import { scanIndicator } from '../../lib/api'

// Aligned with seed_scrapers.py scraper names + data.platform values produced.
// This map IS the username-platform allow-list — only keys present here will
// appear in UsernameTab (defense-in-depth on top of S159 backend taxonomy fix).
const PLATFORM_COLORS = {
  // Social / forums
  reddit: '#ff4500', github: '#238636', gitlab: '#fc6d26',
  medium: '#00ab6c', devto: '#0a0a0a', hackernews: '#ff6600',
  mastodon: '#6364ff', stackoverflow: '#f48024', linktree: '#43e55e',
  hashnode: '#2962ff', bluesky: '#0085ff', disqus: '#2e9fff',
  // Networks / platforms
  telegram: '#0088cc', threads: '#000000', linkedin: '#0a66c2',
  keybase: '#ff6f21', aboutme: '#00405d', pinterest: '#e60023',
  imgur: '#1bb76e', flickr: '#ff0084', soundcloud: '#ff5500',
  // Gaming / activities
  steam: '#1b2838', twitch: '#9146ff', chesscom: '#769656',
  lichess: '#759900', roblox: '#ff2e2e', strava: '#fc4c02',
  anilist: '#02a9ff', myanimelist: '#2e51a2', speedrun: '#ffdd57',
  // Tech / dev platforms
  npm: '#cb3837', pypi: '#3775a9', kaggle: '#20beff',
  codewars: '#b1361e', replit: '#f26207',
}

// Special-case module → canonical platform mapping.
// Use when data.platform stores the verbose verbatim form but the finding
// IS a real username on a known platform (vetted via Q2 sample).
const MODULE_PLATFORM_MAP = {
  'wayback_linkedin_user': 'linkedin',
  'npm_maintainer': 'npm',
  'github_email_search': 'github',
}

function getPlatformColor(platform) {
  if (!platform) return '#666688'
  const key = platform.toLowerCase().replace(/[.\-\s]/g, '_')
  return PLATFORM_COLORS[key] || '#666688'
}

// S159: canonical platform extraction — prefer explicit override, then
// data.platform from backend, then derived from module name (strip suffixes).
function extractPlatform(finding) {
  const m = finding.module
  if (m && MODULE_PLATFORM_MAP[m]) return MODULE_PLATFORM_MAP[m]
  let p = finding.data?.platform
  if (!p && m) {
    p = m
      .replace(/_profile$/, '')
      .replace(/_scraper$/, '')
      .replace(/_search$/, '')
      .replace(/_maintainer$/, '')
  }
  return p ? p.toLowerCase().trim() : null
}

// S159: indicator_value looks like an email or a bare domain → not a username.
function isJunkUsernameValue(v) {
  if (!v) return true
  if (v.includes('@')) return true  // email
  // bare domain (e.g., "gmail.com", "kpmg.lu") — letters/digits/hyphens + TLD
  if (/^[a-z0-9-]+\.[a-z]{2,}$/i.test(v)) return true
  return false
}

export default function UsernameTab({ findings, graphData, targetId, onRefresh }) {
  const [expandedUser, setExpandedUser] = useState(null)
  const [scanningUser, setScanningUser] = useState(null)

  // Build username map from findings + graph identities
  const usernameGroups = useMemo(() => {
    const groups = {}

    // From findings with indicator_type="username"
    for (const f of findings) {
      if (f.indicator_type !== 'username' || !f.indicator_value) continue
      // S159: defense — skip junk values that leaked from misconfigured scrapers
      if (isJunkUsernameValue(f.indicator_value)) continue
      // S159: defense — skip findings whose platform is not in the allow-list
      const fPlatform = extractPlatform(f)
      if (!fPlatform || !PLATFORM_COLORS[fPlatform]) continue
      const key = f.indicator_value.toLowerCase()
      if (!groups[key]) {
        groups[key] = {
          username: f.indicator_value,
          platforms: [],
          findings: [],
          fromExpansion: false,
          fromDeepScan: false,
          maxConfidence: 0,
        }
      }
      groups[key].findings.push(f)
      groups[key].maxConfidence = Math.max(groups[key].maxConfidence, f.confidence || 0)
      if (f.data?.pass === '1.5') groups[key].fromExpansion = true
      if (f.data?.pass === 'deep') groups[key].fromDeepScan = true

      // S159: canonical platform via helper (override > data.platform > module-derived)
      const platform = fPlatform  // already resolved above for filtering
      if (platform && !groups[key].platforms.some(p => p.name === platform)) {
        groups[key].platforms.push({
          name: platform,
          url: f.url,
          module: f.module,
          severity: f.severity,
          confidence: f.confidence,
          fromExpansion: f.data?.pass === '1.5',
          fromDeepScan: f.data?.pass === 'deep',
        })
      }
    }

    // Enrich from graph nodes (type="username")
    if (graphData?.nodes) {
      for (const node of graphData.nodes) {
        if (node.type !== 'username' || !node.value) continue
        // S159: same defense as findings loop
        if (isJunkUsernameValue(node.value)) continue
        const nodePlatform = node.platform ? node.platform.toLowerCase().trim() : null
        if (nodePlatform && !PLATFORM_COLORS[nodePlatform]) continue
        const key = node.value.toLowerCase()
        if (!groups[key]) {
          groups[key] = {
            username: node.value,
            platforms: [],
            findings: [],
            fromExpansion: false,
            fromDeepScan: false,
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

    // Filter out junk usernames (page titles persisted in DB before Sprint 73b)
    const validGroups = Object.values(groups).filter(g => {
      const u = g.username
      if (u.length > 40) return false
      if ((u.match(/ /g) || []).length >= 3) return false
      if (u.includes(' - ') || u.includes(' \u2013 ') || u.includes(' \u2014 ')) return false
      return true
    })

    // Sort: real platform count first, then total platforms, then confidence
    return validGroups.sort((a, b) => {
      const realA = a.platforms.filter(p => p.module && !p.module.startsWith('intelligence')).length
      const realB = b.platforms.filter(p => p.module && !p.module.startsWith('intelligence')).length
      if (realB !== realA) return realB - realA
      if (b.platforms.length !== a.platforms.length) return b.platforms.length - a.platforms.length
      return b.maxConfidence - a.maxConfidence
    })
  }, [findings, graphData])

  // Clear scanning state when findings data changes (scan completed)
  useEffect(() => {
    if (scanningUser) {
      const timer = setTimeout(() => setScanningUser(null), 120000) // 2 min max
      return () => clearTimeout(timer)
    }
  }, [scanningUser])

  async function handleDeepScan(e, username) {
    e.stopPropagation()
    if (scanningUser) return
    setScanningUser(username)
    try {
      await scanIndicator(targetId, 'username', username)
      // Poll for completion — refresh every 5s, clear after 2 min max
      let attempts = 0
      const maxAttempts = 24
      const poll = setInterval(() => {
        attempts++
        if (attempts >= maxAttempts) {
          clearInterval(poll)
          setScanningUser(null)
          if (onRefresh) onRefresh()
          return
        }
        if (onRefresh) onRefresh()
      }, 5000)

      // First refresh after 10s
      setTimeout(() => {
        if (onRefresh) onRefresh()
      }, 10000)
    } catch (err) {
      console.error('Deep scan failed:', err)
      setScanningUser(null)
    }
  }

  // Reuse analysis
  const reuseCount = usernameGroups.filter(g => g.platforms.length >= 2).length
  const expansionCount = usernameGroups.filter(g => g.fromExpansion).length
  const deepCount = usernameGroups.filter(g => g.fromDeepScan).length
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
        {deepCount > 0 && (
          <span className="flex items-center gap-1 text-[#3388ff] font-mono">
            <Search className="w-3 h-3" />
            {deepCount} deep scanned
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
                  {group.fromDeepScan && (
                    <span className="flex items-center gap-1 text-[9px] font-mono text-[#3388ff] bg-[#3388ff15] px-1.5 py-0.5 rounded">
                      <Search className="w-2.5 h-2.5" /> DEEP
                    </span>
                  )}
                  {group.platforms.length >= 2 && (
                    <span className="text-[9px] font-mono text-[#ffcc00] bg-[#ffcc0015] px-1.5 py-0.5 rounded">
                      REUSED
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {/* Deep Scan button */}
                  <button
                    onClick={(e) => handleDeepScan(e, group.username)}
                    disabled={!!scanningUser}
                    className={`flex items-center gap-1 text-[10px] font-mono px-2 py-1 rounded transition-colors ${
                      scanningUser === group.username
                        ? 'bg-[#00ff88]/20 text-[#00ff88] animate-pulse'
                        : scanningUser
                          ? 'text-gray-600 cursor-not-allowed'
                          : 'text-gray-400 hover:text-[#00ff88] hover:bg-[#00ff88]/10'
                    }`}
                    title="Deep scan this username across all platforms"
                  >
                    {scanningUser === group.username ? (
                      <><Loader2 className="w-3 h-3 animate-spin" /> Scanning...</>
                    ) : (
                      <><Search className="w-3 h-3" /> Deep Scan</>
                    )}
                  </button>
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
                          {p.fromDeepScan && (
                            <Search className="w-3 h-3 text-[#3388ff]" />
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
